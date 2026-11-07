"""Geração do relatório demonstrativo de vendas em PDF."""

import logging
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from dinheiro import converter_decimal, formatar_brl

logger = logging.getLogger(__name__)


def gerar_nota(caminho: Path, total: Decimal) -> Path:
    """Grava o total em um PDF demonstrativo, sem validade fiscal."""
    total = converter_decimal(total)
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(caminho), pagesize=A4)
    pdf.setTitle("Relatório de vendas")
    pdf.drawString(72, 780, "Relatório de vendas")
    pdf.drawString(72, 752, f"Valor: {formatar_brl(total)}")
    pdf.drawString(72, 724, "Documento demonstrativo - sem validade fiscal.")
    pdf.save()
    logger.info("Relatório PDF gerado: %s", caminho)
    return caminho
