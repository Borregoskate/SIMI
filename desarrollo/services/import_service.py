"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_service.py

Funciones generales de apoyo para procesos de importación.

Responsabilidades:

1. Validar que un DataFrame tenga información.
2. Validar columnas requeridas.
3. Preparar nombres de columnas.
4. Mantener compatibilidad temporal con cargas existentes.

Este servicio NO consulta la base de datos.
Este servicio NO abre conexiones.
Este servicio NO ejecuta SQL.
Este servicio NO administra transacciones.

La normalización de valores se delega exclusivamente a:

    services.normalizacion_service

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

import pandas as pd

from services.normalizacion_service import (
    normalizar_clave,
    normalizar_nombre_columna,
    normalizar_nombres_columnas,
    normalizar_numero,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
)


def validar_dataframe(df):
    """
    Verifica que el objeto recibido sea un DataFrame válido.

    Lanza:
        TypeError:
            Cuando el objeto no es un DataFrame.

        ValueError:
            Cuando el DataFrame no contiene registros.
    """

    if df is None:
        raise ValueError(
            "No se recibió información para importar."
        )

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "La información recibida debe ser un DataFrame."
        )

    if df.empty:
        raise ValueError(
            "El archivo no contiene registros para importar."
        )

    return True


def validar_dataframe_no_vacio(df):
    """
    Alias compatible con las cargas existentes.

    Valida que el objeto sea un DataFrame y que contenga registros.
    """

    return validar_dataframe(df)


def validar_columnas_requeridas(df, columnas_requeridas):
    """
    Verifica que el DataFrame contenga todas las columnas obligatorias.

    La validación se realiza contra los nombres presentes en el
    DataFrame. El llamador debe definir previamente si trabajará con
    nombres originales o nombres normalizados.

    Parámetros:
        df:
            DataFrame que será validado.

        columnas_requeridas:
            Iterable con los nombres obligatorios.

    Lanza:
        ValueError:
            Cuando falta una o más columnas.
    """

    validar_dataframe(df)

    if columnas_requeridas is None:
        return True

    columnas_requeridas = list(columnas_requeridas)

    if not columnas_requeridas:
        return True

    columnas_disponibles = set(df.columns)

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in columnas_disponibles
    ]

    if columnas_faltantes:
        raise ValueError(
            "El archivo debe contener las columnas: "
            + ", ".join(str(columna) for columna in columnas_faltantes)
        )

    return True


def normalizar_dataframe(df):
    """
    Normaliza únicamente los nombres de las columnas.

    Esta función se conserva por compatibilidad con código anterior.

    No normaliza los valores de las filas. Para normalizar valores debe
    utilizarse services.normalizacion_service.
    """

    return normalizar_nombres_columnas(df)


def preparar_dataframe(df):
    """
    Valida el DataFrame y normaliza los nombres de sus columnas.

    No modifica el DataFrame original.
    """

    validar_dataframe(df)

    return normalizar_nombres_columnas(df)


def leer_excel(archivo, hoja=None, **kwargs):
    """
    Lee temporalmente un archivo Excel y normaliza los nombres de sus
    columnas.

    Esta función se mantiene por compatibilidad hasta homologar
    excel_service.py.

    Parámetros:
        archivo:
            Archivo o ruta compatible con pandas.read_excel.

        hoja:
            Nombre o índice de la hoja. Si es None, se utiliza la
            primera hoja.

        **kwargs:
            Parámetros adicionales enviados a pandas.read_excel.
    """

    if archivo is None:
        raise ValueError(
            "No se recibió un archivo Excel para leer."
        )

    if hoja is None:
        df = pd.read_excel(
            archivo,
            **kwargs,
        )
    else:
        df = pd.read_excel(
            archivo,
            sheet_name=hoja,
            **kwargs,
        )

    return preparar_dataframe(df)


# ==========================================================
# COMPATIBILIDAD TEMPORAL
# ==========================================================
#
# Las siguientes funciones conservan los nombres utilizados por
# implementaciones anteriores.
#
# No contienen reglas propias. Todas delegan al servicio oficial de
# normalización.
#
# Serán retiradas cuando todos los Services hayan sido homologados.
# ==========================================================


def limpiar_texto(valor):
    """
    Compatibilidad temporal con implementaciones anteriores.
    """

    return normalizar_texto(valor)


def limpiar_rfc(valor):
    """
    Compatibilidad temporal con implementaciones anteriores.
    """

    return normalizar_rfc(valor)


def limpiar_clave(valor):
    """
    Compatibilidad temporal con implementaciones anteriores.
    """

    return normalizar_clave(valor)


def limpiar_razon_social(valor):
    """
    Compatibilidad temporal con implementaciones anteriores.
    """

    return normalizar_razon_social(valor)


def limpiar_numero(valor):
    """
    Compatibilidad temporal con implementaciones anteriores.
    """

    return normalizar_numero(valor)


__all__ = [
    "validar_dataframe",
    "validar_dataframe_no_vacio",
    "validar_columnas_requeridas",
    "normalizar_nombre_columna",
    "normalizar_dataframe",
    "preparar_dataframe",
    "leer_excel",
    "limpiar_texto",
    "limpiar_rfc",
    "limpiar_clave",
    "limpiar_razon_social",
    "limpiar_numero",
]