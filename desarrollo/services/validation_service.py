"""
==============================================================
SIMI

validation_service.py

Servicio de validaciones de negocio.
==============================================================
"""


def validar_rfc(rfc: str) -> bool:
    return bool(rfc)


def validar_clave(clave: str) -> bool:
    return bool(clave)


def validar_precio(precio) -> bool:
    return precio is not None and precio >= 0


def validar_cantidad(cantidad) -> bool:
    return cantidad is not None and cantidad >= 0