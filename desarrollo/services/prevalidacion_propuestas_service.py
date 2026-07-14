"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_propuestas_service.py

Servicio de prevalidación para la Carga 2:
Propuestas Iniciales.

Flujo obligatorio:

1. Leer archivo.
2. Estandarizar nombres de columnas.
3. Validar estructura.
4. Preparar columnas internas.
5. Normalizar valores.
6. Eliminar filas completamente vacías.
7. Validar contenido.
8. Validar duplicados.
9. Entregar datos normalizados a importación.

Este servicio NO consulta ni modifica la base de datos.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

import pandas as pd

from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_nombre_columna,
    normalizar_pais,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
)
from services.validacion_service import (
    NIVEL_ERROR,
    esta_vacio,
    validar_campos_obligatorios,
    validar_duplicados,
    validar_numero_positivo,
)


COLUMNAS_REQUERIDAS_PROPUESTAS = {
    "rfc": "RFC",
    "razon_social": "RAZON_SOCIAL",
    "clave": "CLAVE",
    "descripcion": "DESCRIPCION",
    "cantidad_ofertada": "CANTIDAD_OFERTADA",
    "pais_de_origen": "PAIS_ORIGEN",
    "precio_unitario": "PRECIO_UNITARIO",
}


NORMALIZADORES_PROPUESTAS = {
    "RFC": normalizar_rfc,
    "RAZON_SOCIAL": normalizar_razon_social,
    "CLAVE": normalizar_clave,
    "DESCRIPCION": normalizar_texto,
    "CANTIDAD_OFERTADA": normalizar_decimal,
    "PAIS_ORIGEN": normalizar_pais,
    "PRECIO_UNITARIO": normalizar_decimal,
}


CAMPOS_OBLIGATORIOS_PROPUESTAS = [
    "RFC",
    "RAZON_SOCIAL",
    "CLAVE",
    "DESCRIPCION",
    "CANTIDAD_OFERTADA",
    "PAIS_ORIGEN",
    "PRECIO_UNITARIO",
]


def leer_archivo_propuestas(archivo):
    """
    Lee la primera hoja del archivo de propuestas.
    """

    if archivo is None:
        raise ValueError(
            "No se recibió un archivo Excel."
        )

    if hasattr(archivo, "seek"):
        archivo.seek(0)

    return pd.read_excel(
        archivo,
        sheet_name=0,
        header=0,
    )


def estandarizar_columnas_propuestas(df):
    """
    Estandariza los nombres originales de las columnas.
    """

    if df is None:
        return None

    df_estandarizado = df.copy()

    df_estandarizado.columns = [
        normalizar_nombre_columna(columna)
        for columna in df_estandarizado.columns
    ]

    return df_estandarizado


def validar_columnas_requeridas_propuestas(df):
    """
    Valida la estructura oficial de Carga 2.
    """

    errores = []

    if df is None:
        return [
            {
                "fila": None,
                "error": (
                    "No se recibió información para validar."
                ),
            }
        ]

    columnas_archivo = set(df.columns)

    for columna in COLUMNAS_REQUERIDAS_PROPUESTAS:
        if columna not in columnas_archivo:
            errores.append(
                {
                    "fila": None,
                    "error": (
                        "Falta la columna requerida: "
                        f"{columna}"
                    ),
                }
            )

    return errores


def preparar_dataframe_propuestas(df):
    """
    Selecciona y renombra las columnas oficiales.
    """

    columnas_origen = list(
        COLUMNAS_REQUERIDAS_PROPUESTAS.keys()
    )

    df_trabajo = df[columnas_origen].copy()

    df_trabajo = df_trabajo.rename(
        columns=COLUMNAS_REQUERIDAS_PROPUESTAS
    )

    return df_trabajo


def normalizar_archivo_propuestas(df):
    """
    Normaliza todos los valores antes de validar contenido.
    """

    df_normalizado = df.copy()

    for columna, normalizador in (
        NORMALIZADORES_PROPUESTAS.items()
    ):
        if columna in df_normalizado.columns:
            df_normalizado[columna] = (
                df_normalizado[columna]
                .apply(normalizador)
            )

    return df_normalizado


def eliminar_filas_vacias_propuestas(df):
    """
    Elimina filas completamente vacías después de normalizar.
    """

    if df is None:
        return None
    
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
        "Se esperaba un DataFrame para eliminar filas vacías."
        )

    if df.empty:
        return df.copy()

    mascara_con_datos = df.apply(
        lambda fila: any(
            not esta_vacio(valor)
            for valor in fila
        ),
        axis=1,
    )

    return df[mascara_con_datos].copy()


def convertir_mensajes_a_errores(mensajes):
    """
    Convierte mensajes estándar al formato actual de la UI.
    """

    errores = []

    for mensaje in mensajes or []:
        if mensaje.get("nivel") != NIVEL_ERROR:
            continue

        errores.append(
            {
                "fila": mensaje.get("fila"),
                "error": mensaje.get("mensaje"),
            }
        )

    return errores


def validar_contenido_propuestas(df):
    """
    Valida campos obligatorios y valores numéricos.
    """

    mensajes = []

    mensajes.extend(
        validar_campos_obligatorios(
            df=df,
            campos_obligatorios=(
                CAMPOS_OBLIGATORIOS_PROPUESTAS
            ),
            fila_inicio_excel=2,
        )
    )

    mensajes.extend(
        validar_numero_positivo(
            df=df,
            campo="CANTIDAD_OFERTADA",
            fila_inicio_excel=2,
            obligatorio=False,
        )
    )

    mensajes.extend(
        validar_numero_positivo(
            df=df,
            campo="PRECIO_UNITARIO",
            fila_inicio_excel=2,
            obligatorio=False,
        )
    )

    return convertir_mensajes_a_errores(
        mensajes
    )


def validar_duplicados_propuestas(df):
    """
    No permite más de una propuesta para el mismo RFC y CLAVE
    dentro del archivo.
    """

    mensajes = validar_duplicados(
        df=df,
        campos=[
            "RFC",
            "CLAVE",
        ],
        fila_inicio_excel=2,
        nivel=NIVEL_ERROR,
        mensaje=(
            "Existe más de una propuesta para el mismo "
            "RFC y la misma clave."
        ),
    )

    return convertir_mensajes_a_errores(
        mensajes
    )


def prevalidar_archivo_propuestas(archivo):
    """
    Ejecuta la prevalidación completa de Carga 2.
    """

    try:
        df_original = leer_archivo_propuestas(
            archivo
        )

    except Exception as error:
        return {
            "valido": False,
            "errores": [
                {
                    "fila": None,
                    "error": (
                        "No fue posible leer el archivo Excel: "
                        f"{error}"
                    ),
                }
            ],
            "df": None,
        }

    df_estandarizado = (
        estandarizar_columnas_propuestas(
            df_original
        )
    )

    errores_columnas = (
        validar_columnas_requeridas_propuestas(
            df_estandarizado
        )
    )

    if errores_columnas:
        return {
            "valido": False,
            "errores": errores_columnas,
            "df": None,
        }

    df_preparado = preparar_dataframe_propuestas(
        df_estandarizado
    )

    df_normalizado = normalizar_archivo_propuestas(
        df_preparado
    )

    df_normalizado = eliminar_filas_vacias_propuestas(
        df_normalizado
    )

    if (
        df_normalizado is None
        or df_normalizado.empty
    ):
        return {
            "valido": False,
            "errores": [
                {
                    "fila": None,
                    "error": (
                        "El archivo no contiene propuestas "
                        "válidas para procesar."
                    ),
                }
            ],
            "df": df_normalizado,
        }

    errores = []

    errores.extend(
        validar_contenido_propuestas(
            df_normalizado
        )
    )

    errores.extend(
        validar_duplicados_propuestas(
            df_normalizado
        )
    )

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "df": df_normalizado.reset_index(
            drop=True
        ),
    }


__all__ = [
    "COLUMNAS_REQUERIDAS_PROPUESTAS",
    "NORMALIZADORES_PROPUESTAS",
    "leer_archivo_propuestas",
    "estandarizar_columnas_propuestas",
    "validar_columnas_requeridas_propuestas",
    "preparar_dataframe_propuestas",
    "normalizar_archivo_propuestas",
    "eliminar_filas_vacias_propuestas",
    "validar_contenido_propuestas",
    "validar_duplicados_propuestas",
    "prevalidar_archivo_propuestas",
]