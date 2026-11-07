import csv
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

import main
from consolidar import consolidar_vendas
from dinheiro import converter_decimal, formatar_brl
from faturamento import calcular_total
from leitor_pdf import extrair_valor


def gravar_csv(caminho: Path, linhas: list[dict], delimitador: str = ",") -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=list(linhas[0]), delimiter=delimitador
        )
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("1.500,00", Decimal("1500.00")),
        ("1500.25", Decimal("1500.25")),
        ("0,01", Decimal("0.01")),
        (Decimal("123.45"), Decimal("123.45")),
        (0, Decimal("0.00")),
    ],
)
def test_converter_decimal_preserva_centavos(valor, esperado):
    assert converter_decimal(valor) == esperado


@pytest.mark.parametrize(
    "valor", ["-1.00", "NaN", "Infinity", "0.001", "", None, True, "abc"]
)
def test_converter_decimal_rejeita_dinheiro_invalido(valor):
    with pytest.raises(ValueError):
        converter_decimal(valor)


def test_formatar_brl():
    assert formatar_brl(Decimal("1234567.89")) == "R$ 1.234.567,89"


def test_consolidar_csv_e_excel_preserva_filial_e_dinheiro(tmp_path):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "filial_a.csv",
        [{"Produto": " headset ", "Vendas": 3, "Preco": "0,10"}],
    )
    pd.DataFrame([{"Produto": "MONITOR", "Vendas": 2, "Preco": "100.25"}]).to_excel(
        entrada / "filial_b.xlsx", index=False
    )
    destino = tmp_path / "saida" / "consolidado.csv"

    resultado = consolidar_vendas(destino, entrada)

    assert Path(resultado) == destino
    with destino.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert {linha["Filial"] for linha in linhas} == {"filial_a", "filial_b"}
    por_filial = {linha["Filial"]: linha for linha in linhas}
    assert por_filial["filial_a"]["Produto"] == "Headset"
    assert por_filial["filial_b"]["Produto"] == "Monitor"
    assert Decimal(por_filial["filial_a"]["Faturamento"]) == Decimal("0.30")
    assert Decimal(por_filial["filial_b"]["Faturamento"]) == Decimal("200.50")
    assert calcular_total(destino) == Decimal("200.80")


@pytest.mark.parametrize("delimitador", [",", ";"])
def test_consolidar_csv_com_preco_brasileiro(tmp_path, delimitador):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "loja.csv",
        [{"Produto": "Mouse", "Vendas": 2, "Preco": "1.500,25"}],
        delimitador,
    )
    destino = consolidar_vendas(tmp_path / "relatorio.csv", entrada)
    assert calcular_total(destino) == Decimal("3000.50")


@pytest.mark.parametrize(
    ("coluna", "valor"),
    [
        ("Vendas", -1),
        ("Vendas", "1.5"),
        ("Vendas", "NaN"),
        ("Preco", "-0.01"),
        ("Preco", "NaN"),
        ("Preco", "Infinity"),
        ("Preco", "1.001"),
        ("Produto", " "),
    ],
)
def test_consolidar_rejeita_linhas_invalidas(tmp_path, coluna, valor):
    linha = {"Produto": "Teclado", "Vendas": 1, "Preco": "10.00"}
    linha[coluna] = valor
    entrada = tmp_path / "entrada"
    gravar_csv(entrada / "loja.csv", [linha])
    with pytest.raises(ValueError):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)
    assert not (tmp_path / "relatorio.csv").exists()


def test_consolidar_rejeita_coluna_obrigatoria_ausente(tmp_path):
    entrada = tmp_path / "entrada"
    gravar_csv(entrada / "loja.csv", [{"Produto": "Mouse", "Vendas": 1}])
    with pytest.raises(ValueError, match="Preco"):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)


def test_consolidar_rejeita_pasta_sem_planilhas(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    with pytest.raises((ValueError, FileNotFoundError)):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)


def test_consolidar_rejeita_pasta_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        consolidar_vendas(tmp_path / "relatorio.csv", tmp_path / "inexistente")


def test_consolidar_rejeita_planilha_sem_vendas(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "loja.csv").write_text("Produto,Vendas,Preco\n", encoding="utf-8")
    with pytest.raises(ValueError):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)


def test_calcular_total_multiplica_quantidade_por_preco_sem_float(tmp_path):
    caminho = gravar_csv(
        tmp_path / "vendas.csv",
        [
            {"Produto": "Mouse", "Vendas": 3, "Preco": "0.10"},
            {"Produto": "Teclado", "Vendas": 2, "Preco": "15.25"},
        ],
    )
    total = calcular_total(caminho)
    assert isinstance(total, Decimal)
    assert total == Decimal("30.80")


def test_calcular_total_rejeita_faturamento_inconsistente(tmp_path):
    caminho = gravar_csv(
        tmp_path / "vendas.csv",
        [{"Produto": "Mouse", "Vendas": 2, "Preco": "10.00", "Faturamento": "1.00"}],
    )
    with pytest.raises(ValueError):
        calcular_total(caminho)


def test_fluxo_completo_funciona_fora_da_pasta_do_projeto(tmp_path, monkeypatch):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "loja.csv",
        [{"Produto": "mouse", "Vendas": 3, "Preco": "12.34"}],
    )
    outro_diretorio = tmp_path / "outro"
    outro_diretorio.mkdir()
    monkeypatch.chdir(outro_diretorio)
    envios = []
    monkeypatch.setattr(main, "enviar_email", lambda *a, **kw: envios.append((a, kw)))
    saida = tmp_path / "saida"

    total = main.executar_fluxo(entrada, saida)

    assert total == Decimal("37.02")
    assert calcular_total(saida / "relatorio_final.csv") == total
    assert extrair_valor(saida / "nota.pdf") == total
    assert envios == []


def test_fluxo_envia_email_apenas_quando_solicitado(tmp_path, monkeypatch):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "loja.csv",
        [{"Produto": "Mouse", "Vendas": 2, "Preco": "10.00"}],
    )
    envios = []
    monkeypatch.setattr(main, "enviar_email", lambda *a, **kw: envios.append((a, kw)))

    total = main.executar_fluxo(entrada, tmp_path / "saida", enviar=True)

    assert total == Decimal("20.00")
    assert len(envios) == 1
    args, kwargs = envios[0]
    assert args[0] == total
    assert Path(kwargs.get("anexo", args[1] if len(args) > 1 else "")) == (
        tmp_path / "saida" / "nota.pdf"
    )


def test_cli_aceita_pastas_personalizadas(tmp_path):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "loja.csv",
        [{"Produto": "Mouse", "Vendas": 1, "Preco": "10.00"}],
    )
    saida = tmp_path / "saida"
    assert main.main(["--entrada", str(entrada), "--saida", str(saida)]) == 0
    assert extrair_valor(saida / "nota.pdf") == Decimal("10.00")


def test_fluxo_nao_envia_quando_pdf_diverge_do_total(tmp_path, monkeypatch):
    entrada = tmp_path / "entrada"
    gravar_csv(
        entrada / "loja.csv",
        [{"Produto": "Mouse", "Vendas": 1, "Preco": "10.00"}],
    )
    monkeypatch.setattr(main, "extrair_valor", lambda caminho: Decimal("1.00"))
    envios = []
    monkeypatch.setattr(main, "enviar_email", lambda *a, **kw: envios.append((a, kw)))

    with pytest.raises(ValueError, match="difere"):
        main.executar_fluxo(entrada, tmp_path / "saida", enviar=True)

    assert envios == []


def test_cli_retorna_erro_quando_entrada_invalida(tmp_path):
    assert (
        main.main(
            [
                "--entrada",
                str(tmp_path / "inexistente"),
                "--saida",
                str(tmp_path / "saida"),
            ]
        )
        == 1
    )
    assert not (tmp_path / "saida" / "nota.pdf").exists()
