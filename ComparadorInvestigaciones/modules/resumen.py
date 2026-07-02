"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/resumen.py

Descripción:
Pestaña principal de resumen general del sistema.
Esta versión usa analytics_service.py como motor analítico.

Versión: 1.1.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from services.analytics_service import obtener_dashboard
from modules.exportacion import mostrar_exportacion

from utils.helpers import (
    formatear_moneda,
)


def mostrar_resumen(df: pd.DataFrame) -> None:
    """
    Muestra la pestaña principal de Resumen General.
    """

    st.header("📊 Resumen General")
    st.markdown("Vista ejecutiva de las investigaciones cargadas.")

    dashboard = obtener_dashboard(df)

    resumen = dashboard["resumen"]
    resumen_investigacion = dashboard["resumen_investigacion"]
    ranking_proveedores_df = dashboard["ranking_proveedores"]
    ranking_claves_df = dashboard["ranking_claves"]

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

    resumen_mostrar = resumen_investigacion.copy()

    resumen_mostrar["precio_minimo"] = resumen_mostrar["precio_minimo"].apply(
        formatear_moneda
    )

    resumen_mostrar["precio_maximo"] = resumen_mostrar["precio_maximo"].apply(
        formatear_moneda
    )

    resumen_mostrar["precio_promedio"] = resumen_mostrar["precio_promedio"].apply(
        formatear_moneda
    )

    st.dataframe(
        resumen_mostrar,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Ranking de proveedores")

        st.dataframe(
            ranking_proveedores_df.head(10),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("🔑 Ranking de claves")

        st.dataframe(
            ranking_claves_df.head(10),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("🔍 Ver datos consolidados"):
        st.dataframe(
            dashboard["datos"],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    mostrar_exportacion(df)