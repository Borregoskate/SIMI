"""
SIMI - Servicio de Invitaciones

Lee archivos de invitación protegidos con contraseña y extrae:
- CLAVE
- DESCRIPCION
- CANTIDAD REQUERIDA
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import msoffcrypto


PASSWORD_INVITACION = "EMERGENTE"
HOJA_INVITACION = "Propuesta Económica"


def desencriptar_excel(file: Any) -> BytesIO:
    """
    Desencripta un Excel protegido con contraseña.
    """

    decrypted = BytesIO()

    office_file = msoffcrypto.OfficeFile(file)
    office_file.load_key(password=PASSWORD_INVITACION)
    office_file.decrypt(decrypted)

    decrypted.seek(0)

    return decrypted


def leer_archivo_invitacion(file: Any) -> pd.DataFrame:
    """
    Lee el archivo de invitación.

    Encabezados en fila 7:
    C = Clave
    D = Descripción
    H = Cantidad Requerida
    """

    try:
        archivo_excel = desencriptar_excel(file)
    except Exception:
        file.seek(0)
        archivo_excel = file

    df = pd.read_excel(
        archivo_excel,
        sheet_name=HOJA_INVITACION,
        header=6,
        dtype=str
    )

    columnas = {
        "Clave": "CLAVE",
        "Descripción": "DESCRIPCION",
        "Cantidad Requerida": "CANTIDAD REQUERIDA",
    }

    df = df.rename(columns=lambda x: str(x).strip())

    df = df.rename(columns=columnas)

    columnas_necesarias = [
        "CLAVE",
        "DESCRIPCION",
        "CANTIDAD REQUERIDA"
    ]

    df = df[columnas_necesarias].copy()

    df = df.dropna(how="all")

    df["CLAVE"] = df["CLAVE"].astype(str).str.strip()
    df["DESCRIPCION"] = df["DESCRIPCION"].astype(str).str.strip()

    df["CANTIDAD REQUERIDA"] = (
        df["CANTIDAD REQUERIDA"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["CANTIDAD REQUERIDA"] = pd.to_numeric(
        df["CANTIDAD REQUERIDA"],
        errors="coerce"
    ).fillna(0)

    df = df[
        (df["CLAVE"] != "")
        & (df["CLAVE"].str.upper() != "NAN")
    ].copy()

    return df.reset_index(drop=True)


def procesar_invitacion(
    file: Any,
    investigacion: str
) -> dict:
    """
    Procesa una invitación individual.
    """

    resultado = {
        "valido": False,
        "archivo": file.name,
        "investigacion": investigacion,
        "registros": 0,
        "df": pd.DataFrame(),
        "errores": [],
    }

    try:
        df = leer_archivo_invitacion(file)

        df["INVESTIGACION"] = investigacion
        df["ARCHIVO_INVITACION"] = file.name

        resultado["valido"] = True
        resultado["registros"] = len(df)
        resultado["df"] = df

        return resultado

    except Exception as error:
        resultado["errores"] = [str(error)]
        return resultado


def obtener_claves_desiertas(
    df_invitacion: pd.DataFrame,
    df_ofertas: pd.DataFrame
) -> pd.DataFrame:
    """
    Detecta claves invitadas que no recibieron oferta.
    """

    claves_ofertadas = df_ofertas[
        ["INVESTIGACION", "CLAVE"]
    ].drop_duplicates()

    comparativo = df_invitacion.merge(
        claves_ofertadas,
        on=["INVESTIGACION", "CLAVE"],
        how="left",
        indicator=True
    )

    desiertas = comparativo[
        comparativo["_merge"] == "left_only"
    ].drop(columns=["_merge"])

    return desiertas.reset_index(drop=True)


def obtener_resumen_desiertas(
    df_invitacion: pd.DataFrame,
    df_ofertas: pd.DataFrame
) -> dict:
    """
    Devuelve resumen general de claves invitadas vs ofertadas.
    """

    total_invitadas = df_invitacion["CLAVE"].nunique()
    total_ofertadas = df_ofertas["CLAVE"].nunique()

    df_desiertas = obtener_claves_desiertas(
        df_invitacion,
        df_ofertas
    )

    total_desiertas = df_desiertas["CLAVE"].nunique()

    porcentaje_desiertas = 0

    if total_invitadas > 0:
        porcentaje_desiertas = (
            total_desiertas / total_invitadas
        ) * 100

    return {
        "total_invitadas": total_invitadas,
        "total_ofertadas": total_ofertadas,
        "total_desiertas": total_desiertas,
        "porcentaje_desiertas": porcentaje_desiertas,
        "df_desiertas": df_desiertas,
    }