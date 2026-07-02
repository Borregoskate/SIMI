"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/resumen.py

Descripción:
Pestaña principal de resumen general del sistema.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.helpers import (
    obtener_resumen_general,
    ranking_proveedores,
    ranking_claves,
    formatear_moneda,
)


# ==========================================================
# RESUMEN GENERAL
# ==========================================================

def mostrar_resumen(df: pd.DataFrame) -> None:
    """
    Muestra la pestaña principal de Resumen General.
    """

    st.header("📊 Resumen General")
    st.markdown("Vista ejecutiva de las investigaciones cargadas.")

    resumen = obtener_resumen_general(df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📁 Investigaciones",
            resumen["investigaciones"]
        )

    with col2:
        st.metric(
            "🔑 Claves únicas",
            resumen["claves"]
        )

    with col3:
        st.metric(
            "🏢 Proveedores",
            resumen["proveedores"]
        )

    with col4:
        st.metric(
            "📄 Registros",
            f"{resumen['registros']:,}"
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💰 Precio mínimo",
            formatear_moneda(resumen["precio_minimo"])
        )

    with col2:
        st.metric(
            "💰 Precio máximo",
            formatear_moneda(resumen["precio_maximo"])
        )

    with col3:
        st.metric(
            "💰 Precio promedio",
            formatear_moneda(resumen["precio_promedio"])
        )

    st.markdown("---")

    st.subheader("📋 Resumen por investigación")

    resumen_investigacion = (
        df.groupby("INVESTIGACION")
        .agg(
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

    resumen_mostrar = resumen_investigacion.copy()

    resumen_mostrar["precio_minimo"] = resumen_mostrar["precio_minimo"].apply(formatear_moneda)
    resumen_mostrar["precio_maximo"] = resumen_mostrar["precio_maximo"].apply(formatear_moneda)
    resumen_mostrar["precio_promedio"] = resumen_mostrar["precio_promedio"].apply(formatear_moneda)

    st.dataframe(
        resumen_mostrar,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Ranking de proveedores")

        proveedores = ranking_proveedores(df).head(10)

        st.dataframe(
            proveedores,
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("🔑 Ranking de claves")

        claves = ranking_claves(df).head(10)

        st.dataframe(
            claves,
            use_container_width=True,
            hide_index=True
        )

    with st.expander("🔍 Ver datos consolidados"):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )