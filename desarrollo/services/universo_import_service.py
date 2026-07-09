"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

universo_import_service.py

Servicio de importación para la Carga 1:
Universo del Procedimiento.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from config.database import get_connection
from services.import_engine import procesar_dataframe
from services.import_service import limpiar_texto, limpiar_clave, limpiar_numero

from repositories.procedimientos_repository import ProcedimientosRepository
from repositories.claves_repository import ClavesRepository
from repositories.procedimiento_claves_repository import ProcedimientoClavesRepository
from repositories.procedimiento_fases_repository import ProcedimientoFasesRepository


TABLA_DESTINO = "procedimiento_claves"

COLUMNAS_REQUERIDAS = [
    "CLAVE",
    "DESCRIPCION",
    "CANTIDAD_REQUERIDA"
]

FASE_CARGA_1 = "PROPUESTAS_RECIBIDAS"


def importar_universo_procedimiento(
    df,
    numero_procedimiento: str,
    tipo_procedimiento: str,
    ejercicio: int,
    descripcion: str | None = None
):
    """
    Importa el universo del procedimiento en base de datos.

    Flujo:
    1. Crea el procedimiento.
    2. Crea claves nuevas si no existen.
    3. Inserta relación procedimiento_claves.
    4. Registra fase inicial del procedimiento.
    """

    if df is None or df.empty:
        raise ValueError("No se recibió información para importar.")

    numero_procedimiento = limpiar_texto(numero_procedimiento)

    if not numero_procedimiento:
        raise ValueError("El número o nombre del procedimiento es obligatorio.")

    descripcion_final = _construir_descripcion(
        tipo_procedimiento=tipo_procedimiento,
        descripcion=descripcion
    )

    conn = None

    try:
        conn = get_connection()
        conn.autocommit = False

        procedimientos_repository = ProcedimientosRepository()

        procedimiento_existente = procedimientos_repository.get_by_numero_procedimiento(
            conn=conn,
            numero_procedimiento=numero_procedimiento
        )

        if procedimiento_existente:
            raise ValueError(
                "Ya existe un procedimiento registrado con ese número o nombre."
            )

        procedimiento = procedimientos_repository.crear_procedimiento(
            conn=conn,
            numero_procedimiento=numero_procedimiento,
            descripcion=descripcion_final,
            ejercicio=ejercicio,
            activo=True
        )

        contexto = {
            "id_procedimiento": procedimiento["id_procedimiento"]
        }

        resultado = procesar_dataframe(
            df=df,
            tabla=TABLA_DESTINO,
            columnas_requeridas=COLUMNAS_REQUERIDAS,
            funcion_procesar_fila=procesar_fila_universo,
            fila_inicial_excel=8,
            conn=conn,
            contexto=contexto,
            usar_transaccion=False,
            detener_en_error=False
        )

        if resultado["success"]:
            fases_repository = ProcedimientoFasesRepository()
            fases_repository.registrar_fase(
                conn=conn,
                id_procedimiento=procedimiento["id_procedimiento"],
                fase=FASE_CARGA_1
            )

            conn.commit()

            resultado["id_procedimiento"] = procedimiento["id_procedimiento"]
            resultado["numero_procedimiento"] = numero_procedimiento
        else:
            conn.rollback()

        return resultado

    except Exception as error:
        if conn is not None:
            conn.rollback()

        return {
            "success": False,
            "tabla": TABLA_DESTINO,
            "procesados": 0,
            "insertados": 0,
            "actualizados": 0,
            "omitidos": 0,
            "errores": [
                {
                    "fila": None,
                    "error": str(error)
                }
            ],
            "advertencias": []
        }

    finally:
        if conn is not None:
            conn.close()


def procesar_fila_universo(row, conn, contexto):
    """
    Procesa una fila del universo del procedimiento.
    """

    id_procedimiento = contexto["id_procedimiento"]

    clave = limpiar_clave(row.get("CLAVE"))
    descripcion = limpiar_texto(row.get("DESCRIPCION"))
    cantidad_requerida = limpiar_numero(row.get("CANTIDAD_REQUERIDA"))

    if not clave:
        raise ValueError("La clave es obligatoria.")

    if not descripcion:
        raise ValueError("La descripción es obligatoria.")

    claves_repository = ClavesRepository()
    procedimiento_claves_repository = ProcedimientoClavesRepository()

    clave_bd = claves_repository.get_by_clave(clave)

    if not clave_bd:
        clave_bd = claves_repository.crear_clave(
            clave=clave,
            descripcion=descripcion,
            id_categoria=None
        )

    relacion_existente = procedimiento_claves_repository.get_by_procedimiento_clave(
        conn=conn,
        id_procedimiento=id_procedimiento,
        id_clave=clave_bd["id_clave"]
    )

    if relacion_existente:
        procedimiento_claves_repository.actualizar_cantidad(
            conn=conn,
            id_procedimiento_clave=relacion_existente["id_procedimiento_clave"],
            cantidad_requerida=cantidad_requerida
        )

        return {
            "accion": "actualizado",
            "advertencia": "La clave ya existía en el procedimiento; se actualizó la cantidad requerida."
        }

    procedimiento_claves_repository.crear(
        conn=conn,
        id_procedimiento=id_procedimiento,
        id_clave=clave_bd["id_clave"],
        cantidad_requerida=cantidad_requerida
    )

    return {
        "accion": "insertado"
    }


def _construir_descripcion(
    tipo_procedimiento: str,
    descripcion: str | None
):
    """
    Construye la descripción final del procedimiento.

    Nota:
    La tabla procedimientos no tiene todavía columna tipo_procedimiento,
    por eso conservamos el tipo dentro de la descripción.
    """

    tipo_procedimiento = limpiar_texto(tipo_procedimiento)
    descripcion = limpiar_texto(descripcion)

    partes = []

    if tipo_procedimiento:
        partes.append(f"Tipo de procedimiento: {tipo_procedimiento}")

    if descripcion:
        partes.append(descripcion)

    if not partes:
        return None

    return "\n".join(partes)