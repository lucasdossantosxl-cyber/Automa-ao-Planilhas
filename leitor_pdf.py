"""Extração do valor monetário informado no relatório PDF."""

import logging
import re
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from dinheiro import converter_decimal

logger = logging.getLogger(__name__)
PADRAO_VALOR = re.compile(r"\bValor:\s*R\$[^\S\r\n]*([^\r\n]*)", re.IGNORECASE)


def extrair_valor(caminho: Path) -> Decimal:
    """Lê todas as páginas e exige um valor monetário não ambíguo."""
    try:
        leitor = PdfReader(str(caminho))
        texto = "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except PdfReadError:
        raise ValueError("Não foi possível ler o arquivo PDF.") from None

    if not texto.strip():
        raise ValueError("O PDF não contém texto extraível.")

    encontrados = PADRAO_VALOR.findall(texto)
    if not encontrados:
        raise ValueError('O campo "Valor: R$" não foi encontrado no PDF.')

    try:
        valores = {converter_decimal(valor) for valor in encontrados}
    except (ValueError, TypeError):
        raise ValueError(
            "O campo Valor do PDF contém um valor monetário inválido."
        ) from None

    if len(valores) != 1:
        raise ValueError("O PDF contém valores diferentes no campo Valor.")

    valor = valores.pop()
    logger.info("Valor extraído do PDF: %s", valor)
    return valor
