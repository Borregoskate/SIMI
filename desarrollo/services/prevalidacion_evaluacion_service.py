"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_evaluacion_service.py

Servicio de prevalidación para la Carga 3:
Evaluación Técnica.

Formato real del archivo:
- Encabezados en la fila 5.
- Los datos comienzan en la fila 6.
- Cada fila debe contener el número de procedimiento.
- OBSERVACIONES se ignora completamente.

Flujo obligatorio:
1. Leer archivo.
2. Estandarizar columnas.
3. Validar estructura.
4. Preparar columnas internas.
5. Normalizar valores.
6. Eliminar filas vacías.
7. Validar contenido.
8. Validar duplicados.
9. Entregar datos normalizados a importación.

Este servicio NO consulta ni modifica la base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re
import unicodedata

import pandas as pd

from services.normalizacion_service import (
    normalizar_clave,
    normalizar_nombre_columna,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
)
from services.validacion_service import (
    NIVEL_ERROR,
    esta_vacio,
    validar_campos_obligatorios,
    validar_duplicados,
)


FILA_ENCABEZADOS_EVALUACION = 5
FILA_INICIAL_DATOS_EVALUACION = 6

COLUMNAS_REQUERIDAS_EVALUACION = {
    "procedimiento": "PROCEDIMIENTO",
    "rfc": "RFC",
    "razon_social": "RAZON_SOCIAL",
    "clave": "CLAVE",
    "opinion_tecnica": "RESULTADO",
}

NORMALIZADORES_EVALUACION = {
    "PROCEDIMIENTO": normalizar_texto,
    "RFC": normalizar_rfc,
    "RAZON_SOCIAL": normalizar_razon_social,
    "CLAVE": normalizar_clave,
}

CAMPOS_OBLIGATORIOS_EVALUACION = [
    "PROCEDIMIENTO",
    "RFC",
    "RAZON_SOCIAL",
    "CLAVE",
    "RESULTADO",
]

RESULTADOS_VALIDOS = {"POSITIVA", "NEGATIVA"}


def leer_archivo_evaluacion(archivo):
    """Lee la primera hoja usando la fila 5 como encabezado."""
    if archivo is None:
        raise ValueError("No se recibió un archivo Excel.")

    if hasattr(archivo, "seek"):
        archivo.seek(0)

    return pd.read_excel(
        archivo,
        sheet_name=0,
        header=FILA_ENCABEZADOS_EVALUACION - 1,
    )


def estandarizar_columnas_evaluacion(df):
    """Normaliza los nombres de columnas del archivo."""
    if df is None:
        return None

    df_estandarizado = df.copy()
    df_estandarizado.columns = [
        normalizar_nombre_columna(columna)
        for columna in df_estandarizado.columns
    ]
    return df_estandarizado


def validar_columnas_requeridas_evaluacion(df):
    """Valida únicamente las columnas utilizadas por SIMI."""
    errores = []

    if df is None:
        return [{
            "fila": None,
            "error": "No se recibió información para validar.",
        }]

    columnas_archivo = set(df.columns)

    for columna in COLUMNAS_REQUERIDAS_EVALUACION:
        if columna not in columnas_archivo:
            errores.append({
                "fila": None,
                "error": f"Falta la columna requerida: {columna}",
            })

    return errores


def preparar_dataframe_evaluacion(df):
    """
    Selecciona únicamente los campos funcionales.

    Las columnas de descripción, país y observaciones del archivo no se
    importan en evaluaciones_tecnicas. Cada fila debe contener el
    procedimiento correspondiente.
    """
    columnas_origen = list(COLUMNAS_REQUERIDAS_EVALUACION.keys())

    df_trabajo = df[columnas_origen].copy()
    df_trabajo = df_trabajo.rename(
        columns=COLUMNAS_REQUERIDAS_EVALUACION
    )

    return df_trabajo


def _quitar_acentos(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


def normalizar_resultado_evaluacion(valor):
    """
    Convierte variantes como:
    - OPINION POSITIVA
    - OPINIÓN POSITIVA
    - positiva
    - NEGATIVA

    a los valores definitivos:
    - POSITIVA
    - NEGATIVA
    """
    if esta_vacio(valor):
        return None

    texto = _quitar_acentos(valor).upper().strip()
    texto = re.sub(r"[^A-Z]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if texto in {"POSITIVA", "OPINION POSITIVA"}:
        return "POSITIVA"

    if texto in {"NEGATIVA", "OPINION NEGATIVA"}:
        return "NEGATIVA"

    return texto


def normalizar_archivo_evaluacion(df):
    """Normaliza todos los valores antes de validar contenido."""
    df_normalizado = df.copy()

    for columna, normalizador in NORMALIZADORES_EVALUACION.items():
        if columna in df_normalizado.columns:
            df_normalizado[columna] = (
                df_normalizado[columna].apply(normalizador)
            )

    df_normalizado["RESULTADO"] = (
        df_normalizado["RESULTADO"]
        .apply(normalizar_resultado_evaluacion)
    )

    return df_normalizado


def eliminar_filas_vacias_evaluacion(df):
    """Elimina filas completamente vacías después de normalizar."""
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
    """Convierte mensajes estándar al formato utilizado por la UI."""
    errores = []

    for mensaje in mensajes or []:
        if mensaje.get("nivel") != NIVEL_ERROR:
            continue

        errores.append({
            "fila": mensaje.get("fila"),
            "error": mensaje.get("mensaje"),
        })

    return errores


def validar_contenido_evaluacion(df):
    """Valida campos obligatorios y resultados técnicos."""
    mensajes = validar_campos_obligatorios(
        df=df,
        campos_obligatorios=CAMPOS_OBLIGATORIOS_EVALUACION,
        fila_inicio_excel=FILA_INICIAL_DATOS_EVALUACION,
    )

    errores = convertir_mensajes_a_errores(mensajes)

    for posicion, (_, fila) in enumerate(df.iterrows()):
        fila_excel = FILA_INICIAL_DATOS_EVALUACION + posicion
        resultado = fila.get("RESULTADO")

        if esta_vacio(resultado):
            continue

        if resultado not in RESULTADOS_VALIDOS:
            errores.append({
                "fila": fila_excel,
                "error": (
                    "La OPINION TÉCNICA debe ser POSITIVA o NEGATIVA. "
                    f"Valor recibido: {resultado}"
                ),
            })

    procedimientos = [
        valor
        for valor in df["PROCEDIMIENTO"].dropna().unique().tolist()
        if not esta_vacio(valor)
    ]

    if len(procedimientos) > 1:
        errores.append({
            "fila": None,
            "error": (
                "El archivo contiene más de un procedimiento: "
                + ", ".join(map(str, procedimientos))
            ),
        })

    return errores


def validar_duplicados_evaluacion(df):
    """
    No permite más de una evaluación para el mismo procedimiento,
    RFC y clave dentro del archivo.
    """
    mensajes = validar_duplicados(
        df=df,
        campos=[
            "PROCEDIMIENTO",
            "RFC",
            "CLAVE",
        ],
        fila_inicio_excel=FILA_INICIAL_DATOS_EVALUACION,
        nivel=NIVEL_ERROR,
        mensaje=(
            "Existe más de una evaluación para el mismo "
            "procedimiento, RFC y clave."
        ),
    )

    return convertir_mensajes_a_errores(mensajes)


def prevalidar_archivo_evaluacion(archivo):
    """Ejecuta la prevalidación completa de la Carga 3."""
    try:
        df_original = leer_archivo_evaluacion(archivo)
    except Exception as error:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": (
                    "No fue posible leer el archivo Excel: "
                    f"{error}"
                ),
            }],
            "df": None,
        }

    df_estandarizado = estandarizar_columnas_evaluacion(
        df_original
    )

    errores_columnas = validar_columnas_requeridas_evaluacion(
        df_estandarizado
    )

    if errores_columnas:
        return {
            "valido": False,
            "errores": errores_columnas,
            "df": None,
        }

    df_preparado = preparar_dataframe_evaluacion(
        df_estandarizado
    )
    df_normalizado = normalizar_archivo_evaluacion(
        df_preparado
    )
    df_normalizado = eliminar_filas_vacias_evaluacion(
        df_normalizado
    )

    if df_normalizado is None or df_normalizado.empty:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": (
                    "El archivo no contiene evaluaciones "
                    "técnicas válidas para procesar."
                ),
            }],
            "df": df_normalizado,
        }

    errores = []
    errores.extend(
        validar_contenido_evaluacion(df_normalizado)
    )
    errores.extend(
        validar_duplicados_evaluacion(df_normalizado)
    )

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "df": df_normalizado.reset_index(drop=True),
    }


__all__ = [
    "FILA_ENCABEZADOS_EVALUACION",
    "FILA_INICIAL_DATOS_EVALUACION",
    "COLUMNAS_REQUERIDAS_EVALUACION",
    "NORMALIZADORES_EVALUACION",
    "CAMPOS_OBLIGATORIOS_EVALUACION",
    "RESULTADOS_VALIDOS",
    "leer_archivo_evaluacion",
    "estandarizar_columnas_evaluacion",
    "validar_columnas_requeridas_evaluacion",
    "preparar_dataframe_evaluacion",
    "normalizar_resultado_evaluacion",
    "normalizar_archivo_evaluacion",
    "eliminar_filas_vacias_evaluacion",
    "validar_contenido_evaluacion",
    "validar_duplicados_evaluacion",
    "prevalidar_archivo_evaluacion",
]
