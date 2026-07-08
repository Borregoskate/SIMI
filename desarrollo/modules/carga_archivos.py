"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

modules/carga_archivos.py

Módulo para lectura, limpieza y preparación de archivos Excel.

Sprint 0.6 — Paso 006
Carga 1 — Universo del Procedimiento

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re
import unicodedata

import pandas as pd

from services.validacion_service import (
    validar_columnas_requeridas,
    validar_carga_1_universo,
)


# ==========================================================
# CONFIGURACIÓN DE CARGA 1
# ==========================================================

HOJA_PROPUESTA_ECONOMICA = "Propuesta Económica"

# Excel fila 7, pandas usa índice base 0
FILA_ENCABEZADOS = 6

# Primer renglón real de datos en Excel
FILA_INICIO_DATOS_EXCEL = 8


COLUMNAS_CARGA_1 = {
    "CLAVE": "clave",
    "DESCRIPCION": "descripcion",
}


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def normalizar_texto(valor):
    """
    Normaliza texto eliminando acentos, espacios innecesarios
    y convirtiendo a mayúsculas.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")

    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def limpiar_texto(valor):
    """
    Limpia valores de texto provenientes del archivo Excel.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto.upper()


def limpiar_clave(valor):
    """
    Limpia la clave sin modificar su formato original.
    """
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def normalizar_columnas(df):
    """
    Normaliza nombres de columnas eliminando acentos,
    espacios dobles, saltos de línea y caracteres especiales.
    """
    df = df.copy()

    df.columns = [
        normalizar_texto(columna)
        for columna in df.columns
    ]

    return df


def crear_error_lectura(campo, mensaje):
    """
    Crea un error estándar para errores de lectura del archivo.
    """
    return {
        "nivel": "ERROR",
        "fila": None,
        "campo": campo,
        "valor": None,
        "mensaje": mensaje
    }


# ==========================================================
# PROCESAMIENTO PRINCIPAL
# ==========================================================

def procesar_carga_1_universo_procedimiento(archivo_excel):
    """
    Procesa el archivo Excel correspondiente a la Carga 1.

    Carga 1 — Universo del Procedimiento.

    Lee:
    - Hoja: Propuesta Económica
    - Encabezados: fila 7
    - Columnas requeridas:
        CLAVE
        DESCRIPCION

    No procesa cantidad requerida porque el archivo actual
    no contiene ese dato de forma confiable.

    Retorna:
    {
        "valido": bool,
        "datos": DataFrame,
        "errores": list,
        "mensajes": list,
        "resumen": dict,
        "total_registros": int
    }
    """

    try:
        df = pd.read_excel(
            archivo_excel,
            sheet_name=HOJA_PROPUESTA_ECONOMICA,
            header=FILA_ENCABEZADOS
        )

    except ValueError:
        mensaje = crear_error_lectura(
            campo="HOJA",
            mensaje=(
                "No se encontró la hoja requerida: "
                f"{HOJA_PROPUESTA_ECONOMICA}"
            )
        )

        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": [mensaje],
            "mensajes": [mensaje],
            "resumen": {
                "total_registros": 0,
                "errores": 1,
                "advertencias": 0,
                "informativos": 0,
                "valido": False
            },
            "total_registros": 0
        }

    except Exception as e:
        mensaje = crear_error_lectura(
            campo="ARCHIVO",
            mensaje=f"No fue posible leer el archivo: {str(e)}"
        )

        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": [mensaje],
            "mensajes": [mensaje],
            "resumen": {
                "total_registros": 0,
                "errores": 1,
                "advertencias": 0,
                "informativos": 0,
                "valido": False
            },
            "total_registros": 0
        }

    df = normalizar_columnas(df)

    mensajes_columnas = validar_columnas_requeridas(
        df=df,
        columnas_requeridas=list(COLUMNAS_CARGA_1.keys())
    )

    if mensajes_columnas:
        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": mensajes_columnas,
            "mensajes": mensajes_columnas,
            "resumen": {
                "total_registros": 0,
                "errores": len(mensajes_columnas),
                "advertencias": 0,
                "informativos": 0,
                "valido": False
            },
            "total_registros": 0
        }

    df = df[list(COLUMNAS_CARGA_1.keys())].copy()

    df["clave"] = df["CLAVE"].apply(limpiar_clave)
    df["descripcion"] = df["DESCRIPCION"].apply(limpiar_texto)

    # La cantidad requerida se conserva en el modelo,
    # pero en esta carga queda como NULL.
    df["cantidad_requerida"] = None

    df_limpio = df[[
        "clave",
        "descripcion",
        "cantidad_requerida"
    ]].copy()

    resultado_validacion = validar_carga_1_universo(
        df=df_limpio,
        fila_inicio_excel=FILA_INICIO_DATOS_EXCEL
    )

    datos_validados = resultado_validacion["datos_validados"]
    mensajes = resultado_validacion["mensajes"]
    resumen = resultado_validacion["resumen"]

    # Para evitar insertar duplicados después.
    # Si hay duplicados, se reportan como advertencia, pero aquí
    # conservamos el primer registro para la vista previa.
    datos_validados = datos_validados.drop_duplicates(
        subset=["clave"],
        keep="first"
    ).reset_index(drop=True)

    resumen["total_registros"] = len(datos_validados)

    errores = [
        mensaje for mensaje in mensajes
        if mensaje.get("nivel") == "ERROR"
    ]

    return {
        "valido": resultado_validacion["valido"],
        "datos": datos_validados,
        "errores": errores,
        "mensajes": mensajes,
        "resumen": resumen,
        "total_registros": len(datos_validados)
    }