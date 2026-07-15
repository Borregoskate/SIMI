"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

evaluacion_import_service.py

Servicio de importación para la Carga 3:
Evaluación Técnica.

Reglas:
- El procedimiento del archivo debe coincidir con el seleccionado.
- El proveedor debe existir previamente.
- La clave debe pertenecer al procedimiento.
- Debe existir una propuesta inicial del proveedor para la clave.
- Si la evaluación no existe, se inserta.
- Si ya existe, se actualiza únicamente el resultado.
- Toda la carga se ejecuta en una sola transacción.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

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


TABLA_DESTINO = "evaluaciones_tecnicas"

COLUMNAS_REQUERIDAS_CARGA_EVALUACION = {
    "PROCEDIMIENTO": "PROCEDIMIENTO",
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "RESULTADO": "RESULTADO",
}

FILA_INICIAL_EXCEL = 6


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
    """
    Obtiene el procedimiento activo seleccionado.

    La consulta se delega completamente al Repository.
    """
    return ProcedimientosRepository().get_activo_by_id(
        id_procedimiento=id_procedimiento,
        conn=conn,
    )


def importar_evaluaciones_tecnicas(df, id_procedimiento):
    """Importa todas las evaluaciones dentro de una sola transacción."""
    resultado = crear_resultado_importacion(TABLA_DESTINO)

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
                    COLUMNAS_REQUERIDAS_CARGA_EVALUACION
                ),
                funcion_procesar_fila=procesar_fila_evaluacion,
                tabla=TABLA_DESTINO,
                fila_inicial_excel=FILA_INICIAL_EXCEL,
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
        resultado["errores"].append({
            "fila": None,
            "error": str(error),
        })
        return resultado


def procesar_fila_evaluacion(
    fila,
    conn=None,
    id_procedimiento=None,
):
    """Verifica e inserta o actualiza una evaluación técnica."""
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

    numero_seleccionado = obtener_valor(
        procedimiento,
        "numero_procedimiento",
    )
    numero_archivo = fila.get("PROCEDIMIENTO")

    if numero_archivo != numero_seleccionado:
        raise ValueError(
            "El procedimiento del archivo no coincide con el "
            "procedimiento seleccionado. "
            f"Archivo: {numero_archivo}. "
            f"Seleccionado: {numero_seleccionado}."
        )

    procedimiento_clave = (
        ClavesRepository().get_procedimiento_clave(
            id_procedimiento=id_procedimiento,
            clave=fila.get("CLAVE"),
            conn=conn,
        )
    )

    if not procedimiento_clave:
        raise ValueError(
            f"La clave {fila.get('CLAVE')} no pertenece al universo "
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
        rfc=fila.get("RFC"),
        conn=conn,
    )

    if not proveedor:
        raise ValueError(
            f"El proveedor con RFC {fila.get('RFC')} no existe. "
            "Debe haberse registrado previamente mediante la "
            "carga de propuestas iniciales."
        )

    id_proveedor = obtener_valor(
        proveedor,
        "id_proveedor",
    )

    propuesta_inicial = (
        PropuestasRepository().existe_propuesta_inicial(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )
    )

    if not propuesta_inicial:
        raise ValueError(
            "No existe una propuesta inicial para el proveedor "
            f"{fila.get('RFC')} y la clave {fila.get('CLAVE')} "
            "dentro del procedimiento seleccionado."
        )

    evaluaciones_repository = (
        EvaluacionesTecnicasRepository()
    )

    existente = evaluaciones_repository.existe_evaluacion(
        id_procedimiento=id_procedimiento,
        id_proveedor=id_proveedor,
        id_clave=id_clave,
        conn=conn,
    )

    resultado_tecnico = fila.get("RESULTADO")

    if existente:
        id_evaluacion = obtener_valor(
            existente,
            "id_evaluacion",
        )
        resultado_actual = obtener_valor(
            existente,
            "resultado",
        )

        if resultado_actual == resultado_tecnico:
            return {
                "accion": "omitido",
                "mensaje": (
                    "La evaluación ya existe con el mismo resultado."
                ),
            }

        evaluaciones_repository.actualizar_resultado(
            id_evaluacion=id_evaluacion,
            resultado=resultado_tecnico,
            conn=conn,
        )

        return {"accion": "actualizado"}

    evaluaciones_repository.crear_evaluacion(
        id_procedimiento=id_procedimiento,
        id_proveedor=id_proveedor,
        id_clave=id_clave,
        resultado=resultado_tecnico,
        conn=conn,
    )

    return {"accion": "insertado"}


__all__ = [
    "TABLA_DESTINO",
    "COLUMNAS_REQUERIDAS_CARGA_EVALUACION",
    "FILA_INICIAL_EXCEL",
    "obtener_procedimientos_activos",
    "obtener_valor",
    "validar_procedimiento_existe",
    "importar_evaluaciones_tecnicas",
    "procesar_fila_evaluacion",
]
