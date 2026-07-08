"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

services/validacion_service.py

Servicio general de validación de datos para procesos de carga.

Sprint 0.6 — Paso 006
Módulo de carga de archivos

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re
import unicodedata

import pandas as pd


# ==========================================================
# CONSTANTES
# ==========================================================

NIVEL_ERROR = "ERROR"
NIVEL_ADVERTENCIA = "ADVERTENCIA"
NIVEL_INFO = "INFO"


# ==========================================================
# NORMALIZACIÓN GENERAL
# ==========================================================

def normalizar_texto(valor):
    """
    Normaliza texto para comparación interna:
    - elimina acentos
    - convierte a mayúsculas
    - elimina espacios dobles
    - elimina saltos de línea
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")

    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def limpiar_texto_usuario(valor):
    """
    Limpia texto conservando una versión presentable para usuario.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def limpiar_clave(valor):
    """
    Limpia una clave sin alterar su formato original.
    """
    if pd.isna(valor):
        return ""

    return str(valor).strip()


# ==========================================================
# GENERADOR DE MENSAJES
# ==========================================================

def crear_mensaje_validacion(
    nivel,
    campo,
    mensaje,
    fila=None,
    valor=None
):
    """
    Crea un mensaje estándar de validación.
    """
    return {
        "nivel": nivel,
        "fila": fila,
        "campo": campo,
        "valor": valor,
        "mensaje": mensaje
    }


# ==========================================================
# VALIDACIONES GENERALES
# ==========================================================

def validar_columnas_requeridas(df, columnas_requeridas):
    """
    Valida que existan las columnas requeridas en un DataFrame.
    """
    mensajes = []

    columnas_archivo = list(df.columns)

    for columna in columnas_requeridas:
        if columna not in columnas_archivo:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ERROR,
                    campo=columna,
                    mensaje=f"No se encontró la columna requerida: {columna}"
                )
            )

    return mensajes


def validar_campos_obligatorios(
    df,
    campos_obligatorios,
    fila_inicio_excel=2
):
    """
    Valida que los campos obligatorios no estén vacíos.
    """
    mensajes = []

    for index, row in df.iterrows():
        fila_excel = index + fila_inicio_excel

        for campo in campos_obligatorios:
            valor = row.get(campo)

            if normalizar_texto(valor) == "":
                mensajes.append(
                    crear_mensaje_validacion(
                        nivel=NIVEL_ERROR,
                        fila=fila_excel,
                        campo=campo,
                        valor=valor,
                        mensaje=f"El campo {campo} es obligatorio."
                    )
                )

    return mensajes


def validar_filas_vacias(
    df,
    campos_base,
    fila_inicio_excel=2
):
    """
    Detecta filas completamente vacías.
    No se considera error crítico; solo advertencia.
    """
    mensajes = []

    for index, row in df.iterrows():
        fila_excel = index + fila_inicio_excel

        fila_vacia = True

        for campo in campos_base:
            if normalizar_texto(row.get(campo)) != "":
                fila_vacia = False
                break

        if fila_vacia:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ADVERTENCIA,
                    fila=fila_excel,
                    campo="FILA",
                    mensaje="Fila completamente vacía. Será ignorada."
                )
            )

    return mensajes


def validar_duplicados(
    df,
    campo,
    fila_inicio_excel=2
):
    """
    Detecta valores duplicados en un campo.
    """
    mensajes = []

    if campo not in df.columns:
        return mensajes

    df_temp = df.copy()
    df_temp["_valor_normalizado"] = df_temp[campo].apply(normalizar_texto)

    df_temp = df_temp[df_temp["_valor_normalizado"] != ""]

    duplicados = df_temp[
        df_temp.duplicated(
            subset=["_valor_normalizado"],
            keep=False
        )
    ]

    for _, row in duplicados.iterrows():
        fila_excel = row.name + fila_inicio_excel

        mensajes.append(
            crear_mensaje_validacion(
                nivel=NIVEL_ADVERTENCIA,
                fila=fila_excel,
                campo=campo,
                valor=row.get(campo),
                mensaje=f"Valor duplicado detectado en {campo}."
            )
        )

    return mensajes


def validar_descripcion_distinta_por_clave(
    df,
    campo_clave="clave",
    campo_descripcion="descripcion",
    fila_inicio_excel=2
):
    """
    Valida que una misma clave no tenga descripciones distintas.
    """
    mensajes = []

    if campo_clave not in df.columns or campo_descripcion not in df.columns:
        return mensajes

    df_temp = df.copy()

    df_temp["_clave_norm"] = df_temp[campo_clave].apply(normalizar_texto)
    df_temp["_descripcion_norm"] = df_temp[campo_descripcion].apply(normalizar_texto)

    df_temp = df_temp[
        (df_temp["_clave_norm"] != "")
        & (df_temp["_descripcion_norm"] != "")
    ]

    grupos = df_temp.groupby("_clave_norm")["_descripcion_norm"].nunique()

    claves_conflictivas = grupos[grupos > 1].index.tolist()

    for clave in claves_conflictivas:
        registros = df_temp[df_temp["_clave_norm"] == clave]

        for _, row in registros.iterrows():
            fila_excel = row.name + fila_inicio_excel

            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ERROR,
                    fila=fila_excel,
                    campo=campo_descripcion,
                    valor=row.get(campo_descripcion),
                    mensaje=(
                        "La misma clave tiene descripciones distintas "
                        "dentro del archivo."
                    )
                )
            )

    return mensajes


def validar_longitud_minima_texto(
    df,
    campo,
    longitud_minima=5,
    fila_inicio_excel=2
):
    """
    Valida que un campo de texto tenga longitud mínima.
    """
    mensajes = []

    if campo not in df.columns:
        return mensajes

    for index, row in df.iterrows():
        fila_excel = index + fila_inicio_excel
        valor = limpiar_texto_usuario(row.get(campo))

        if valor == "":
            continue

        if len(valor) < longitud_minima:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ADVERTENCIA,
                    fila=fila_excel,
                    campo=campo,
                    valor=valor,
                    mensaje=(
                        f"El texto del campo {campo} parece demasiado corto."
                    )
                )
            )

    return mensajes


# ==========================================================
# RESUMEN DE VALIDACIÓN
# ==========================================================

def contar_mensajes_por_nivel(mensajes):
    """
    Cuenta errores, advertencias e información.
    """
    return {
        "errores": sum(1 for m in mensajes if m["nivel"] == NIVEL_ERROR),
        "advertencias": sum(1 for m in mensajes if m["nivel"] == NIVEL_ADVERTENCIA),
        "informativos": sum(1 for m in mensajes if m["nivel"] == NIVEL_INFO),
    }


def generar_resumen_validacion(
    df,
    mensajes,
    campo_clave=None
):
    """
    Genera un resumen general de validación.
    """
    conteo = contar_mensajes_por_nivel(mensajes)

    resumen = {
        "total_registros": len(df),
        "errores": conteo["errores"],
        "advertencias": conteo["advertencias"],
        "informativos": conteo["informativos"],
        "valido": conteo["errores"] == 0,
    }

    if campo_clave and campo_clave in df.columns:
        resumen["claves_unicas"] = (
            df[campo_clave]
            .apply(normalizar_texto)
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        resumen["duplicados_clave"] = (
            df[campo_clave]
            .apply(normalizar_texto)
            .replace("", pd.NA)
            .dropna()
            .duplicated()
            .sum()
        )

    return resumen


# ==========================================================
# VALIDACIÓN GENERAL PARA CARGA 1
# ==========================================================

def validar_carga_1_universo(df, fila_inicio_excel=8):
    """
    Validación específica pero reutilizable para la Carga 1.

    Se valida:
    - campos obligatorios
    - filas vacías
    - claves duplicadas
    - descripciones distintas para la misma clave
    - descripción demasiado corta

    No valida cantidad requerida.
    """
    mensajes = []

    campos_base = [
        "clave",
        "descripcion"
    ]

    mensajes.extend(
        validar_filas_vacias(
            df=df,
            campos_base=campos_base,
            fila_inicio_excel=fila_inicio_excel
        )
    )

    df_no_vacio = df[
        ~(
            (df["clave"].apply(normalizar_texto) == "")
            & (df["descripcion"].apply(normalizar_texto) == "")
        )
    ].copy()

    mensajes.extend(
        validar_campos_obligatorios(
            df=df_no_vacio,
            campos_obligatorios=campos_base,
            fila_inicio_excel=fila_inicio_excel
        )
    )

    mensajes.extend(
        validar_duplicados(
            df=df_no_vacio,
            campo="clave",
            fila_inicio_excel=fila_inicio_excel
        )
    )

    mensajes.extend(
        validar_descripcion_distinta_por_clave(
            df=df_no_vacio,
            campo_clave="clave",
            campo_descripcion="descripcion",
            fila_inicio_excel=fila_inicio_excel
        )
    )

    mensajes.extend(
        validar_longitud_minima_texto(
            df=df_no_vacio,
            campo="descripcion",
            longitud_minima=10,
            fila_inicio_excel=fila_inicio_excel
        )
    )

    resumen = generar_resumen_validacion(
        df=df_no_vacio,
        mensajes=mensajes,
        campo_clave="clave"
    )

    return {
        "valido": resumen["valido"],
        "resumen": resumen,
        "mensajes": mensajes,
        "datos_validados": df_no_vacio.reset_index(drop=True)
    }