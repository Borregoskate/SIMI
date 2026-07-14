"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

normalizacion_service.py

Servicio central de normalización de datos.

Este archivo funciona como fachada de la capa Service sobre los
normalizadores generales definidos en utils/normalizadores.py.

Toda carga debe normalizar los datos antes de:

1. Validar estructura y contenido.
2. Validar contra base de datos.
3. Insertar o actualizar información.

Este servicio NO consulta la base de datos.
Este servicio NO abre conexiones.
Este servicio NO ejecuta SQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re
import unicodedata

import pandas as pd

from utils.normalizadores import (
    normalizar_booleano,
    normalizar_clave,
    normalizar_dataframe,
    normalizar_decimal,
    normalizar_numero,
    normalizar_pais,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
    quitar_acentos,
)


def normalizar_nombre_columna(columna):
    """
    Normaliza el nombre de una columna para uso interno.

    Ejemplos:
        "RAZÓN SOCIAL"       -> "razon_social"
        "PRECIO UNITARIO"    -> "precio_unitario"
        "País de Origen"     -> "pais_de_origen"

    La normalización de nombres de columnas es distinta a la
    normalización de los valores contenidos en el DataFrame.
    """

    if columna is None:
        return ""

    texto = str(columna).strip()

    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)

    return texto.strip("_")


def normalizar_nombres_columnas(df):
    """
    Devuelve una copia del DataFrame con los nombres de sus columnas
    normalizados.

    No modifica el DataFrame original.
    """

    if df is None:
        return None

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Se esperaba un DataFrame para normalizar sus columnas."
        )

    df_normalizado = df.copy()

    df_normalizado.columns = [
        normalizar_nombre_columna(columna)
        for columna in df_normalizado.columns
    ]

    columnas_duplicadas = (
        df_normalizado.columns[
            df_normalizado.columns.duplicated()
        ].tolist()
    )

    if columnas_duplicadas:
        raise ValueError(
            "La normalización produjo nombres de columnas duplicados: "
            + ", ".join(sorted(set(columnas_duplicadas)))
        )

    return df_normalizado


def normalizar_dataframe_por_columnas(df, normalizadores):
    """
    Aplica una función normalizadora a cada columna configurada.

    Parámetros:
        df:
            DataFrame de origen.

        normalizadores:
            Diccionario con la forma:

            {
                "RFC": normalizar_rfc,
                "CLAVE": normalizar_clave,
                "PRECIO UNITARIO": normalizar_decimal,
            }

    Devuelve:
        Una copia normalizada del DataFrame.
    """

    if df is None:
        return None

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Se esperaba un DataFrame para normalizar sus datos."
        )

    if normalizadores is None:
        return df.copy()

    if not isinstance(normalizadores, dict):
        raise TypeError(
            "Los normalizadores deben proporcionarse en un diccionario."
        )

    return normalizar_dataframe(
        df=df,
        normalizadores=normalizadores,
    )


__all__ = [
    "quitar_acentos",
    "normalizar_texto",
    "normalizar_rfc",
    "normalizar_clave",
    "normalizar_razon_social",
    "normalizar_pais",
    "normalizar_numero",
    "normalizar_decimal",
    "normalizar_booleano",
    "normalizar_dataframe",
    "normalizar_nombre_columna",
    "normalizar_nombres_columnas",
    "normalizar_dataframe_por_columnas",
]