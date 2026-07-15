"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

propuestas_import_service.py

Servicio de importación para la Carga 2: Propuestas Iniciales.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

from repositories.claves_repository import ClavesRepository
from repositories.procedimientos_repository import ProcedimientosRepository
from repositories.propuestas_repository import PropuestasRepository
from repositories.proveedores_repository import ProveedoresRepository
from services.database_service import database_transaction
from services.import_engine import (
    ImportacionConErrores,
    crear_resultado_importacion,
    exigir_importacion_exitosa,
    procesar_dataframe,
)

TABLA_DESTINO = "propuestas"
COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS = {
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "CANTIDAD_OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS_ORIGEN": "PAIS_ORIGEN",
    "PRECIO_UNITARIO": "PRECIO_UNITARIO",
}


def obtener_procedimientos_activos():
    """Consulta procedimientos activos sin exponer conexiones a la interfaz."""
    return ProcedimientosRepository().get_activos()


def importar_propuestas_iniciales(df, id_procedimiento):
    """Importa todas las propuestas dentro de una sola transacción."""

    resultado = crear_resultado_importacion(TABLA_DESTINO)

    try:
        if df is None or df.empty:
            raise ValueError("No se recibió información para importar.")
        if not id_procedimiento:
            raise ValueError("No se recibió el procedimiento seleccionado.")

        with database_transaction() as conn:
            resultado = procesar_dataframe(
                df=df,
                columnas_requeridas=COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS,
                funcion_procesar_fila=procesar_fila_propuesta,
                tabla=TABLA_DESTINO,
                fila_inicial_excel=2,
                conn=conn,
                detener_en_error=True,
                id_procedimiento=id_procedimiento,
            )
            exigir_importacion_exitosa(resultado)

        return resultado

    except ImportacionConErrores as error:
        return error.resultado
    except Exception as error:
        resultado["success"] = False
        resultado["errores"].append({"fila": None, "error": str(error)})
        return resultado


def obtener_valor_id(registro, campo):
    if registro is None:
        return None
    if isinstance(registro, dict):
        return registro.get(campo)
    raise ValueError(
        f"No fue posible leer el campo {campo}. "
        "El registro no tiene formato de diccionario."
    )


def validar_procedimiento_existe(id_procedimiento, conn):
    query = """
        SELECT *
        FROM simi.procedimientos
        WHERE id_procedimiento = %s
          AND activo = TRUE
        LIMIT 1;
    """
    return ProcedimientosRepository().custom_query(
        query=query,
        params=(id_procedimiento,),
        conn=conn,
        fetchone=True,
    )


def procesar_fila_propuesta(fila, conn=None, id_procedimiento=None):
    if conn is None:
        raise ValueError("No se recibió una conexión activa a base de datos.")
    if not id_procedimiento:
        raise ValueError("No se recibió el procedimiento seleccionado.")

    procedimiento = validar_procedimiento_existe(id_procedimiento, conn)
    if not procedimiento:
        raise ValueError("El procedimiento seleccionado no existe o no está activo.")

    procedimiento_clave = ClavesRepository().get_procedimiento_clave(
        id_procedimiento=id_procedimiento,
        clave=fila.get("CLAVE"),
        conn=conn,
    )
    if not procedimiento_clave:
        raise ValueError(
            f"La clave {fila.get('CLAVE')} no pertenece al universo "
            "del procedimiento seleccionado."
        )

    id_procedimiento_clave = obtener_valor_id(
        procedimiento_clave,
        "id_procedimiento_clave",
    )

    proveedores_repository = ProveedoresRepository()
    proveedor = proveedores_repository.get_by_rfc(
        rfc=fila.get("RFC"),
        conn=conn,
    )
    if proveedor:
        id_proveedor = obtener_valor_id(proveedor, "id_proveedor")
    else:
        proveedor = proveedores_repository.crear_proveedor(
            rfc=fila.get("RFC"),
            razon_social=fila.get("RAZON_SOCIAL"),
            conn=conn,
        )
        id_proveedor = obtener_valor_id(proveedor, "id_proveedor")

    propuestas_repository = PropuestasRepository()
    existente = propuestas_repository.existe_propuesta_inicial(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        conn=conn,
    )
    if existente:
        return {
            "accion": "omitido",
            "mensaje": (
                "Ya existe una propuesta inicial para este proveedor y esta clave."
            ),
        }

    propuestas_repository.crear_propuesta_inicial(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        cantidad_ofertada=fila.get("CANTIDAD_OFERTADA"),
        pais_origen=fila.get("PAIS_ORIGEN"),
        precio_unitario=fila.get("PRECIO_UNITARIO"),
        conn=conn,
    )
    return {"accion": "insertado"}


__all__ = [
    "TABLA_DESTINO",
    "COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS",
    "obtener_procedimientos_activos",
    "importar_propuestas_iniciales",
    "obtener_valor_id",
    "validar_procedimiento_existe",
    "procesar_fila_propuesta",
]
