"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
services/analytics_service.py

Descripción:
Servicio analítico central de SIMI.
Orquesta KPIs, rankings, variaciones y estructuras listas
para mostrarse en los módulos de Streamlit.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import pandas as pd

from utils.helpers import (
    obtener_resumen_general,
    ranking_proveedores,
    ranking_claves,
    filtrar_por_clave,
    filtrar_por_proveedor,
    obtener_resumen_clave,
    obtener_detalle_clave,
    obtener_resumen_precios,
    obtener_resumen_proveedor,
    obtener_detalle_proveedor,
    extraer_numero_investigacion,
)


# ==========================================================
# DASHBOARD GENERAL
# ==========================================================

def obtener_dashboard(df: pd.DataFrame) -> dict:
    """
    Devuelve toda la información necesaria para el resumen general.
    """

    resumen = obtener_resumen_general(df)

    resumen_investigacion = (
        df.groupby("INVESTIGACION")
        .agg(
            archivo=("ARCHIVO", "first"),
            registros=("CLAVE", "count"),
            claves=("CLAVE", "nunique"),
            proveedores=("RAZON SOCIAL", "nunique"),
            precio_minimo=("PRECIO UNITARIO", "min"),
            precio_maximo=("PRECIO UNITARIO", "max"),
            precio_promedio=("PRECIO UNITARIO", "mean"),
        )
        .reset_index()
        .sort_values("INVESTIGACION")
    )

    return {
        "resumen": resumen,
        "resumen_investigacion": resumen_investigacion,
        "ranking_proveedores": ranking_proveedores(df),
        "ranking_claves": ranking_claves(df),
        "datos": df,
    }


# ==========================================================
# ANÁLISIS POR CLAVE
# ==========================================================

def analizar_clave(
    df: pd.DataFrame,
    clave: str
) -> dict:
    """
    Devuelve análisis completo de una clave.
    """

    df_clave = filtrar_por_clave(df, clave)

    if df_clave.empty:
        return {
            "existe": False,
            "df": df_clave,
            "resumen": {},
            "precios": {},
            "detalle": pd.DataFrame(),
            "pivot": pd.DataFrame(),
        }

    resumen = obtener_resumen_clave(df_clave)
    precios = obtener_resumen_precios(df_clave)
    detalle = obtener_detalle_clave(df_clave)

    pivot = (
        df_clave
        .pivot_table(
            values="PRECIO UNITARIO",
            index="INVESTIGACION",
            columns="RAZON SOCIAL",
            aggfunc="first"
        )
        .round(2)
    )

    return {
        "existe": True,
        "df": df_clave,
        "resumen": resumen,
        "precios": precios,
        "detalle": detalle,
        "pivot": pivot,
    }


# ==========================================================
# ANÁLISIS POR PROVEEDOR
# ==========================================================

def analizar_proveedor(
    df: pd.DataFrame,
    proveedor: str
) -> dict:
    """
    Devuelve análisis completo de un proveedor.
    """

    df_proveedor = filtrar_por_proveedor(df, proveedor)

    if df_proveedor.empty:
        return {
            "existe": False,
            "df": df_proveedor,
            "resumen": {},
            "detalle": pd.DataFrame(),
            "variaciones": {},
            "resumen_claves": pd.DataFrame(),
        }

    df_proveedor = df_proveedor.copy()

    df_proveedor["NUM_INVESTIGACION"] = df_proveedor["INVESTIGACION"].apply(
        extraer_numero_investigacion
    )

    resumen = obtener_resumen_proveedor(df_proveedor)
    detalle = obtener_detalle_proveedor(df_proveedor)
    variaciones = obtener_variaciones_proveedor(df_proveedor)
    resumen_claves = obtener_resumen_claves_proveedor(df_proveedor)

    return {
        "existe": True,
        "df": df_proveedor,
        "resumen": resumen,
        "detalle": detalle,
        "variaciones": variaciones,
        "resumen_claves": resumen_claves,
    }


# ==========================================================
# VARIACIONES DE PROVEEDOR
# ==========================================================

def obtener_variaciones_proveedor(
    df_proveedor: pd.DataFrame
) -> dict:
    """
    Devuelve variaciones de precio por clave para un proveedor.

    Solo considera claves que aparecen en más de una investigación.
    """

    claves_conteo = (
        df_proveedor
        .groupby("CLAVE")["INVESTIGACION"]
        .nunique()
    )

    claves_repetidas = claves_conteo[
        claves_conteo > 1
    ].index.tolist()

    resultado = {}

    for clave in sorted(claves_repetidas):

        df_clave = (
            df_proveedor[
                df_proveedor["CLAVE"] == clave
            ]
            .copy()
            .sort_values("NUM_INVESTIGACION")
        )

        df_variacion = df_clave[
            [
                "INVESTIGACION",
                "DESCRIPCION",
                "PRECIO UNITARIO",
                "PAIS DE ORIGEN",
                "CANTIDAD OFERTADA"
            ]
        ].copy()

        df_variacion["DIFERENCIA VS ANTERIOR"] = (
            df_variacion["PRECIO UNITARIO"].diff()
        )

        df_variacion["% VARIACION"] = (
            df_variacion["PRECIO UNITARIO"].pct_change() * 100
        )

        precio_inicial = df_variacion["PRECIO UNITARIO"].iloc[0]
        precio_final = df_variacion["PRECIO UNITARIO"].iloc[-1]

        cambio_total = 0

        if precio_inicial > 0:
            cambio_total = (
                (precio_final - precio_inicial)
                / precio_inicial
            ) * 100

        resultado[clave] = {
            "descripcion": df_variacion["DESCRIPCION"].iloc[0],
            "df": df_variacion,
            "precio_inicial": precio_inicial,
            "precio_final": precio_final,
            "cambio_total": cambio_total,
        }

    return resultado


# ==========================================================
# RESUMEN DE CLAVES POR PROVEEDOR
# ==========================================================

def obtener_resumen_claves_proveedor(
    df_proveedor: pd.DataFrame
) -> pd.DataFrame:
    """
    Devuelve resumen agrupado por clave para un proveedor.
    """

    return (
        df_proveedor
        .groupby("CLAVE")
        .agg(
            investigaciones=("INVESTIGACION", "nunique"),
            registros=("CLAVE", "count"),
            precio_minimo=("PRECIO UNITARIO", "min"),
            precio_maximo=("PRECIO UNITARIO", "max"),
            precio_promedio=("PRECIO UNITARIO", "mean"),
            paises=("PAIS DE ORIGEN", lambda x: ", ".join(sorted(x.dropna().unique())))
        )
        .reset_index()
        .sort_values("CLAVE")
    )


# ==========================================================
# FUTURA INTEGRACIÓN CON ADJUDICACIONES
# ==========================================================

def integrar_adjudicaciones(
    df_investigaciones: pd.DataFrame,
    df_adjudicaciones: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Punto preparado para integrar adjudicaciones en fases futuras.

    Por ahora, si no existe DataFrame de adjudicaciones,
    devuelve las investigaciones sin cambios.
    """

    if df_adjudicaciones is None or df_adjudicaciones.empty:
        return df_investigaciones

    # Futura lógica:
    # - unir por INVESTIGACION + CLAVE + RFC
    # - marcar proveedor adjudicado
    # - calcular diferencia contra mejor precio
    # - calcular ahorro o sobrecosto

    return df_investigaciones