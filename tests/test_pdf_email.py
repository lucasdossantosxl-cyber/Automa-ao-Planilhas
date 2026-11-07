import smtplib
import ssl
from decimal import Decimal

import pytest
from reportlab.pdfgen import canvas

from enviar_email import enviar_email
from gerar_pdf import gerar_nota
from leitor_pdf import extrair_valor


@pytest.mark.parametrize("total", ["0.00", "0.01", "1500.00", "1234567.89"])
def test_pdf_preserva_total_e_cria_pasta(tmp_path, total):
    destino = tmp_path / "saida" / "nota.pdf"
    assert gerar_nota(destino, Decimal(total)) == destino
    assert extrair_valor(destino) == Decimal(total)


def test_extrai_valor_da_segunda_pagina(tmp_path):
    caminho = tmp_path / "multipagina.pdf"
    pdf = canvas.Canvas(str(caminho))
    pdf.drawString(72, 750, "Capa do relatório")
    pdf.showPage()
    pdf.drawString(72, 750, "Valor: R$ 1.234,56")
    pdf.save()
    assert extrair_valor(caminho) == Decimal("1234.56")


@pytest.mark.parametrize(
    ("texto", "erro"),
    [
        (None, "texto extraível"),
        ("Sem valor", "não foi encontrado"),
        ("Valor: R$ -1,00", "monetário inválido"),
        ("Valor: R$ 1,001", "monetário inválido"),
        ("Valor: R$ inválido\nValor: R$ 20,00", "monetário inválido"),
        ("Valor: R$ 10,00\nValor: R$ 20,00", "valores diferentes"),
    ],
)
def test_rejeita_pdf_sem_valor_valido(tmp_path, texto, erro):
    caminho = tmp_path / "invalido.pdf"
    pdf = canvas.Canvas(str(caminho))
    if texto is not None:
        for indice, linha in enumerate(texto.splitlines()):
            pdf.drawString(72, 750 - indice * 20, linha)
    pdf.showPage()
    pdf.save()
    with pytest.raises(ValueError, match=erro):
        extrair_valor(caminho)


def test_rejeita_arquivo_que_nao_e_pdf(tmp_path):
    caminho = tmp_path / "invalido.pdf"
    caminho.write_text("Isto não é um PDF.", encoding="utf-8")
    with pytest.raises(ValueError, match="ler o arquivo PDF"):
        extrair_valor(caminho)


@pytest.fixture
def ambiente_smtp(monkeypatch):
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "EMAIL_TO",
        "EMAIL_FROM",
        "SMTP_TIMEOUT",
    ):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("SMTP_USER", "teste@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "senha-de-teste")
    monkeypatch.setenv("EMAIL_TO", "destino@example.com")


def test_email_usa_tls_timeout_total_e_anexo(tmp_path, monkeypatch, ambiente_smtp):
    chamadas = {}

    class SMTPFalso:
        def __init__(self, host, port, timeout):
            chamadas["conexao"] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, *, context):
            chamadas["tls"] = context

        def login(self, usuario, senha):
            chamadas["login"] = (usuario, senha)

        def send_message(self, mensagem):
            chamadas["mensagem"] = mensagem
            return {}

    monkeypatch.setattr(smtplib, "SMTP", SMTPFalso)
    pdf = gerar_nota(tmp_path / "nota.pdf", Decimal("1234.56"))
    enviar_email(Decimal("1234.56"), pdf)

    assert chamadas["conexao"] == ("smtp.gmail.com", 587, 30)
    assert isinstance(chamadas["tls"], ssl.SSLContext)
    assert chamadas["tls"].check_hostname
    assert chamadas["login"] == ("teste@example.com", "senha-de-teste")
    mensagem = chamadas["mensagem"]
    assert mensagem["To"] == "destino@example.com"
    assert mensagem["From"] == "teste@example.com"
    assert "R$ 1.234,56" in mensagem.get_body().get_content()
    anexo = next(mensagem.iter_attachments())
    assert anexo.get_content_type() == "application/pdf"
    assert anexo.get_filename() == "nota.pdf"
    assert anexo.get_payload(decode=True) == pdf.read_bytes()


def test_email_informa_variaveis_ausentes(monkeypatch, ambiente_smtp):
    monkeypatch.delenv("SMTP_USER")
    monkeypatch.delenv("SMTP_PASSWORD")
    with pytest.raises(ValueError, match="SMTP_USER, SMTP_PASSWORD"):
        enviar_email(Decimal("1.00"))


@pytest.mark.parametrize(
    ("variavel", "valor"),
    [
        ("SMTP_PORT", "invalida"),
        ("SMTP_PORT", "0"),
        ("SMTP_PORT", "65536"),
        ("SMTP_TIMEOUT", "0"),
        ("SMTP_TIMEOUT", "nan"),
        ("SMTP_TIMEOUT", "inf"),
        ("SMTP_TIMEOUT", "invalido"),
        ("SMTP_HOST", " "),
    ],
)
def test_email_valida_configuracao(monkeypatch, ambiente_smtp, variavel, valor):
    monkeypatch.setenv(variavel, valor)
    with pytest.raises(ValueError, match=variavel):
        enviar_email(Decimal("1.00"))


@pytest.mark.parametrize("erro", [smtplib.SMTPException("erro"), OSError("erro")])
def test_email_trata_falha_de_conexao(monkeypatch, ambiente_smtp, erro):
    def falhar(*args, **kwargs):
        raise erro

    monkeypatch.setattr(smtplib, "SMTP", falhar)
    with pytest.raises(RuntimeError, match="configuração SMTP"):
        enviar_email(Decimal("1.00"))


def test_email_informa_anexo_inacessivel(tmp_path, ambiente_smtp):
    with pytest.raises(RuntimeError, match="ler o PDF"):
        enviar_email(Decimal("1.00"), tmp_path / "ausente.pdf")
