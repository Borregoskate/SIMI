"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_universo_service.py

Servicio de prevalidación para la Carga 1.

Autor: Jorge Saavedra
Versión: 2.1.0
==============================================================
"""

import pandas as pd

from services.database_service import database_transaction
from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_texto,
)
from services.validacion_catalogos_service import (
    validar_claves_contra_catalogo,
    validar_procedimiento_existente,
)
from services.validacion_service import NIVEL_ERROR, validar_carga_1_universo

HOJA_UNIVERSO = "Propuesta Económica"
COLUMNAS_UNIVERSO = ["CLAVE", "DESCRIPCION", "CANTIDAD_REQUERIDA"]


def leer_archivo_universo(archivo):
    try:
        if archivo is None:
            return None, "No se recibió un archivo Excel."
        if hasattr(archivo, "seek"):
            archivo.seek(0)

        df = pd.read_excel(
            archivo,
            sheet_name=HOJA_UNIVERSO,
            header=6,
            usecols="C,D,H",
        )
        if len(df.columns) != len(COLUMNAS_UNIVERSO):
            return None, "No fue posible identificar las columnas esperadas."
        df.columns = COLUMNAS_UNIVERSO
        return df, None
    except ValueError:
        return None, f"No se encontró la hoja '{HOJA_UNIVERSO}' en el archivo."
    except Exception as error:
        return None, f"Error al leer el archivo: {error}"


def normalizar_dataframe_universo(df):
    if df is None:
        return None
    resultado = df.copy()
    resultado["CLAVE"] = resultado["CLAVE"].apply(normalizar_clave)
    resultado["DESCRIPCION"] = resultado["DESCRIPCION"].apply(normalizar_texto)
    resultado["CANTIDAD_REQUERIDA"] = resultado["CANTIDAD_REQUERIDA"].apply(
        normalizar_decimal
    )
    return resultado


def eliminar_filas_vacias_universo(df):
    if df is None:
        return None
    mascara = ~(
        df["CLAVE"].isna()
        & df["DESCRIPCION"].isna()
        & df["CANTIDAD_REQUERIDA"].isna()
    )
    return df[mascara].copy()


def convertir_mensajes_a_errores(mensajes):
    errores = []
    for mensaje in mensajes or []:
        if mensaje.get("nivel") != NIVEL_ERROR:
            continue
        fila = mensaje.get("fila")
        texto = mensaje.get("mensaje", "Error de validación.")
        errores.append(f"Fila {fila}: {texto}" if fila is not None else texto)
    return errores


def prevalidar_universo_procedimiento(archivo):
    df_original, error_lectura = leer_archivo_universo(archivo)
    if error_lectura:
        return {
            "valido": False,
            "dataframe": None,
            "errores": [error_lectura],
            "resumen": {
                "total_registros": 0,
                "total_claves_unicas": 0,
                "total_duplicados": 0,
                "total_errores": 1,
            },
        }

    df_preparado = eliminar_filas_vacias_universo(
        normalizar_dataframe_universo(df_original)
    )
    if df_preparado is None or df_preparado.empty:
        return {
            "valido": False,
            "dataframe": df_preparado,
            "errores": ["El archivo no contiene registros válidos para procesar."],
            "resumen": {
                "total_registros": 0,
                "total_claves_unicas": 0,
                "total_duplicados": 0,
                "total_errores": 1,
            },
        }

    validacion = validar_carga_1_universo(df=df_preparado, fila_inicio_excel=8)
    resumen_general = validacion["resumen"]
    return {
        "valido": validacion["valido"],
        "dataframe": validacion["datos_validados"],
        "errores": convertir_mensajes_a_errores(validacion["mensajes"]),
        "resumen": {
            "total_registros": resumen_general.get("total_registros", 0),
            "total_claves_unicas": resumen_general.get("claves_unicas", 0),
            "total_duplicados": resumen_general.get("duplicados_clave", 0),
            "total_errores": resumen_general.get("errores", 0),
        },
    }


def prevalidar_universo_contra_bd(df, numero_procedimiento):
    """Valida contra BD sin recibir una conexión desde el módulo visual."""

    errores = []
    numero_normalizado = normalizar_texto(numero_procedimiento)
    if not numero_normalizado:
        return _crear_resultado_bd(
            df,
            ["El número o nombre del procedimiento es obligatorio."],
        )

    try:
        with database_transaction() as conn:
            validacion_procedimiento = validar_procedimiento_existente(
                numero_procedimiento=numero_normalizado,
                conn=conn,
            )
            if validacion_procedimiento["existe"]:
                return _crear_resultado_bd(
                    df,
                    [
                        f"El procedimiento '{numero_normalizado}' "
                        "ya existe en base de datos."
                    ],
                )

            resultado_claves = validar_claves_contra_catalogo(df=df, conn=conn)

        errores.extend(resultado_claves.get("errores", []))
        resumen = resultado_claves.get("resumen", {}).copy()
        resumen["errores"] = len(errores)
        return {
            "success": not errores,
            "df": resultado_claves.get("df"),
            "errores": errores,
            "resumen": resumen,
        }
    except Exception as error:
        return _crear_resultado_bd(df, [str(error)])


def _crear_resultado_bd(df, errores):
    return {
        "success": False,
        "df": df,
        "errores": errores,
        "resumen": {
            "total_registros": 0 if df is None else len(df),
            "claves_existentes": 0,
            "claves_nuevas": 0,
            "errores": len(errores),
        },
    }


limpiar_dataframe_universo = normalizar_dataframe_universo

__all__ = [
    "HOJA_UNIVERSO",
    "COLUMNAS_UNIVERSO",
    "leer_archivo_universo",
    "normalizar_dataframe_universo",
    "limpiar_dataframe_universo",
    "eliminar_filas_vacias_universo",
    "prevalidar_universo_procedimiento",
    "prevalidar_universo_contra_bd",
]
