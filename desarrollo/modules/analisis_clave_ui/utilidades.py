"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

utilidades.py

Utilidades exclusivamente visuales para Análisis por Clave.

No contiene reglas de negocio ni cálculos analíticos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from decimal import Decimal, InvalidOperation


TEXTO_SIN_INFORMACION = "Sin información"


def _decimal_seguro(valor):
    """Convierte un valor a Decimal solo para formato visual."""
    if valor is None:
        return None

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not numero.is_finite():
        return None

    return numero


def formatear_moneda(valor):
    """Formatea un valor monetario para visualización."""
    numero = _decimal_seguro(valor)

    if numero is None:
        return TEXTO_SIN_INFORMACION

    return f"${numero:,.2f}"


def formatear_porcentaje(valor):
    """Formatea un porcentaje para visualización."""
    numero = _decimal_seguro(valor)

    if numero is None:
        return TEXTO_SIN_INFORMACION

    return f"{numero:,.2f}%"


def formatear_entero(valor):
    """Formatea conteos para visualización."""
    numero = _decimal_seguro(valor)

    if numero is None:
        return "0"

    return f"{int(numero):,}"


def formatear_numero(valor):
    """Formatea cantidades conservando hasta dos decimales."""
    numero = _decimal_seguro(valor)

    if numero is None:
        return TEXTO_SIN_INFORMACION

    if numero == numero.to_integral():
        return f"{int(numero):,}"

    return f"{numero:,.2f}"


def formatear_si_no(valor):
    """Convierte un booleano a Sí o No."""
    return "Sí" if bool(valor) else "No"


def obtener_icono_clasificacion(clasificacion):
    """Devuelve un icono visual según la clasificación."""
    iconos = {
        "AHORRO": "📉",
        "SIN CAMBIO": "➖",
        "INCREMENTO": "📈",
        "INFORMACIÓN INSUFICIENTE": "ℹ️",
    }

    return iconos.get(clasificacion, "ℹ️")


def obtener_icono_estado(estado):
    """Devuelve un icono visual según el estado analítico."""
    iconos = {
        "SIN PROPUESTAS": "⚪",
        "SOLO OFERTA INICIAL": "🔵",
        "SIN APROBACIÓN TÉCNICA": "🔴",
        "CON OFERTA VIABLE": "🟢",
        "CON SUBASTA": "🟣",
        "ADJUDICADO": "✅",
        "SIN INFORMACIÓN": "ℹ️",
    }

    return iconos.get(estado, "ℹ️")
