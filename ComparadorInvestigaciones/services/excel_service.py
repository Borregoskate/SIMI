"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
services/excel_service.py

Descripción:
Servicio encargado de leer, validar y preparar archivos
de investigaciones de mercado homologadas.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from utils.helpers import (
    validar_columnas,
    obtener_errores_dataframe,
    preparar_dataframe_base,
    agregar_investigacion,
    agregar_nombre_archivo,
    extraer_numero_investigacion,
    limpiar_texto,
    unificar_proveedores_por_rfc,
)


# ==========================================================
# LECTURA DE ARCHIVOS
# ==========================================================

def leer_archivo(file: Any) -> pd.DataFrame:
    """
    Lee un archivo Excel o CSV.

    SIMI asume que los archivos ya vienen homologados con
    las columnas oficiales del proyecto.
    """

    nombre = file.name.lower()

    if nombre.endswith(".csv"):
        return pd.read_csv(file, dtype=str)

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(file, dtype=str)

    raise ValueError(
        "Formato no soportado. Usa archivos .xlsx, .xls o .csv"
    )


# ==========================================================
# PREPARACIÓN DE ARCHIVO INDIVIDUAL
# ==========================================================

def procesar_archivo(file: Any) -> dict:
    """
    Procesa una investigación individual.

    Devuelve un diccionario con:
    - valido
    - archivo
    - investigacion
    - registros
    - df
    - errores
    """

    resultado = {
        "valido": False,
        "archivo": file.name,
        "investigacion": "",
        "registros": 0,
        "df": pd.DataFrame(),
        "errores": [],
    }

    try:
        df = leer_archivo(file)

        errores = obtener_errores_dataframe(df)

        if errores:
            resultado["errores"] = errores
            return resultado

        nombre_archivo = file.name.replace(".xlsx", "").replace(".xls", "").replace(".csv", "")
        investigacion = extraer_numero_investigacion(nombre_archivo)

        if investigacion == "":
            investigacion = limpiar_texto(nombre_archivo)

        df = preparar_dataframe_base(df)
        df = agregar_investigacion(df, investigacion)
        df = agregar_nombre_archivo(df, nombre_archivo)

        resultado["valido"] = True
        resultado["investigacion"] = investigacion
        resultado["registros"] = len(df)
        resultado["df"] = df

        return resultado

    except Exception as error:
        resultado["errores"] = [str(error)]
        return resultado


# ==========================================================
# PROCESAMIENTO DE MÚLTIPLES ARCHIVOS
# ==========================================================

def procesar_archivos(files: list[Any]) -> dict:
    """
    Procesa múltiples archivos de investigaciones.

    Devuelve:
    - df_consolidado
    - archivos_validos
    - archivos_invalidos
    - total_registros
    """

    dataframes = []
    archivos_validos = []
    archivos_invalidos = []

    for file in files:
        resultado = procesar_archivo(file)

        if resultado["valido"]:
            dataframes.append(resultado["df"])
            archivos_validos.append(resultado)
        else:
            archivos_invalidos.append(resultado)

    if dataframes:
        df_consolidado = pd.concat(
            dataframes,
            ignore_index=True
        )

        df_consolidado = unificar_proveedores_por_rfc(
            df_consolidado
        )

    else:
        df_consolidado = pd.DataFrame()

    return {
        "df_consolidado": df_consolidado,
        "archivos_validos": archivos_validos,
        "archivos_invalidos": archivos_invalidos,
        "total_registros": len(df_consolidado),
    }


# ==========================================================
# VALIDACIÓN RÁPIDA
# ==========================================================

def archivo_es_valido(file: Any) -> bool:
    """
    Valida rápidamente si un archivo cumple la estructura.
    """

    try:
        df = leer_archivo(file)

        valido, _ = validar_columnas(df)

        return valido

    except Exception:
        return False