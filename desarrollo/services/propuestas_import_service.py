"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

propuestas_import_service.py

Servicio de importación para la Carga 2:
Propuestas Iniciales.

Este servicio procesa filas ya normalizadas y prevalidas,
y las inserta mediante el Motor General de Importación.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.procedimientos_repository import ProcedimientosRepository
from repositories.claves_repository import ClavesRepository
from repositories.proveedores_repository import ProveedoresRepository
from repositories.propuestas_repository import PropuestasRepository


def obtener_valor_id(registro, campo):
    """
    Obtiene un valor de un registro devuelto por BaseRepository.

    Protege contra respuestas tipo dict o tipo tuple/list.
    En condiciones normales debe venir como dict.
    """

    if registro is None:
        return None

    if isinstance(registro, dict):
        return registro.get(campo)

    raise ValueError(
        f"No fue posible leer el campo {campo}. "
        "El registro no tiene formato de diccionario."
    )


def validar_procedimiento_existe(id_procedimiento, conn):
    """
    Valida que el procedimiento exista y esté activo.
    """

    procedimientos_repository = ProcedimientosRepository()

    query = """
        SELECT *
        FROM simi.procedimientos
        WHERE id_procedimiento = %s
          AND activo = TRUE
        LIMIT 1;
    """

    result = procedimientos_repository.custom_query(
        query,
        params=(id_procedimiento,),
        conn=conn,
        fetch=True
    )

    return result[0] if result else None


def procesar_fila_propuesta(
    fila,
    conn=None,
    id_procedimiento=None
):
    """
    Procesa una fila de propuestas iniciales.

    Reglas:
    - El procedimiento debe existir y estar activo.
    - La clave debe pertenecer al universo del procedimiento.
    - El proveedor se busca por RFC.
    - Si el proveedor no existe, se crea.
    - No se permite duplicar propuesta inicial para el mismo
      proveedor y clave dentro del mismo procedimiento.
    """

    if not conn:
        raise ValueError("No se recibió una conexión activa a base de datos.")

    if not id_procedimiento:
        raise ValueError("No se recibió el procedimiento seleccionado.")

    rfc = fila.get("RFC")
    razon_social = fila.get("RAZON_SOCIAL")
    clave = fila.get("CLAVE")
    cantidad_ofertada = fila.get("CANTIDAD_OFERTADA")
    pais_origen = fila.get("PAIS_ORIGEN")
    precio_unitario = fila.get("PRECIO_UNITARIO")

    procedimiento = validar_procedimiento_existe(
        id_procedimiento=id_procedimiento,
        conn=conn
    )

    if not procedimiento:
        raise ValueError(
            "El procedimiento seleccionado no existe o no está activo."
        )

    claves_repository = ClavesRepository()

    procedimiento_clave = claves_repository.get_procedimiento_clave(
        id_procedimiento=id_procedimiento,
        clave=clave,
        conn=conn
    )

    if not procedimiento_clave:
        raise ValueError(
            f"La clave {clave} no pertenece al universo "
            "del procedimiento seleccionado."
        )

    id_procedimiento_clave = obtener_valor_id(
        procedimiento_clave,
        "id_procedimiento_clave"
    )

    proveedores_repository = ProveedoresRepository()

    proveedor = proveedores_repository.get_by_rfc(
        rfc=rfc,
        conn=conn
    )

    if proveedor:
        id_proveedor = obtener_valor_id(
            proveedor,
            "id_proveedor"
        )
    else:
        proveedor = proveedores_repository.crear_proveedor(
            rfc=rfc,
            razon_social=razon_social,
            conn=conn
        )

        id_proveedor = obtener_valor_id(
            proveedor,
            "id_proveedor"
        )

    propuestas_repository = PropuestasRepository()

    propuesta_existente = propuestas_repository.existe_propuesta_inicial(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        conn=conn
    )

    if propuesta_existente:
        return {
            "accion": "omitido",
            "mensaje": (
                "Ya existe una propuesta inicial para este proveedor "
                "y esta clave."
            )
        }

    propuestas_repository.crear_propuesta_inicial(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        cantidad_ofertada=cantidad_ofertada,
        pais_origen=pais_origen,
        precio_unitario=precio_unitario,
        conn=conn
    )

    return {
        "accion": "insertado"
    }