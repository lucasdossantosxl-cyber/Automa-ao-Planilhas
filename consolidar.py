"""Leitura e validação das vendas recebidas em arquivos CSV ou XLSX."""

import csv
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd

from dinheiro import converter_decimal

BASE = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)
COLUNAS = {"Produto", "Vendas", "Preco"}


def validar_vendas(tabela: pd.DataFrame) -> pd.DataFrame:
    """Valida linhas e calcula cada subtotal usando Decimal."""
    faltantes = COLUNAS - set(tabela.columns)
    if faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes))
        )
    if tabela.empty:
        raise ValueError("A tabela de vendas está vazia.")
    tabela = tabela.copy()
    produtos, quantidades, precos, subtotais = [], [], [], []
    for linha, (_, venda) in enumerate(tabela.iterrows(), start=2):
        try:
            produto = str(venda["Produto"]).strip()
            if pd.isna(venda["Produto"]) or not produto:
                raise ValueError("Produto não pode ficar vazio.")
            quantidade = Decimal(str(venda["Vendas"]).strip())
            if (
                not quantidade.is_finite()
                or quantidade < 0
                or quantidade != quantidade.to_integral_value()
            ):
                raise ValueError("Vendas deve ser uma quantidade inteira não negativa.")
            preco = converter_decimal(venda["Preco"])
            subtotal = converter_decimal(quantidade * preco)
            if "Faturamento" in tabela.columns:
                informado = converter_decimal(venda["Faturamento"])
                if informado != subtotal:
                    raise ValueError("Faturamento difere de Vendas × Preco.")
        except (ValueError, InvalidOperation) as erro:
            raise ValueError(f"Linha {linha}: {erro}") from erro
        produtos.append(produto.title())
        quantidades.append(int(quantidade))
        precos.append(preco)
        subtotais.append(subtotal)
    tabela["Produto"] = produtos
    tabela["Vendas"] = quantidades
    tabela["Preco"] = precos
    tabela["Faturamento"] = subtotais
    return tabela


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Reconhece CSV com vírgula ou ponto e vírgula, preservando os decimais."""
    try:
        with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            primeira_linha = next(
                (linha for linha in arquivo if linha.rstrip("\r\n")), ""
            )
            dialecto = csv.Sniffer().sniff(primeira_linha, delimiters=",;")
            arquivo.seek(0)
            leitor = csv.reader(arquivo, dialecto, strict=True)
            cabecalho = next((linha for linha in leitor if linha), [])
            nomes = [nome.strip() for nome in cabecalho]
            if len(set(nomes)) != len(nomes):
                raise ValueError("O cabeçalho CSV contém colunas duplicadas.")
            for linha in leitor:
                if linha and len(linha) != len(cabecalho):
                    raise ValueError(
                        f"Linha {leitor.line_num}: esperados {len(cabecalho)} "
                        f"campos CSV, recebidos {len(linha)}. "
                        "Use aspas em valores que contenham o separador."
                    )
        return pd.read_csv(
            caminho,
            sep=dialecto.delimiter,
            dtype=str,
            encoding="utf-8-sig",
            index_col=False,
        )
    except (
        csv.Error,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        UnicodeError,
    ) as erro:
        raise ValueError(f"CSV inválido ou vazio: {caminho.name}.") from erro


def consolidar_vendas(destino: Path, entrada: Path | None = None) -> Path:
    """Consolida os arquivos da pasta; o nome de cada arquivo identifica a filial."""
    entrada = Path(entrada) if entrada is not None else BASE / "entrada"
    destino = Path(destino)
    if not entrada.is_dir():
        raise FileNotFoundError(f"Pasta de entrada não encontrada: {entrada}.")
    arquivos = sorted(
        caminho
        for caminho in entrada.iterdir()
        if caminho.is_file()
        and caminho.suffix.lower() in {".csv", ".xlsx"}
        and not caminho.name.startswith("~$")
        and caminho.resolve() != destino.resolve()
    )
    if not arquivos:
        raise ValueError(f"Nenhum arquivo CSV ou XLSX encontrado em {entrada}.")
    tabelas = []
    for arquivo in arquivos:
        try:
            tabela = (
                ler_csv(arquivo)
                if arquivo.suffix.lower() == ".csv"
                else pd.read_excel(arquivo, dtype=str, engine="openpyxl")
            )
            tabela = validar_vendas(tabela)
        except (ValueError, OSError, BadZipFile, KeyError) as erro:
            raise ValueError(f"{arquivo.name}: {erro}") from erro
        tabela["Filial"] = arquivo.stem
        tabelas.append(tabela[["Filial", "Produto", "Vendas", "Preco", "Faturamento"]])
    consolidado = pd.concat(tabelas, ignore_index=True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    consolidado.to_csv(destino, index=False, encoding="utf-8")
    LOGGER.info(
        "Consolidadas %d vendas de %d arquivo(s).", len(consolidado), len(arquivos)
    )
    return destino
