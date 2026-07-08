"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

modules/carga_archivos.py

Módulo para lectura, limpieza y validación de archivos Excel.

Sprint 0.6 — Paso 006
Carga 1 — Universo del Procedimiento

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re
import unicodedata

import pandas as pd


# ==========================================================
# CONFIGURACIÓN DE CARGA 1
# ==========================================================

HOJA_PROPUESTA_ECONOMICA = "Propuesta Económica"

# Excel fila 7, pandas usa índice base 0
FILA_ENCABEZADOS = 6


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


# ==========================================================
# VALIDACIONES
# ==========================================================

def validar_columnas_requeridas(df):
    """
    Valida que el archivo contenga las columnas requeridas.
    """
    errores = []

    columnas_archivo = list(df.columns)

    for columna in COLUMNAS_CARGA_1.keys():
        if columna not in columnas_archivo:
            errores.append({
                "fila": None,
                "campo": columna,
                "error": f"No se encontró la columna requerida: {columna}"
            })

    return errores


def validar_filas_carga_1(df):
    """
    Valida fila por fila los datos de la Carga 1.

    En esta carga solo se validan:
    - clave
    - descripción

    La cantidad requerida no se toma del archivo actual.
    Se asignará como NULL para conservar compatibilidad futura.
    """
    errores = []

    for index, row in df.iterrows():
        fila_excel = index + FILA_ENCABEZADOS + 2

        clave = limpiar_clave(row.get("CLAVE"))
        descripcion = limpiar_texto(row.get("DESCRIPCION"))

        fila_vacia = (
            clave == ""
            and descripcion == ""
        )

        if fila_vacia:
            continue

        if clave == "":
            errores.append({
                "fila": fila_excel,
                "campo": "CLAVE",
                "error": "La clave es obligatoria."
            })

        if descripcion == "":
            errores.append({
                "fila": fila_excel,
                "campo": "DESCRIPCION",
                "error": "La descripción es obligatoria."
            })

    return errores


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
        "total_registros": int
    }
    """

    errores = []

    try:
        df = pd.read_excel(
            archivo_excel,
            sheet_name=HOJA_PROPUESTA_ECONOMICA,
            header=FILA_ENCABEZADOS
        )

    except ValueError:
        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": [{
                "fila": None,
                "campo": "HOJA",
                "error": (
                    "No se encontró la hoja requerida: "
                    f"{HOJA_PROPUESTA_ECONOMICA}"
                )
            }],
            "total_registros": 0
        }

    except Exception as e:
        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": [{
                "fila": None,
                "campo": "ARCHIVO",
                "error": f"No fue posible leer el archivo: {str(e)}"
            }],
            "total_registros": 0
        }

    df = normalizar_columnas(df)

    errores.extend(validar_columnas_requeridas(df))

    if errores:
        return {
            "valido": False,
            "datos": pd.DataFrame(),
            "errores": errores,
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

    df_limpio = df_limpio[
        ~(
            (df_limpio["clave"] == "")
            & (df_limpio["descripcion"] == "")
        )
    ]

    errores.extend(validar_filas_carga_1(df))

    if errores:
        return {
            "valido": False,
            "datos": df_limpio,
            "errores": errores,
            "total_registros": len(df_limpio)
        }

    df_limpio = df_limpio.drop_duplicates(
        subset=["clave"],
        keep="first"
    )

    df_limpio = df_limpio.reset_index(drop=True)

    return {
        "valido": True,
        "datos": df_limpio,
        "errores": [],
        "total_registros": len(df_limpio)
    }