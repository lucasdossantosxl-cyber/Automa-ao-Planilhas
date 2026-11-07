"""Fluxo completo: planilhas → CSV → faturamento → PDF → e-mail opcional."""

import argparse
import logging
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from pypdf.errors import PdfReadError

from consolidar import consolidar_vendas
from dinheiro import formatar_brl
from enviar_email import enviar_email
from faturamento import calcular_total
from gerar_pdf import gerar_nota
from leitor_pdf import extrair_valor

BASE = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)


def executar_fluxo(entrada: Path, saida: Path, enviar: bool = False) -> Decimal:
    """Gera os relatórios e verifica o valor lido antes de permitir o envio."""
    saida = Path(saida)
    csv = consolidar_vendas(saida / "relatorio_final.csv", entrada)
    total = calcular_total(csv)
    pdf = gerar_nota(saida / "nota.pdf", total)
    valor = extrair_valor(pdf)
    if valor != total:
        raise ValueError("O valor extraído do PDF difere do faturamento calculado.")
    LOGGER.info("Faturamento total: %s", formatar_brl(total))
    LOGGER.info("Arquivos gerados em %s", saida.resolve())
    if enviar:
        enviar_email(valor, anexo=pdf)
    else:
        LOGGER.info("Para enviar o relatório, execute com --enviar-email.")
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=BASE / "entrada")
    parser.add_argument("--saida", type=Path, default=BASE / "saida")
    parser.add_argument(
        "--enviar-email", action="store_true", help="Envia o PDF via SMTP."
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv(BASE / ".env", override=False)
    try:
        executar_fluxo(args.entrada, args.saida, enviar=args.enviar_email)
    except (ValueError, OSError, RuntimeError, PdfReadError) as erro:
        LOGGER.error("Falha na automação: %s", erro)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
