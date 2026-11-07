"""Conversão de dinheiro sem a imprecisão de números de ponto flutuante."""

import re
from decimal import Decimal, InvalidOperation

CENTAVO = Decimal("0.01")


def converter_decimal(valor: object) -> Decimal:
    """Aceita 1500.00, 1500,00 ou 1.500,00; rejeita valores inválidos."""
    texto = str(valor).strip()
    if "," in texto:
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+),\d{1,2}", texto):
            raise ValueError(f"Valor monetário inválido: {valor!r}.")
        texto = texto.replace(".", "").replace(",", ".")
    try:
        numero = Decimal(texto)
        if not numero.is_finite() or numero < 0:
            raise ValueError("O valor deve ser finito e não negativo.")
        arredondado = numero.quantize(CENTAVO)
    except (InvalidOperation, TypeError) as erro:
        raise ValueError(f"Valor monetário inválido: {valor!r}.") from erro
    if numero != arredondado:
        raise ValueError("O valor deve ter no máximo duas casas decimais.")
    return arredondado


def formatar_brl(valor: Decimal) -> str:
    """Formata um valor como R$ 1.500,00 sem depender do locale da máquina."""
    texto = f"{converter_decimal(valor):,.2f}"
    return "R$ " + texto.translate(str.maketrans({",": ".", ".": ","}))
