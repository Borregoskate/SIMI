"""Utilidades exclusivamente visuales para Análisis por Proveedor."""

from decimal import Decimal, InvalidOperation

import pandas as pd


TEXTO_SIN_INFORMACION = "Sin información"


def _decimal_seguro(valor):
    if valor is None:
        return None
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return numero if numero.is_finite() else None


def formatear_moneda(valor):
    numero = _decimal_seguro(valor)
    return TEXTO_SIN_INFORMACION if numero is None else f"${numero:,.2f}"


def formatear_porcentaje(valor):
    numero = _decimal_seguro(valor)
    return TEXTO_SIN_INFORMACION if numero is None else f"{numero:,.2f}%"


def formatear_entero(valor):
    numero = _decimal_seguro(valor)
    return "0" if numero is None else f"{int(numero):,}"


def formatear_numero(valor):
    numero = _decimal_seguro(valor)
    if numero is None:
        return TEXTO_SIN_INFORMACION
    if numero == numero.to_integral():
        return f"{int(numero):,}"
    return f"{numero:,.2f}"


def dataframe_desde_registros(registros, columnas=None):
    dataframe = pd.DataFrame([dict(item) for item in registros or []])
    if dataframe.empty or not columnas:
        return dataframe
    disponibles = [columna for columna in columnas if columna in dataframe.columns]
    return dataframe[disponibles]


def etiqueta_procedimiento(item):
    numero = item.get("numero_procedimiento") or "Sin procedimiento"
    ejercicio = item.get("ejercicio")
    if ejercicio is not None and str(ejercicio) not in str(numero):
        return f"{numero} — {ejercicio}"
    return str(numero)
