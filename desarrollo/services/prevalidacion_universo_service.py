"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_universo_service.py

Servicio de prevalidación para la Carga 1:
Universo del Procedimiento.

Este servicio NO inserta datos en base de datos.
Solo valida estructura, contenido, duplicados y consistencia
contra base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd

from services.validacion_catalogos_service import (
    validar_claves_contra_catalogo,
    validar_procedimiento_existente
)


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

        if not clave or str(clave).lower() == "nan":
            errores.append(f"Fila {fila_excel}: la clave es obligatoria.")

        if not descripcion or str(descripcion).lower() == "nan":
            errores.append(f"Fila {fila_excel}: la descripción es obligatoria.")

        if clave and str(clave).lower() != "nan":
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


def prevalidar_universo_contra_bd(df, conn, numero_procedimiento):
    """
    Ejecuta la prevalidación del universo contra base de datos.

    Validaciones:
    - El procedimiento no debe existir previamente.
    - Las claves existentes deben coincidir con su descripción en catálogo.
    - Las claves nuevas se marcan para futura inserción.
    - Se agregan columnas ID_CLAVE y ES_NUEVA.

    Este proceso NO inserta datos.
    """

    errores = []

    validacion_procedimiento = validar_procedimiento_existente(
        conn=conn,
        numero_procedimiento=numero_procedimiento
    )

    if validacion_procedimiento["existe"]:
        errores.append(
            f"El procedimiento '{numero_procedimiento}' ya existe en base de datos."
        )

        return {
            "success": False,
            "df": df,
            "errores": errores,
            "resumen": {
                "total_registros": len(df),
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": len(errores)
            }
        }

    resultado_claves = validar_claves_contra_catalogo(
        df=df,
        conn=conn
    )

    errores.extend(resultado_claves["errores"])

    return {
        "success": len(errores) == 0,
        "df": resultado_claves["df"],
        "errores": errores,
        "resumen": resultado_claves["resumen"]
    }