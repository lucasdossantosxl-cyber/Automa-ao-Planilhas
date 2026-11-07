"""Envio do relatório usando credenciais fornecidas pelo ambiente."""

import logging
import math
import os
import smtplib
import ssl
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

from dinheiro import converter_decimal, formatar_brl

logger = logging.getLogger(__name__)


def enviar_email(valor: Decimal, anexo: Path | None = None) -> None:
    """Envia o total por SMTP com STARTTLS e anexo PDF opcional."""
    valor = converter_decimal(valor)
    obrigatorias = ("SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")
    faltantes = [nome for nome in obrigatorias if not os.getenv(nome, "").strip()]
    if faltantes:
        raise ValueError("Variáveis de ambiente ausentes: " + ", ".join(faltantes))

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    if not smtp_host:
        raise ValueError("SMTP_HOST não pode estar vazio.")
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        raise ValueError(
            "SMTP_PORT deve ser um número inteiro entre 1 e 65535."
        ) from None
    if not 1 <= smtp_port <= 65535:
        raise ValueError("SMTP_PORT deve ser um número inteiro entre 1 e 65535.")
    try:
        smtp_timeout = float(os.getenv("SMTP_TIMEOUT", "30"))
    except ValueError:
        raise ValueError(
            "SMTP_TIMEOUT deve ser um número positivo em segundos."
        ) from None
    if not math.isfinite(smtp_timeout) or smtp_timeout <= 0:
        raise ValueError("SMTP_TIMEOUT deve ser um número positivo em segundos.")

    smtp_user = os.environ["SMTP_USER"].strip()
    mensagem = EmailMessage()
    mensagem["Subject"] = "Relatório Diário de Vendas"
    mensagem["From"] = os.getenv("EMAIL_FROM", "").strip() or smtp_user
    mensagem["To"] = os.environ["EMAIL_TO"].strip()
    mensagem.set_content(
        f"Olá, o total de vendas extraído do relatório foi {formatar_brl(valor)}."
    )
    if anexo is not None:
        anexo = Path(anexo)
        try:
            conteudo = anexo.read_bytes()
        except OSError:
            raise RuntimeError(
                "Não foi possível ler o PDF para anexar ao e-mail."
            ) from None
        mensagem.add_attachment(
            conteudo, maintype="application", subtype="pdf", filename=anexo.name
        )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as servidor:
            servidor.starttls(context=ssl.create_default_context())
            servidor.login(smtp_user, os.environ["SMTP_PASSWORD"])
            recusados = servidor.send_message(mensagem)
            if recusados:
                raise RuntimeError("O servidor SMTP recusou um ou mais destinatários.")
    except (smtplib.SMTPException, OSError):
        raise RuntimeError(
            "Não foi possível enviar o e-mail. Verifique a conexão e a configuração SMTP."
        ) from None

    logger.info("E-mail enviado com sucesso.")
