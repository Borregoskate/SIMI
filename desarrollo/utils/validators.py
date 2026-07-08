"""
Validadores generales.
"""


def es_texto_valido(valor):
    return valor is not None and str(valor).strip() != ""


def es_numero_positivo(valor):
    try:
        return float(valor) >= 0
    except (TypeError, ValueError):
        return False