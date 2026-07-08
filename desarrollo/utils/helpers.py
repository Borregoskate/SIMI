"""
Funciones auxiliares generales.
"""


def limpiar_texto(valor):
    if valor is None:
        return ""

    return str(valor).strip().upper()


def normalizar_rfc(rfc):
    return limpiar_texto(rfc)


def normalizar_clave(clave):
    return limpiar_texto(clave)