"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_universo_service.py

Servicio de prevalidación para la Carga 1:
Universo del Procedimiento.

Flujo obligatorio:

1. Leer archivo.
2. Estandarizar columnas.
3. Normalizar valores.
4. Eliminar filas completamente vacías.
5. Validar estructura y contenido.
6. Validar contra base de datos.
7. Entregar datos preparados a importación.

Este servicio NO inserta información.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

import pandas as pd

from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_texto,
)
from services.validacion_catalogos_service import (
    validar_claves_contra_catalogo,
    validar_procedimiento_existente,
)
from services.validacion_service import (
    NIVEL_ERROR,
    validar_carga_1_universo,
)


HOJA_UNIVERSO = "Propuesta Económica"

COLUMNAS_UNIVERSO = [
    "CLAVE",
    "DESCRIPCION",
    "CANTIDAD_REQUERIDA",
]


def leer_archivo_universo(archivo):
    """
    Lee el archivo oficial de Universo del Procedimiento.

    Estructura:

    - Hoja: Propuesta Económica.
    - Encabezados: fila 7.
    - Datos relevantes: columnas C, D y H.
    """

    try:
        if archivo is None:
            return None, "No se recibió un archivo Excel."

        if hasattr(archivo, "seek"):
            archivo.seek(0)

        df = pd.read_excel(
            archivo,
            sheet_name=HOJA_UNIVERSO,
            header=6,
            usecols="C,D,H",
        )

        if len(df.columns) != len(COLUMNAS_UNIVERSO):
            return (
                None,
                "No fue posible identificar las columnas "
                "esperadas del universo.",
            )

        df.columns = COLUMNAS_UNIVERSO

        return df, None

    except ValueError:
        return (
            None,
            f"No se encontró la hoja "
            f"'{HOJA_UNIVERSO}' en el archivo.",
        )

    except Exception as error:
        return (
            None,
            f"Error al leer el archivo: {error}",
        )


def normalizar_dataframe_universo(df):
    """
    Normaliza los valores del Universo antes de validar.
    """

    if df is None:
        return None

    df_normalizado = df.copy()

    df_normalizado["CLAVE"] = (
        df_normalizado["CLAVE"]
        .apply(normalizar_clave)
    )

    df_normalizado["DESCRIPCION"] = (
        df_normalizado["DESCRIPCION"]
        .apply(normalizar_texto)
    )

    df_normalizado["CANTIDAD_REQUERIDA"] = (
        df_normalizado["CANTIDAD_REQUERIDA"]
        .apply(normalizar_decimal)
    )

    return df_normalizado


def eliminar_filas_vacias_universo(df):
    """
    Elimina filas sin clave, descripción ni cantidad.

    La eliminación ocurre después de la normalización.
    """

    if df is None:
        return None

    mascara_con_datos = ~(
        df["CLAVE"].isna()
        & df["DESCRIPCION"].isna()
        & df["CANTIDAD_REQUERIDA"].isna()
    )

    return df[mascara_con_datos].copy()


def convertir_mensajes_a_errores(mensajes):
    """
    Convierte los mensajes estructurados al formato que actualmente
    consume carga_universo.py.
    """

    errores = []

    for mensaje in mensajes or []:
        if mensaje.get("nivel") != NIVEL_ERROR:
            continue

        fila = mensaje.get("fila")
        texto = mensaje.get("mensaje", "Error de validación.")

        if fila is not None:
            errores.append(
                f"Fila {fila}: {texto}"
            )
        else:
            errores.append(texto)

    return errores


def prevalidar_universo_procedimiento(archivo):
    """
    Ejecuta la prevalidación estructural de la Carga 1.

    Reglas:

    - CLAVE obligatoria.
    - DESCRIPCION obligatoria.
    - CANTIDAD_REQUERIDA opcional.
    - No se permiten claves duplicadas.
    """

    df_original, error_lectura = leer_archivo_universo(
        archivo
    )

    if error_lectura:
        return {
            "valido": False,
            "dataframe": None,
            "errores": [error_lectura],
            "resumen": {
                "total_registros": 0,
                "total_claves_unicas": 0,
                "total_duplicados": 0,
                "total_errores": 1,
            },
        }

    df_normalizado = normalizar_dataframe_universo(
        df_original
    )

    df_preparado = eliminar_filas_vacias_universo(
        df_normalizado
    )

    if df_preparado is None or df_preparado.empty:
        return {
            "valido": False,
            "dataframe": df_preparado,
            "errores": [
                "El archivo no contiene registros válidos "
                "para procesar."
            ],
            "resumen": {
                "total_registros": 0,
                "total_claves_unicas": 0,
                "total_duplicados": 0,
                "total_errores": 1,
            },
        }

    resultado_validacion = validar_carga_1_universo(
        df=df_preparado,
        fila_inicio_excel=8,
    )

    errores = convertir_mensajes_a_errores(
        resultado_validacion["mensajes"]
    )

    resumen_general = resultado_validacion["resumen"]

    resumen = {
        "total_registros": resumen_general.get(
            "total_registros",
            0,
        ),
        "total_claves_unicas": resumen_general.get(
            "claves_unicas",
            0,
        ),
        "total_duplicados": resumen_general.get(
            "duplicados_clave",
            0,
        ),
        "total_errores": resumen_general.get(
            "errores",
            0,
        ),
    }

    return {
        "valido": resultado_validacion["valido"],
        "dataframe": resultado_validacion[
            "datos_validados"
        ],
        "errores": errores,
        "resumen": resumen,
    }


def prevalidar_universo_contra_bd(
    df,
    conn,
    numero_procedimiento,
):
    """
    Ejecuta la validación del universo contra la base de datos.

    Reglas:

    - El procedimiento no debe existir.
    - Solo se verifica la existencia de la clave.
    - No se compara la descripción contra catálogo.
    - Las claves nuevas se marcan para futura inserción.
    """

    errores = []

    numero_normalizado = normalizar_texto(
        numero_procedimiento
    )

    if not numero_normalizado:
        errores.append(
            "El número o nombre del procedimiento "
            "es obligatorio."
        )

        return {
            "success": False,
            "df": df,
            "errores": errores,
            "resumen": {
                "total_registros": 0 if df is None else len(df),
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": len(errores),
            },
        }

    validacion_procedimiento = (
        validar_procedimiento_existente(
            numero_procedimiento=numero_normalizado,
            conn=conn,
        )
    )

    if validacion_procedimiento["existe"]:
        errores.append(
            f"El procedimiento '{numero_normalizado}' "
            "ya existe en base de datos."
        )

        return {
            "success": False,
            "df": df,
            "errores": errores,
            "resumen": {
                "total_registros": 0 if df is None else len(df),
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": len(errores),
            },
        }

    resultado_claves = validar_claves_contra_catalogo(
        df=df,
        conn=conn,
    )

    errores.extend(
        resultado_claves.get("errores", [])
    )

    resumen = resultado_claves.get(
        "resumen",
        {},
    ).copy()

    resumen["errores"] = len(errores)

    return {
        "success": len(errores) == 0,
        "df": resultado_claves.get("df"),
        "errores": errores,
        "resumen": resumen,
    }


# Compatibilidad temporal con código anterior.
limpiar_dataframe_universo = normalizar_dataframe_universo


__all__ = [
    "HOJA_UNIVERSO",
    "COLUMNAS_UNIVERSO",
    "leer_archivo_universo",
    "normalizar_dataframe_universo",
    "limpiar_dataframe_universo",
    "eliminar_filas_vacias_universo",
    "prevalidar_universo_procedimiento",
    "prevalidar_universo_contra_bd",
]

