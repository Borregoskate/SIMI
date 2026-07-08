"""
Funciones de formato.
"""


def formatear_moneda(valor):
    if valor is None:
        return "$0.00"

    return f"${valor:,.2f}"


def formatear_porcentaje(valor):
    if valor is None:
        return "0.00%"

    return f"{valor:.2f}%"