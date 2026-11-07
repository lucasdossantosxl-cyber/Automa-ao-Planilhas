"""Cálculo do faturamento a partir de quantidade × preço de cada produto."""

from decimal import Decimal
from pathlib import Path

from consolidar import ler_csv, validar_vendas


def calcular_total(caminho: Path) -> Decimal:
    """Recalcula os subtotais e confere a coluna Faturamento, quando presente."""
    tabela = validar_vendas(ler_csv(Path(caminho)))
    return sum(tabela["Faturamento"], start=Decimal("0.00"))
