"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_universo_service.py

Servicio de prevalidación para la Carga 1:
Universo del Procedimiento.

Este servicio NO inserta datos en base de datos.
Solo valida estructura, contenido y duplicados del archivo Excel.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd


HOJA_UNIVERSO = "Propuesta Económica"


def leer_archivo_universo(archivo):
    """
    Lee el archivo Excel de universo del procedimiento.

    Estructura autorizada:
    - Hoja: Propuesta Económica
    - Encabezados: fila 7
    - Columnas relevantes:
        C = CLAVE
        D = DESCRIPCION
        H = CANTIDAD_REQUERIDA opcional
    """

    try:
        df = pd.read_excel(
            archivo,
            sheet_name=HOJA_UNIVERSO,
            header=6,
            usecols="C,D,H"
        )

        df.columns = [
            "CLAVE",
            "DESCRIPCION",
            "CANTIDAD_REQUERIDA"
        ]

        return df, None

    except ValueError:
        return None, f"No se encontró la hoja '{HOJA_UNIVERSO}' en el archivo."

    except Exception as error:
        return None, f"Error al leer el archivo: {error}"


def limpiar_dataframe_universo(df):
    """
    Limpia datos vacíos y normaliza columnas básicas.
    """

    df = df.copy()

    df = df.dropna(
        subset=["CLAVE", "DESCRIPCION"],
        how="all"
    )

    df["CLAVE"] = df["CLAVE"].astype(str).str.strip()
    df["DESCRIPCION"] = df["DESCRIPCION"].astype(str).str.strip()

    df["CANTIDAD_REQUERIDA"] = pd.to_numeric(
        df["CANTIDAD_REQUERIDA"],
        errors="coerce"
    )

    return df


def prevalidar_universo_procedimiento(archivo):
    """
    Prevalida el archivo de universo del procedimiento.

    Reglas actuales:
    - CLAVE es obligatoria.
    - DESCRIPCION es obligatoria.
    - CANTIDAD_REQUERIDA es opcional.
    - No debe haber claves duplicadas.
    """

    errores = []

    df, error_lectura = leer_archivo_universo(archivo)

    if error_lectura:
        return {
            "valido": False,
            "dataframe": None,
            "errores": [error_lectura],
            "resumen": {}
        }

    df = limpiar_dataframe_universo(df)

    if df.empty:
        errores.append("El archivo no contiene registros válidos para procesar.")

    claves_vistas = set()
    claves_duplicadas = set()

    for index, row in df.iterrows():
        fila_excel = index + 8

        clave = row.get("CLAVE")
        descripcion = row.get("DESCRIPCION")

        if not clave or clave.lower() == "nan":
            errores.append(f"Fila {fila_excel}: la clave es obligatoria.")

        if not descripcion or descripcion.lower() == "nan":
            errores.append(f"Fila {fila_excel}: la descripción es obligatoria.")

        if clave and clave.lower() != "nan":
            if clave in claves_vistas:
                claves_duplicadas.add(clave)
            else:
                claves_vistas.add(clave)

    for clave in claves_duplicadas:
        errores.append(f"La clave '{clave}' aparece duplicada dentro del archivo.")

    resumen = {
        "total_registros": len(df),
        "total_claves_unicas": df["CLAVE"].nunique() if not df.empty else 0,
        "total_duplicados": len(claves_duplicadas),
        "total_errores": len(errores),
    }

    return {
        "valido": len(errores) == 0,
        "dataframe": df,
        "errores": errores,
        "resumen": resumen
    }