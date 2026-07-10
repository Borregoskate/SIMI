"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_propuestas_service.py

Servicio de prevalidación para la Carga 2:
Propuestas Iniciales.

Este servicio NO inserta datos en base de datos.
Lee, normaliza y valida el archivo antes de la importación.

Formato oficial de Carga 2:
- Una sola hoja.
- Encabezados en la primera fila.
- Una fila representa una propuesta por proveedor y clave.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import pandas as pd

from utils.normalizadores import (
    normalizar_dataframe,
    normalizar_rfc,
    normalizar_razon_social,
    normalizar_clave,
    normalizar_texto,
    normalizar_pais,
    normalizar_decimal
)


# ==========================================================
# COLUMNAS OFICIALES DEL ARCHIVO
# ==========================================================

COLUMNAS_REQUERIDAS_PROPUESTAS = {
    "RFC": "RFC",
    "RAZON SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "DESCRIPCION": "DESCRIPCION",
    "CANTIDAD OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS DE ORIGEN": "PAIS_ORIGEN",
    "PRECIO UNITARIO": "PRECIO_UNITARIO",
}


# ==========================================================
# NORMALIZADORES POR COLUMNA
# ==========================================================

NORMALIZADORES_PROPUESTAS = {
    "RFC": normalizar_rfc,
    "RAZON SOCIAL": normalizar_razon_social,
    "CLAVE": normalizar_clave,
    "DESCRIPCION": normalizar_texto,
    "CANTIDAD OFERTADA": normalizar_decimal,
    "PAIS DE ORIGEN": normalizar_pais,
    "PRECIO UNITARIO": normalizar_decimal,
}


# ==========================================================
# LECTURA DEL ARCHIVO
# ==========================================================

def leer_archivo_propuestas(archivo):
    """
    Lee el archivo Excel de propuestas iniciales.

    Reglas del formato:
    - El archivo contiene una sola hoja.
    - Los encabezados están en la primera fila.
    """

    archivo.seek(0)

    return pd.read_excel(
        archivo,
        sheet_name=0,
        header=0
    )


# ==========================================================
# NORMALIZACIÓN
# ==========================================================

def normalizar_archivo_propuestas(df):
    """
    Normaliza los datos antes de ejecutar las validaciones.
    """

    return normalizar_dataframe(
        df=df,
        normalizadores=NORMALIZADORES_PROPUESTAS
    )


# ==========================================================
# VALIDACIÓN DE COLUMNAS
# ==========================================================

def validar_columnas_requeridas_propuestas(df):
    """
    Valida que estén presentes todas las columnas oficiales.
    """

    errores = []

    columnas_archivo = {
        str(columna).strip().upper()
        for columna in df.columns
    }

    for columna in COLUMNAS_REQUERIDAS_PROPUESTAS:
        if columna not in columnas_archivo:
            errores.append({
                "fila": None,
                "error": f"Falta la columna requerida: {columna}"
            })

    return errores


# ==========================================================
# PREPARACIÓN DEL DATAFRAME
# ==========================================================

def preparar_dataframe_propuestas(df):
    """
    Conserva las columnas oficiales y las renombra para uso
    interno dentro de los servicios de SIMI.
    """

    df_trabajo = df[
        list(COLUMNAS_REQUERIDAS_PROPUESTAS.keys())
    ].copy()

    df_trabajo = df_trabajo.rename(
        columns=COLUMNAS_REQUERIDAS_PROPUESTAS
    )

    # Elimina filas completamente vacías.
    df_trabajo = df_trabajo.dropna(how="all")

    return df_trabajo


# ==========================================================
# VALIDACIÓN DEL CONTENIDO
# ==========================================================

def validar_contenido_propuestas(df):
    """
    Valida campos obligatorios y reglas numéricas.
    """

    errores = []

    for index, fila in df.iterrows():
        # Encabezados en fila 1, por lo que el primer registro
        # corresponde a la fila 2 de Excel.
        numero_fila_excel = index + 2

        rfc = fila.get("RFC")
        razon_social = fila.get("RAZON_SOCIAL")
        clave = fila.get("CLAVE")
        descripcion = fila.get("DESCRIPCION")
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

        if not descripcion:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La descripción es obligatoria."
            })

        if cantidad_ofertada is None:
            errores.append({
                "fila": numero_fila_excel,
                "error": "La cantidad ofertada es obligatoria."
            })
        elif cantidad_ofertada <= 0:
            errores.append({
                "fila": numero_fila_excel,
                "error": (
                    "La cantidad ofertada debe ser mayor a cero."
                )
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
                "error": (
                    "El precio unitario debe ser mayor a cero."
                )
            })

    return errores


# ==========================================================
# VALIDACIÓN DE DUPLICADOS
# ==========================================================

def validar_duplicados_propuestas(df):
    """
    Valida que no exista más de una propuesta para el mismo
    RFC y la misma clave dentro del archivo.
    """

    errores = []

    filas_validas = df[
        df["RFC"].notna()
        & df["CLAVE"].notna()
    ]

    duplicados = filas_validas[
        filas_validas.duplicated(
            subset=["RFC", "CLAVE"],
            keep=False
        )
    ]

    for index, fila in duplicados.iterrows():
        numero_fila_excel = index + 2

        errores.append({
            "fila": numero_fila_excel,
            "error": (
                f"Propuesta duplicada para el RFC "
                f"{fila.get('RFC')} y la clave "
                f"{fila.get('CLAVE')}."
            )
        })

    return errores


# ==========================================================
# PREVALIDACIÓN GENERAL
# ==========================================================

def prevalidar_archivo_propuestas(archivo):
    """
    Ejecuta la prevalidación completa de Carga 2.

    Flujo:
    1. Leer la única hoja.
    2. Usar encabezados de la primera fila.
    3. Estandarizar nombres de columnas.
    4. Validar columnas requeridas.
    5. Normalizar los datos.
    6. Preparar el DataFrame.
    7. Validar contenido.
    8. Validar duplicados.
    """

    try:
        df_original = leer_archivo_propuestas(archivo)
    except Exception as error:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": (
                    "No fue posible leer el archivo Excel: "
                    f"{error}"
                )
            }],
            "df": None
        }

    # Normaliza los nombres de columnas.
    df_original.columns = [
        str(columna).strip().upper()
        for columna in df_original.columns
    ]

    errores_columnas = (
        validar_columnas_requeridas_propuestas(df_original)
    )

    if errores_columnas:
        return {
            "valido": False,
            "errores": errores_columnas,
            "df": None
        }

    df_normalizado = normalizar_archivo_propuestas(
        df_original
    )

    df_preparado = preparar_dataframe_propuestas(
        df_normalizado
    )

    errores = []

    errores.extend(
        validar_contenido_propuestas(df_preparado)
    )

    errores.extend(
        validar_duplicados_propuestas(df_preparado)
    )

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "df": df_preparado
    }
