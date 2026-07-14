"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

normalizadores.py

Funciones generales para normalización de datos antes de
prevalidar o insertar información en base de datos.

Versión: 1.2.0
==============================================================
"""

import re
import unicodedata
from decimal import Decimal, InvalidOperation

import pandas as pd


def quitar_acentos(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor)
    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


def normalizar_texto(valor):
    if valor is None or pd.isna(valor):
        return None

    texto = str(valor).strip()

    if not texto or texto.lower() == "nan":
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
    """
    Normaliza una razón social:

    - Convierte a mayúsculas.
    - Elimina acentos y espacios duplicados.
    - Homologa las formas societarias más frecuentes.

    Ejemplos:
    LABORATORIO EJEMPLO SA DE CV
        -> LABORATORIO EJEMPLO S.A. DE C.V.

    EMPRESA EJEMPLO S DE RL DE CV
        -> EMPRESA EJEMPLO S. DE R.L. DE C.V.
    """
    texto = normalizar_texto(valor)

    if not texto:
        return None

    # Quitar puntos y comas únicamente para reconocer de forma uniforme
    # las terminaciones societarias. Después se reconstruyen.
    texto = re.sub(r"\s*,\s*", " ", texto)
    texto = re.sub(r"\.", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    reemplazos = (
        (
            r"\bS\s+DE\s+RL\s+DE\s+CV\b",
            "S. DE R.L. DE C.V.",
        ),
        (
            r"\bS\s+DE\s+R\s*L\s+DE\s+C\s*V\b",
            "S. DE R.L. DE C.V.",
        ),
        (
            r"\bSA\s+DE\s+CV\b",
            "S.A. DE C.V.",
        ),
        (
            r"\bS\s+A\s+DE\s+C\s+V\b",
            "S.A. DE C.V.",
        ),
        (
            r"\bSC\b",
            "S.C.",
        ),
        (
            r"\bAC\b",
            "A.C.",
        ),
    )

    for patron, reemplazo in reemplazos:
        texto = re.sub(patron, reemplazo, texto)

    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def normalizar_pais(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return None

    texto = texto.replace("\\", "/")
    texto = re.sub(r"\s*/\s*", " / ", texto)
    texto = re.sub(r"[-–—]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

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

        if pais:
            partes.append(equivalencias.get(pais, pais))

    return " / ".join(partes) if partes else None


def normalizar_numero(valor):
    """
    Conserva compatibilidad con los procesos anteriores.

    Para cantidades de SIMI debe utilizarse normalizar_entero().
    """
    if valor is None or pd.isna(valor):
        return None

    texto = str(valor).strip()

    if not texto or texto.lower() == "nan":
        return None

    texto = texto.replace(",", "")

    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_entero(valor):
    """
    Normaliza cantidades como enteros estrictos.

    Acepta:
        100
        100.0
        "100"
        "1,000"

    Rechaza:
        100.5
        "100.50"
        valores no numéricos

    No redondea silenciosamente.
    """
    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, bool):
        return None

    texto = str(valor).strip()

    if not texto or texto.lower() == "nan":
        return None

    texto = texto.replace(",", "")

    try:
        numero = Decimal(texto)
    except (InvalidOperation, ValueError):
        return None

    if not numero.is_finite():
        return None

    if numero != numero.to_integral_value():
        return None

    return int(numero)


def normalizar_decimal(valor):
    if valor is None or pd.isna(valor):
        return None

    texto = str(valor).strip()

    if not texto or texto.lower() == "nan":
        return None

    texto = texto.replace(",", "")

    try:
        numero = Decimal(texto)
    except (InvalidOperation, ValueError):
        return None

    if not numero.is_finite():
        return None

    return numero


def normalizar_booleano(valor):
    if valor is None or pd.isna(valor):
        return None

    texto = normalizar_texto(valor)

    if texto in [
        "SI",
        "S",
        "YES",
        "Y",
        "TRUE",
        "1",
        "POSITIVO",
        "POSITIVA",
    ]:
        return True

    if texto in [
        "NO",
        "N",
        "FALSE",
        "0",
        "NEGATIVO",
        "NEGATIVA",
    ]:
        return False

    return None


def normalizar_dataframe(df, normalizadores: dict):
    if df is None:
        return None

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Se esperaba un DataFrame.")

    df_normalizado = df.copy()

    for columna, funcion_normalizadora in normalizadores.items():
        if columna in df_normalizado.columns:
            df_normalizado[columna] = df_normalizado[columna].apply(
                funcion_normalizadora
            )

    return df_normalizado
