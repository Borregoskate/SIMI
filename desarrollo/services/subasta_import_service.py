"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

subasta_import_service.py

Servicio de importación para la Carga 4:
Subasta Privada.

Reglas:
- El procedimiento seleccionado debe existir y estar activo.
- La clave debe pertenecer al procedimiento.
- El proveedor debe existir previamente.
- Debe existir una propuesta inicial del proveedor para la clave.
- Debe existir una evaluación técnica POSITIVA.
- Si la propuesta SUBASTA no existe, se inserta.
- Si ya existe con valores diferentes, se actualiza.
- Si ya existe con los mismos valores, se omite.
- Toda la carga se ejecuta en una sola transacción.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, InvalidOperation

from repositories.claves_repository import ClavesRepository
from repositories.evaluaciones_tecnicas_repository import (
    EvaluacionesTecnicasRepository,
)
from repositories.procedimientos_repository import (
    ProcedimientosRepository,
)
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
TIPO_PROPUESTA = PropuestasRepository.TIPO_SUBASTA
FILA_INICIAL_EXCEL = 2

COLUMNAS_REQUERIDAS_CARGA_SUBASTA = {
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "CANTIDAD_OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS_ORIGEN": "PAIS_ORIGEN",
    "PRECIO_UNITARIO": "PRECIO_UNITARIO",
}


def obtener_procedimientos_activos():
    """Consulta procedimientos activos sin exponer conexiones a la UI."""
    return ProcedimientosRepository().get_activos()


def obtener_valor(registro, campo):
    """Obtiene un campo de un registro devuelto por BaseRepository."""
    if registro is None:
        return None

    if isinstance(registro, dict):
        return registro.get(campo)

    raise ValueError(
        f"No fue posible leer el campo {campo}. "
        "El registro no tiene formato de diccionario."
    )


def validar_procedimiento_existe(id_procedimiento, conn):
    """Obtiene el procedimiento activo seleccionado."""
    return ProcedimientosRepository().get_activo_by_id(
        id_procedimiento=id_procedimiento,
        conn=conn,
    )


def _decimal_comparable(valor):
    """
    Convierte valores numéricos a Decimal para comparar datos
    normalizados con valores NUMERIC devueltos por PostgreSQL.
    """
    if valor is None:
        return None

    if isinstance(valor, Decimal):
        return valor

    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return valor


def propuesta_subasta_sin_cambios(
    propuesta_existente,
    cantidad_ofertada,
    pais_origen,
    precio_unitario,
):
    """Indica si una subasta existente contiene los mismos valores."""
    cantidad_actual = _decimal_comparable(
        obtener_valor(
            propuesta_existente,
            "cantidad_ofertada",
        )
    )
    cantidad_nueva = _decimal_comparable(
        cantidad_ofertada
    )

    precio_actual = _decimal_comparable(
        obtener_valor(
            propuesta_existente,
            "precio_unitario",
        )
    )
    precio_nuevo = _decimal_comparable(
        precio_unitario
    )

    pais_actual = obtener_valor(
        propuesta_existente,
        "pais_origen",
    )

    return (
        cantidad_actual == cantidad_nueva
        and pais_actual == pais_origen
        and precio_actual == precio_nuevo
    )


def importar_subasta_privada(df, id_procedimiento):
    """Importa todas las posturas de subasta en una transacción."""
    resultado = crear_resultado_importacion(TABLA_DESTINO)
    resultado["tipo_propuesta"] = TIPO_PROPUESTA

    try:
        if df is None or df.empty:
            raise ValueError(
                "No se recibió información para importar."
            )

        if not id_procedimiento:
            raise ValueError(
                "No se recibió el procedimiento seleccionado."
            )

        with database_transaction() as conn:
            resultado = procesar_dataframe(
                df=df,
                columnas_requeridas=(
                    COLUMNAS_REQUERIDAS_CARGA_SUBASTA
                ),
                funcion_procesar_fila=procesar_fila_subasta,
                tabla=TABLA_DESTINO,
                fila_inicial_excel=FILA_INICIAL_EXCEL,
                conn=conn,
                detener_en_error=True,
                id_procedimiento=id_procedimiento,
            )

            resultado["tipo_propuesta"] = TIPO_PROPUESTA
            exigir_importacion_exitosa(resultado)

        return resultado

    except ImportacionConErrores as error:
        error.resultado["tipo_propuesta"] = TIPO_PROPUESTA
        return error.resultado

    except Exception as error:
        resultado["success"] = False
        resultado["errores"].append({
            "fila": None,
            "error": str(error),
        })
        return resultado


def procesar_fila_subasta(
    fila,
    conn=None,
    id_procedimiento=None,
):
    """Verifica e inserta, actualiza u omite una propuesta SUBASTA."""
    if conn is None:
        raise ValueError(
            "No se recibió una conexión activa a base de datos."
        )

    if not id_procedimiento:
        raise ValueError(
            "No se recibió el procedimiento seleccionado."
        )

    procedimiento = validar_procedimiento_existe(
        id_procedimiento=id_procedimiento,
        conn=conn,
    )

    if not procedimiento:
        raise ValueError(
            "El procedimiento seleccionado no existe o no está activo."
        )

    clave = fila.get("CLAVE")
    rfc = fila.get("RFC")

    procedimiento_clave = (
        ClavesRepository().get_procedimiento_clave(
            id_procedimiento=id_procedimiento,
            clave=clave,
            conn=conn,
        )
    )

    if not procedimiento_clave:
        raise ValueError(
            f"La clave {clave} no pertenece al universo "
            "del procedimiento seleccionado."
        )

    id_procedimiento_clave = obtener_valor(
        procedimiento_clave,
        "id_procedimiento_clave",
    )
    id_clave = obtener_valor(
        procedimiento_clave,
        "id_clave",
    )

    proveedor = ProveedoresRepository().get_by_rfc(
        rfc=rfc,
        conn=conn,
    )

    if not proveedor:
        raise ValueError(
            f"El proveedor con RFC {rfc} no existe. "
            "Debe haberse registrado previamente mediante la "
            "carga de propuestas iniciales."
        )

    id_proveedor = obtener_valor(
        proveedor,
        "id_proveedor",
    )

    propuestas_repository = PropuestasRepository()

    propuesta_inicial = (
        propuestas_repository.existe_propuesta_inicial(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )
    )

    if not propuesta_inicial:
        raise ValueError(
            "No existe una propuesta inicial para el proveedor "
            f"{rfc} y la clave {clave} dentro del "
            "procedimiento seleccionado."
        )

    evaluacion_positiva = (
        EvaluacionesTecnicasRepository()
        .proveedor_aprobado_para_clave(
            id_procedimiento=id_procedimiento,
            id_proveedor=id_proveedor,
            id_clave=id_clave,
            conn=conn,
        )
    )

    if not evaluacion_positiva:
        raise ValueError(
            "El proveedor no cuenta con una evaluación técnica "
            f"POSITIVA para el RFC {rfc} y la clave {clave}."
        )

    cantidad_ofertada = fila.get("CANTIDAD_OFERTADA")
    pais_origen = fila.get("PAIS_ORIGEN")
    precio_unitario = fila.get("PRECIO_UNITARIO")

    propuesta_subasta = (
        propuestas_repository.existe_propuesta_subasta(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )
    )

    if propuesta_subasta:
        if propuesta_subasta_sin_cambios(
            propuesta_existente=propuesta_subasta,
            cantidad_ofertada=cantidad_ofertada,
            pais_origen=pais_origen,
            precio_unitario=precio_unitario,
        ):
            return {
                "accion": "omitido",
                "mensaje": (
                    "La propuesta de subasta ya existe con "
                    "los mismos valores."
                ),
            }

        id_propuesta = obtener_valor(
            propuesta_subasta,
            "id_propuesta",
        )

        propuestas_repository.actualizar_propuesta_subasta(
            id_propuesta=id_propuesta,
            cantidad_ofertada=cantidad_ofertada,
            pais_origen=pais_origen,
            precio_unitario=precio_unitario,
            conn=conn,
        )

        return {"accion": "actualizado"}

    propuestas_repository.crear_propuesta_subasta(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        cantidad_ofertada=cantidad_ofertada,
        pais_origen=pais_origen,
        precio_unitario=precio_unitario,
        conn=conn,
    )

    return {"accion": "insertado"}


__all__ = [
    "TABLA_DESTINO",
    "TIPO_PROPUESTA",
    "FILA_INICIAL_EXCEL",
    "COLUMNAS_REQUERIDAS_CARGA_SUBASTA",
    "obtener_procedimientos_activos",
    "obtener_valor",
    "validar_procedimiento_existe",
    "propuesta_subasta_sin_cambios",
    "importar_subasta_privada",
    "procesar_fila_subasta",
]