"""
==============================================================
SIMI

permissions.py

Control de permisos por rol.
==============================================================
"""

from config.constants import (
    ROL_ADMINISTRADOR_MAESTRO,
    ROL_ADMINISTRADOR,
    ROL_ANALISTA,
    ROL_CONSULTA
)


def es_administrador_maestro(rol: str) -> bool:
    return rol == ROL_ADMINISTRADOR_MAESTRO


def puede_administrar_usuarios(rol: str) -> bool:
    return rol in [
        ROL_ADMINISTRADOR_MAESTRO,
        ROL_ADMINISTRADOR
    ]


def puede_cargar_archivos(rol: str) -> bool:
    return rol in [
        ROL_ADMINISTRADOR_MAESTRO,
        ROL_ADMINISTRADOR,
        ROL_ANALISTA
    ]


def puede_consultar(rol: str) -> bool:
    return rol in [
        ROL_ADMINISTRADOR_MAESTRO,
        ROL_ADMINISTRADOR,
        ROL_ANALISTA,
        ROL_CONSULTA
    ]


def puede_eliminar_datos(rol: str) -> bool:
    return rol == ROL_ADMINISTRADOR_MAESTRO