"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

adjudicaciones_import_service.py

Servicio de importación para la Carga 5:
Adjudicaciones.

Reglas:
- El procedimiento debe existir y estar activo.
- El procedimiento del archivo debe coincidir con el seleccionado.
- La clave debe pertenecer al procedimiento.
- El proveedor debe existir.
- Debe existir evaluación técnica POSITIVA.
- Debe existir una propuesta viable.
- Se prioriza SUBASTA y, en su ausencia, se acepta INICIAL.
- Una clave puede tener un máximo de tres proveedores.
- Si no existe adjudicación, se inserta.
- Si existe con valores diferentes, se actualiza.
- Si existe con los mismos valores, se omite.
- Toda la carga se ejecuta dentro de una sola transacción.

Este servicio NO:
- Normaliza datos.
- Contiene SQL.
- Abre conexiones directamente.
- Realiza commit o rollback manual.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from decimal import Decimal, InvalidOperation

from repositories.adjudicaciones_repository import (
    AdjudicacionesRepository,
)
from repositories.claves_repository import ClavesRepository
from repositories.evaluaciones_tecnicas_repository import (
    EvaluacionesTecnicasRepository,
)
from repositories.procedimientos_repository import (
    ProcedimientosRepository,
)
from repositories.propuestas_repository import (
    PropuestasRepository,
)
from repositories.proveedores_repository import (
    ProveedoresRepository,
)
from services.database_service import database_transaction
from services.import_engine import (
    ImportacionConErrores,
    crear_resultado_importacion,
    exigir_importacion_exitosa,
    procesar_dataframe,
)


TABLA_DESTINO = "adjudicaciones"
FILA_INICIAL_EXCEL = 2
MAXIMO_PROVEEDORES_POR_CLAVE = 3

COLUMNAS_REQUERIDAS_CARGA_ADJUDICACIONES = {
    "PROCEDIMIENTO": "PROCEDIMIENTO",
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "CANTIDAD_ADJUDICADA": "CANTIDAD_ADJUDICADA",
    "PORCENTAJE_ADJUDICADO": "PORCENTAJE_ADJUDICADO",
    "PRECIO_UNITARIO_ADJUDICADO": (
        "PRECIO_UNITARIO_ADJUDICADO"
    ),
}


def obtener_procedimientos_activos():
    """
    Devuelve los procedimientos activos disponibles para la UI.
    """

    return ProcedimientosRepository().get_activos()


def obtener_valor(registro, campo):
    """
    Obtiene un campo de un registro devuelto por BaseRepository.
    """

    if registro is None:
        return None

    if isinstance(registro, dict):
        return registro.get(campo)

    raise ValueError(
        f"No fue posible leer el campo {campo}. "
        "El registro no tiene formato de diccionario."
    )


def _decimal_comparable(valor):
    """
    Convierte valores numéricos a Decimal para realizar
    comparaciones seguras con valores NUMERIC de PostgreSQL.
    """

    if valor is None:
        return None

    if isinstance(valor, Decimal):
        return valor

    try:
        return Decimal(str(valor))

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return valor


def adjudicacion_sin_cambios(
    adjudicacion_existente,
    cantidad_adjudicada,
    porcentaje_adjudicado,
    precio_unitario_adjudicado,
):
    """
    Indica si una adjudicación existente contiene exactamente
    los mismos valores que la fila normalizada del archivo.
    """

    cantidad_actual = _decimal_comparable(
        obtener_valor(
            adjudicacion_existente,
            "cantidad_adjudicada",
        )
    )
    cantidad_nueva = _decimal_comparable(
        cantidad_adjudicada
    )

    porcentaje_actual = _decimal_comparable(
        obtener_valor(
            adjudicacion_existente,
            "porcentaje_adjudicado",
        )
    )
    porcentaje_nuevo = _decimal_comparable(
        porcentaje_adjudicado
    )

    precio_actual = _decimal_comparable(
        obtener_valor(
            adjudicacion_existente,
            "precio_unitario_adjudicado",
        )
    )
    precio_nuevo = _decimal_comparable(
        precio_unitario_adjudicado
    )

    return (
        cantidad_actual == cantidad_nueva
        and porcentaje_actual == porcentaje_nuevo
        and precio_actual == precio_nuevo
    )


def validar_procedimiento_archivo(
    procedimiento,
    procedimiento_archivo,
):
    """
    Valida que el procedimiento escrito en el archivo coincida
    con el procedimiento seleccionado en Streamlit.
    """

    numero_procedimiento = obtener_valor(
        procedimiento,
        "numero_procedimiento",
    )

    if numero_procedimiento != procedimiento_archivo:
        raise ValueError(
            "El procedimiento del archivo no coincide con el "
            "procedimiento seleccionado. "
            f"Archivo: {procedimiento_archivo}. "
            f"Seleccionado: {numero_procedimiento}."
        )


def obtener_propuesta_viable(
    propuestas_repository,
    id_procedimiento_clave,
    id_proveedor,
    conn,
):
    """
    Busca la propuesta económica válida para la adjudicación.

    Prioridad:
    1. SUBASTA.
    2. INICIAL.
    """

    propuesta_subasta = (
        propuestas_repository.existe_propuesta_subasta(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )
    )

    if propuesta_subasta:
        return propuesta_subasta

    return propuestas_repository.existe_propuesta_inicial(
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        conn=conn,
    )


def _obtener_entero_consulta(registro, campo):
    """
    Obtiene un entero desde el resultado agregado de un Repository.
    """

    valor = obtener_valor(
        registro,
        campo,
    )

    if valor is None:
        return 0

    return int(valor)


def validar_limite_proveedores(
    adjudicaciones_repository,
    id_procedimiento,
    id_clave,
    adjudicacion_existente,
    conn,
):
    """
    Verifica el máximo de tres proveedores adjudicados por clave.

    El límite únicamente debe comprobarse cuando se insertará una
    nueva combinación procedimiento + clave + proveedor.
    """

    if adjudicacion_existente:
        return

    resultado_conteo = (
        adjudicaciones_repository
        .contar_proveedores_adjudicados(
            id_procedimiento=id_procedimiento,
            id_clave=id_clave,
            conn=conn,
        )
    )

    total = _obtener_entero_consulta(
        resultado_conteo,
        "total",
    )

    if total >= MAXIMO_PROVEEDORES_POR_CLAVE:
        raise ValueError(
            "La clave ya tiene el máximo de tres proveedores "
            "adjudicados dentro del procedimiento."
        )


def importar_adjudicaciones(
    df,
    id_procedimiento,
):
    """
    Importa todas las adjudicaciones dentro de una sola
    transacción.

    El DataFrame debe llegar previamente normalizado y validado
    por prevalidacion_adjudicaciones_service.py.
    """

    resultado = crear_resultado_importacion(
        TABLA_DESTINO
    )

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
                    COLUMNAS_REQUERIDAS_CARGA_ADJUDICACIONES
                ),
                funcion_procesar_fila=(
                    procesar_fila_adjudicacion
                ),
                tabla=TABLA_DESTINO,
                fila_inicial_excel=FILA_INICIAL_EXCEL,
                conn=conn,
                detener_en_error=True,
                id_procedimiento=id_procedimiento,
            )

            exigir_importacion_exitosa(
                resultado
            )

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


def procesar_fila_adjudicacion(
    fila,
    conn=None,
    id_procedimiento=None,
):
    """
    Verifica e inserta, actualiza u omite una adjudicación.
    """

    if conn is None:
        raise ValueError(
            "No se recibió una conexión activa a base de datos."
        )

    if not id_procedimiento:
        raise ValueError(
            "No se recibió el procedimiento seleccionado."
        )

    procedimientos_repository = (
        ProcedimientosRepository()
    )
    claves_repository = (
        ClavesRepository()
    )
    proveedores_repository = (
        ProveedoresRepository()
    )
    propuestas_repository = (
        PropuestasRepository()
    )
    evaluaciones_repository = (
        EvaluacionesTecnicasRepository()
    )
    adjudicaciones_repository = (
        AdjudicacionesRepository()
    )

    procedimiento = (
        procedimientos_repository.get_activo_by_id(
            id_procedimiento=id_procedimiento,
            conn=conn,
        )
    )

    if not procedimiento:
        raise ValueError(
            "El procedimiento seleccionado no existe "
            "o no está activo."
        )

    procedimiento_archivo = fila.get(
        "PROCEDIMIENTO"
    )

    validar_procedimiento_archivo(
        procedimiento=procedimiento,
        procedimiento_archivo=procedimiento_archivo,
    )

    clave = fila.get(
        "CLAVE"
    )
    rfc = fila.get(
        "RFC"
    )

    procedimiento_clave = (
        claves_repository.get_procedimiento_clave(
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

    proveedor = proveedores_repository.get_by_rfc(
        rfc=rfc,
        conn=conn,
    )

    if not proveedor:
        raise ValueError(
            f"El proveedor con RFC {rfc} no existe."
        )

    id_proveedor = obtener_valor(
        proveedor,
        "id_proveedor",
    )

    evaluacion_positiva = (
        evaluaciones_repository
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

    propuesta_viable = obtener_propuesta_viable(
        propuestas_repository=propuestas_repository,
        id_procedimiento_clave=id_procedimiento_clave,
        id_proveedor=id_proveedor,
        conn=conn,
    )

    if not propuesta_viable:
        raise ValueError(
            "No existe una propuesta SUBASTA ni una propuesta "
            f"INICIAL para el RFC {rfc} y la clave {clave}."
        )

    adjudicacion_existente = (
        adjudicaciones_repository.get_by_combinacion(
            id_procedimiento=id_procedimiento,
            id_clave=id_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )
    )

    validar_limite_proveedores(
        adjudicaciones_repository=(
            adjudicaciones_repository
        ),
        id_procedimiento=id_procedimiento,
        id_clave=id_clave,
        adjudicacion_existente=adjudicacion_existente,
        conn=conn,
    )

    cantidad_adjudicada = fila.get(
        "CANTIDAD_ADJUDICADA"
    )
    porcentaje_adjudicado = int(
        fila.get(
            "PORCENTAJE_ADJUDICADO"
        )
    )
    precio_unitario_adjudicado = fila.get(
        "PRECIO_UNITARIO_ADJUDICADO"
    )

    if adjudicacion_existente:
        if adjudicacion_sin_cambios(
            adjudicacion_existente=(
                adjudicacion_existente
            ),
            cantidad_adjudicada=cantidad_adjudicada,
            porcentaje_adjudicado=porcentaje_adjudicado,
            precio_unitario_adjudicado=(
                precio_unitario_adjudicado
            ),
        ):
            return {
                "accion": "omitido",
                "mensaje": (
                    "La adjudicación ya existe con "
                    "los mismos valores."
                ),
            }

        id_adjudicacion = obtener_valor(
            adjudicacion_existente,
            "id_adjudicacion",
        )

        adjudicaciones_repository.actualizar_adjudicacion(
            id_adjudicacion=id_adjudicacion,
            cantidad_adjudicada=cantidad_adjudicada,
            porcentaje_adjudicado=porcentaje_adjudicado,
            precio_unitario_adjudicado=(
                precio_unitario_adjudicado
            ),
            conn=conn,
        )

        return {
            "accion": "actualizado",
        }

    adjudicaciones_repository.crear_adjudicacion(
        id_procedimiento=id_procedimiento,
        id_clave=id_clave,
        id_proveedor=id_proveedor,
        cantidad_adjudicada=cantidad_adjudicada,
        porcentaje_adjudicado=porcentaje_adjudicado,
        precio_unitario_adjudicado=(
            precio_unitario_adjudicado
        ),
        conn=conn,
    )

    return {
        "accion": "insertado",
    }


__all__ = [
    "TABLA_DESTINO",
    "FILA_INICIAL_EXCEL",
    "MAXIMO_PROVEEDORES_POR_CLAVE",
    "COLUMNAS_REQUERIDAS_CARGA_ADJUDICACIONES",
    "obtener_procedimientos_activos",
    "obtener_valor",
    "adjudicacion_sin_cambios",
    "validar_procedimiento_archivo",
    "obtener_propuesta_viable",
    "validar_limite_proveedores",
    "importar_adjudicaciones",
    "procesar_fila_adjudicacion",
]