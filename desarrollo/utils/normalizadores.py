"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

normalizadores.py

Funciones generales para normalización de datos antes de
prevalidar o insertar información en base de datos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import re
import unicodedata
from decimal import Decimal, InvalidOperation


def quitar_acentos(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar_texto(valor):
    if valor is None:
        return None

    texto = str(valor).strip()

    if texto == "" or texto.lower() == "nan":
        return None

    texto = quitar_acentos(texto)
    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_rfc(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return None

    return re.sub(r"[^A-Z0-9]", "", texto)


def normalizar_clave(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return None

    return texto.replace(" ", "")


def normalizar_razon_social(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return None

    return re.sub(r"\s+", " ", texto).strip()


def normalizar_pais(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return None

    texto = texto.replace("\\", "/")
    texto = re.sub(r"\s*/\s*", "/", texto)
    texto = re.sub(r"[-–—]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    equivalencias = {
        "USA": "ESTADOS UNIDOS",
        "U.S.A": "ESTADOS UNIDOS",
        "U.S.A.": "ESTADOS UNIDOS",
        "US": "ESTADOS UNIDOS",
        "U.S": "ESTADOS UNIDOS",
        "U.S.": "ESTADOS UNIDOS",
        "EUA": "ESTADOS UNIDOS",
        "EEUU": "ESTADOS UNIDOS",
        "EE.UU": "ESTADOS UNIDOS",
        "EE.UU.": "ESTADOS UNIDOS",
        "ESTADOS UNIDOS DE AMERICA": "ESTADOS UNIDOS",
        "UNITED STATES": "ESTADOS UNIDOS",
        "UNITED STATES OF AMERICA": "ESTADOS UNIDOS",
    }

    partes = []

    for pais in texto.split("/"):
        pais = pais.strip()

        if not pais:
            continue

        partes.append(equivalencias.get(pais, pais))

    return "/".join(partes) if partes else None


def normalizar_numero(valor):
    if valor is None:
        return None

    texto = str(valor).strip()

    if texto == "" or texto.lower() == "nan":
        return None

    texto = texto.replace(",", "")

    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_decimal(valor):
    if valor is None:
        return None

    texto = str(valor).strip()

    if texto == "" or texto.lower() == "nan":
        return None

    texto = texto.replace(",", "")

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def normalizar_booleano(valor):
    if valor is None:
        return None

    texto = normalizar_texto(valor)

    if texto in ["SI", "S", "YES", "Y", "TRUE", "1", "POSITIVO", "POSITIVA"]:
        return True

    if texto in ["NO", "N", "FALSE", "0", "NEGATIVO", "NEGATIVA"]:
        return False

    return None


def normalizar_dataframe(df, normalizadores: dict):
    """
    Aplica normalizadores por columna a un DataFrame.

    normalizadores:
    {
        "RFC": normalizar_rfc,
        "CLAVE": normalizar_clave,
        "PRECIO UNITARIO": normalizar_decimal
    }
    """

    df_normalizado = df.copy()

    for columna, funcion_normalizadora in normalizadores.items():
        if columna in df_normalizado.columns:
            df_normalizado[columna] = df_normalizado[columna].apply(
                funcion_normalizadora
            )

    return df_normalizado