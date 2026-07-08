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

import pandas as pd


# ==========================================================
# CONFIGURACIÓN DE CARGA 1
# ==========================================================

HOJA_PROPUESTA_ECONOMICA = "Propuesta Económica"
FILA_ENCABEZADOS = 6  # Excel fila 7, pandas usa índice base 0


COLUMNAS_CARGA_1 = {
    "CLAVE": "clave",
    "DESCRIPCION": "descripcion",
    "CANTIDAD REQUERIDA": "cantidad_requerida",
}


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def limpiar_texto(valor):
    """
    Limpia valores de texto provenientes del archivo Excel.
    """
    if pd.isna(valor):
        return ""

    return str(valor).strip().upper()


def limpiar_clave(valor):
    """
    Limpia y normaliza la clave.
    No transforma el formato de la clave, solo elimina espacios.
    """
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def limpiar_cantidad(valor):
    """
    Convierte la cantidad requerida a número.
    Si no se puede convertir, regresa None.
    """
    if pd.isna(valor):
        return None

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def normalizar_columnas(df):
    """
    Normaliza nombres de columnas para facilitar la lectura.
    """
    df = df.copy()

    df.columns = [
        str(col).strip().upper()
        for col in df.columns
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
    """
    errores = []

    for index, row in df.iterrows():
        fila_excel = index + FILA_ENCABEZADOS + 2

        clave = limpiar_clave(row.get("CLAVE"))
        descripcion = limpiar_texto(row.get("DESCRIPCION"))
        cantidad = limpiar_cantidad(row.get("CANTIDAD REQUERIDA"))

        fila_vacia = (
            clave == ""
            and descripcion == ""
            and cantidad is None
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

        if cantidad is None:
            errores.append({
                "fila": fila_excel,
                "campo": "CANTIDAD REQUERIDA",
                "error": "La cantidad requerida debe ser numérica."
            })
        elif cantidad <= 0:
            errores.append({
                "fila": fila_excel,
                "campo": "CANTIDAD REQUERIDA",
                "error": "La cantidad requerida debe ser mayor a cero."
            })

    return errores


# ==========================================================
# PROCESAMIENTO PRINCIPAL
# ==========================================================

def procesar_carga_1_universo_procedimiento(archivo_excel):
    """
    Procesa el archivo Excel correspondiente a la Carga 1.

    Carga 1 — Universo del Procedimiento

    Lee:
    - Hoja: Propuesta Económica
    - Encabezados: fila 7
    - Columnas requeridas:
        CLAVE
        DESCRIPCION
        CANTIDAD REQUERIDA

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
                "error": f"No se encontró la hoja requerida: {HOJA_PROPUESTA_ECONOMICA}"
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
    df["cantidad_requerida"] = df["CANTIDAD REQUERIDA"].apply(limpiar_cantidad)

    df_limpio = df[[
        "clave",
        "descripcion",
        "cantidad_requerida"
    ]].copy()

    df_limpio = df_limpio[
        ~(
            (df_limpio["clave"] == "")
            & (df_limpio["descripcion"] == "")
            & (df_limpio["cantidad_requerida"].isna())
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

    return {
        "valido": True,
        "datos": df_limpio,
        "errores": [],
        "total_registros": len(df_limpio)
    }