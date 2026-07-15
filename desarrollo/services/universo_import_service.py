"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

universo_import_service.py

Servicio de importación para la Carga 1: Universo.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

from repositories.claves_repository import ClavesRepository
from repositories.procedimiento_claves_repository import ProcedimientoClavesRepository
from repositories.procedimiento_fases_repository import ProcedimientoFasesRepository
from repositories.procedimientos_repository import ProcedimientosRepository
from services.database_service import database_transaction
from services.import_engine import (
    ImportacionConErrores,
    crear_resultado_importacion,
    exigir_importacion_exitosa,
    procesar_dataframe,
)
from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_texto,
)

TABLA_DESTINO = "procedimiento_claves"
COLUMNAS_REQUERIDAS = ["CLAVE", "DESCRIPCION", "CANTIDAD_REQUERIDA"]
FASE_CARGA_1 = "PROPUESTAS_RECIBIDAS"


def importar_universo_procedimiento(
    df,
    numero_procedimiento: str,
    tipo_procedimiento: str,
    ejercicio: int,
    descripcion: str | None = None,
):
    """Importa el universo completo dentro de una sola transacción."""

    resultado = crear_resultado_importacion(TABLA_DESTINO)

    try:
        _validar_datos_generales(df, numero_procedimiento, ejercicio)
        numero_normalizado = normalizar_texto(numero_procedimiento)
        descripcion_final = _construir_descripcion(
            tipo_procedimiento=tipo_procedimiento,
            descripcion=descripcion,
        )

        with database_transaction() as conn:
            procedimientos_repository = ProcedimientosRepository()
            existente = procedimientos_repository.get_by_numero_procedimiento(
                numero_procedimiento=numero_normalizado,
                conn=conn,
            )
            if existente:
                raise ValueError(
                    "Ya existe un procedimiento registrado con ese número o nombre."
                )

            procedimiento = procedimientos_repository.crear_procedimiento(
                numero_procedimiento=numero_normalizado,
                descripcion=descripcion_final,
                ejercicio=int(ejercicio),
                activo=True,
                conn=conn,
            )

            resultado = procesar_dataframe(
                df=df,
                tabla=TABLA_DESTINO,
                columnas_requeridas=COLUMNAS_REQUERIDAS,
                funcion_procesar_fila=procesar_fila_universo,
                fila_inicial_excel=8,
                conn=conn,
                contexto={"id_procedimiento": procedimiento["id_procedimiento"]},
                detener_en_error=False,
            )
            exigir_importacion_exitosa(resultado)

            ProcedimientoFasesRepository().registrar_fase(
                id_procedimiento=procedimiento["id_procedimiento"],
                fase=FASE_CARGA_1,
                conn=conn,
            )

            resultado["id_procedimiento"] = procedimiento["id_procedimiento"]
            resultado["numero_procedimiento"] = numero_normalizado

        return resultado

    except ImportacionConErrores as error:
        return error.resultado
    except Exception as error:
        resultado["success"] = False
        resultado["errores"].append({"fila": None, "error": str(error)})
        return resultado


def procesar_fila_universo(row, conn, contexto):
    """Procesa una fila ya normalizada y validada."""

    id_procedimiento = contexto["id_procedimiento"]
    clave = normalizar_clave(row.get("CLAVE"))
    descripcion = normalizar_texto(row.get("DESCRIPCION"))
    cantidad_requerida = normalizar_decimal(row.get("CANTIDAD_REQUERIDA"))

    if not clave:
        raise ValueError("La clave es obligatoria.")
    if not descripcion:
        raise ValueError("La descripción es obligatoria.")

    claves_repository = ClavesRepository()
    relaciones_repository = ProcedimientoClavesRepository()

    clave_bd = claves_repository.get_by_clave(clave=clave, conn=conn)
    if not clave_bd:
        clave_bd = claves_repository.crear_clave(
            clave=clave,
            descripcion=descripcion,
            id_categoria=None,
            conn=conn,
        )

    relacion = relaciones_repository.get_by_procedimiento_clave(
        id_procedimiento=id_procedimiento,
        id_clave=clave_bd["id_clave"],
        conn=conn,
    )

    if relacion:
        relaciones_repository.actualizar_cantidad(
            id_procedimiento_clave=relacion["id_procedimiento_clave"],
            cantidad_requerida=cantidad_requerida,
            conn=conn,
        )
        return {
            "accion": "actualizado",
            "advertencia": (
                "La clave ya existía en el procedimiento; "
                "se actualizó la cantidad requerida."
            ),
        }

    relaciones_repository.crear(
        id_procedimiento=id_procedimiento,
        id_clave=clave_bd["id_clave"],
        cantidad_requerida=cantidad_requerida,
        conn=conn,
    )
    return {"accion": "insertado"}


def _validar_datos_generales(df, numero_procedimiento, ejercicio):
    if df is None or df.empty:
        raise ValueError("No se recibió información para importar.")
    if not normalizar_texto(numero_procedimiento):
        raise ValueError("El número o nombre del procedimiento es obligatorio.")
    if ejercicio is None:
        raise ValueError("El ejercicio del procedimiento es obligatorio.")


def _construir_descripcion(tipo_procedimiento, descripcion):
    tipo = normalizar_texto(tipo_procedimiento)
    detalle = normalizar_texto(descripcion)
    partes = []
    if tipo:
        partes.append(f"Tipo de procedimiento: {tipo}")
    if detalle:
        partes.append(detalle)
    return "\n".join(partes) if partes else None


__all__ = [
    "TABLA_DESTINO",
    "COLUMNAS_REQUERIDAS",
    "FASE_CARGA_1",
    "importar_universo_procedimiento",
    "procesar_fila_universo",
]
