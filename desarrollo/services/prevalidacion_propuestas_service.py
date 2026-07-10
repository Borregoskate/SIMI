"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_propuestas_service.py

Servicio de prevalidación para la Carga 2:
Propuestas Iniciales.

Este servicio NO inserta datos en base de datos.
Solo normaliza, valida estructura, contenido y duplicados
del archivo Excel.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd

from utils.normalizadores import (
    normalizar_dataframe,
    normalizar_rfc,
    normalizar_razon_social,
    normalizar_clave,
    normalizar_pais,
    normalizar_decimal
)


COLUMNAS_REQUERIDAS_PROPUESTAS = {
    "RFC": "RFC",
    "RAZON SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "DESCRIPCION": "DESCRIPCION",
    "CANTIDAD OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS DE ORIGEN": "PAIS_ORIGEN",
    "PRECIO UNITARIO": "PRECIO_UNITARIO",
}


NORMALIZADORES_PROPUESTAS = {
    "RFC": normalizar_rfc,
    "RAZON SOCIAL": normalizar_razon_social,
    "CLAVE": normalizar_clave,
    "PAIS DE ORIGEN": normalizar_pais,
    "CANTIDAD OFERTADA": normalizar_decimal,
    "PRECIO UNITARIO": normalizar_decimal,
}


def leer_archivo_propuestas(archivo):
    """
    Lee el archivo Excel de propuestas iniciales.

    Se asume la misma estructura base:
    hoja 'Propuesta Económica' con encabezados en fila 7.
    """

    return pd.read_excel(
        archivo,
        sheet_name="Propuesta Económica",
        header=6
    )


def normalizar_archivo_propuestas(df):
    """
    Normaliza las columnas relevantes antes de validar.
    """

    return normalizar_dataframe(
        df=df,
        normalizadores=NORMALIZADORES_PROPUESTAS
    )


def validar_columnas_requeridas_propuestas(df):
    """
    Valida que el archivo contenga las columnas requeridas.
    """

    columnas_archivo = list(df.columns)
    errores = []

    for columna in COLUMNAS_REQUERIDAS_PROPUESTAS.keys():
        if columna not in columnas_archivo:
            errores.append({
                "fila": None,
                "error": f"Falta la columna requerida: {columna}"
            })

    return errores


def preparar_dataframe_propuestas(df):
    """
    Conserva y renombra únicamente las columnas necesarias.
    """

    df_trabajo = df[list(COLUMNAS_REQUERIDAS_PROPUESTAS.keys())].copy()
    df_trabajo = df_trabajo.rename(
        columns=COLUMNAS_REQUERIDAS_PROPUESTAS
    )

    return df_trabajo


def validar_contenido_propuestas(df):
    """
    Valida contenido obligatorio y reglas básicas de negocio.
    """

    errores = []

    for index, fila in df.iterrows():
        numero_fila_excel = index + 8

        rfc = fila.get("RFC")
        razon_social = fila.get("RAZON_SOCIAL")
        clave = fila.get("CLAVE")
        cantidad_ofertada = fila.get("CANTIDAD_OFERTADA")
        pais_origen = fila.get("PAIS_ORIGEN")
        precio_unitario = fila.get("PRECIO_UNITARIO")

        if not rfc:
            errores.append({
                "fila": numero_fila_excel,
                "error": "El RFC es obligatorio."
            })

        if not razon_social:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La razón social es obligatoria."
            })

        if not clave:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La clave es obligatoria."
            })

        if cantidad_ofertada is None:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La cantidad ofertada es obligatoria."
            })
        elif cantidad_ofertada <= 0:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La cantidad ofertada debe ser mayor a cero."
            })

        if not pais_origen:
            errores.append({
                "fila": numero_fila_excel,
                "error": "El país de origen es obligatorio."
            })

        if precio_unitario is None:
            errores.append({
                "fila": numero_fila_excel,
                "error": "El precio unitario es obligatorio."
            })
        elif precio_unitario <= 0:
            errores.append({
                "fila": numero_fila_excel,
                "error": "El precio unitario debe ser mayor a cero."
            })

    return errores


def validar_duplicados_propuestas(df):
    """
    Valida duplicados dentro del archivo.

    No debe existir más de una propuesta inicial para
    el mismo RFC y la misma clave dentro del mismo archivo.
    """

    errores = []

    duplicados = df[df.duplicated(
        subset=["RFC", "CLAVE"],
        keep=False
    )]

    for index, fila in duplicados.iterrows():
        numero_fila_excel = index + 8

        errores.append({
            "fila": numero_fila_excel,
            "error": (
                f"Propuesta duplicada en el archivo para RFC {fila.get('RFC')} "
                f"y clave {fila.get('CLAVE')}."
            )
        })

    return errores


def prevalidar_archivo_propuestas(archivo):
    """
    Ejecuta la prevalidación completa del archivo de propuestas.

    Flujo oficial:
    1. Leer Excel
    2. Validar columnas originales
    3. Normalizar datos
    4. Preparar DataFrame
    5. Validar contenido
    6. Validar duplicados
    """

    df_original = leer_archivo_propuestas(archivo)

    errores = []

    errores_columnas = validar_columnas_requeridas_propuestas(df_original)

    if errores_columnas:
        return {
            "valido": False,
            "errores": errores_columnas,
            "df": None
        }

    df_normalizado = normalizar_archivo_propuestas(df_original)
    df_preparado = preparar_dataframe_propuestas(df_normalizado)

    errores.extend(
        validar_contenido_propuestas(df_preparado)
    )

    errores.extend(
        validar_duplicados_propuestas(df_preparado)
    )

    if errores:
        return {
            "valido": False,
            "errores": errores,
            "df": df_preparado
        }

    return {
        "valido": True,
        "errores": [],
        "df": df_preparado
    }