"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/analisis_proveedores.py

Descripción:
Pestaña de análisis por proveedor.
Esta versión usa analytics_service.py como motor analítico.

Versión: 1.1.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from services.analytics_service import analizar_proveedor

from utils.helpers import (
    obtener_lista_proveedores,
    formatear_moneda,
    formatear_porcentaje,
)


def mostrar_analisis_proveedor(df: pd.DataFrame) -> None:
    """
    Muestra el análisis detallado por proveedor.
    """

    st.header("🏢 Análisis por Proveedor")

    proveedores = obtener_lista_proveedores(df)

    if not proveedores:
        st.warning("No se encontraron proveedores disponibles.")
        return

    proveedor_seleccionado = st.selectbox(
        "Selecciona un proveedor",
        proveedores,
        key="selector_proveedor"
    )

    analisis = analizar_proveedor(
        df,
        proveedor_seleccionado
    )

    if not analisis["existe"]:
        st.warning("No hay información para el proveedor seleccionado.")
        return

    df_proveedor = analisis["df"]
    resumen = analisis["resumen"]
    detalle = analisis["detalle"]
    variaciones = analisis["variaciones"]
    resumen_claves = analisis["resumen_claves"]

    st.subheader(f"📋 {resumen['proveedor']}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "RFC",
            resumen["rfc"]
        )

    with col2:
        st.metric(
            "🔑 Claves distintas",
            resumen["total_claves"]
        )

    with col3:
        st.metric(
            "📁 Investigaciones",
            resumen["total_investigaciones"]
        )

    st.markdown("---")

    # ======================================================
    # 1. DETALLE DEL PROVEEDOR
    # ======================================================

    st.subheader("📋 Detalle del proveedor")

    detalle_mostrar = detalle.copy()

    if "PRECIO UNITARIO" in detalle_mostrar.columns:
        detalle_mostrar["PRECIO UNITARIO"] = detalle_mostrar[
            "PRECIO UNITARIO"
        ].apply(formatear_moneda)

    if "CANTIDAD OFERTADA" in detalle_mostrar.columns:
        detalle_mostrar["CANTIDAD OFERTADA"] = detalle_mostrar[
            "CANTIDAD OFERTADA"
        ].apply(
            lambda x: f"{x:,.0f}"
        )

    st.dataframe(
        detalle_mostrar,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ======================================================
    # 2. ANÁLISIS DE VARIACIONES
    # ======================================================

    st.subheader("📊 Análisis de variaciones")

    if not variaciones:
        st.info(
            "Este proveedor no tiene claves repetidas en múltiples investigaciones."
        )
    else:
        st.info(
            f"Se encontraron {len(variaciones)} clave(s) con participación en múltiples investigaciones."
        )

        for clave, info in variaciones.items():

            st.markdown(f"### 🔑 Clave: {clave}")
            st.caption(info["descripcion"])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Precio inicial",
                    formatear_moneda(info["precio_inicial"])
                )

            with col2:
                st.metric(
                    "Precio final",
                    formatear_moneda(info["precio_final"])
                )

            with col3:
                st.metric(
                    "Variación total",
                    formatear_porcentaje(info["cambio_total"])
                )

            df_mostrar = info["df"].copy()

            if "PRECIO UNITARIO" in df_mostrar.columns:
                df_mostrar["PRECIO UNITARIO"] = df_mostrar[
                    "PRECIO UNITARIO"
                ].apply(formatear_moneda)

            if "DIFERENCIA VS ANTERIOR" in df_mostrar.columns:
                df_mostrar["DIFERENCIA VS ANTERIOR"] = df_mostrar[
                    "DIFERENCIA VS ANTERIOR"
                ].apply(
                    lambda x: "" if pd.isna(x) else formatear_moneda(x)
                )

            if "% VARIACION" in df_mostrar.columns:
                df_mostrar["% VARIACION"] = df_mostrar[
                    "% VARIACION"
                ].apply(
                    lambda x: "" if pd.isna(x) else formatear_porcentaje(x)
                )

            if "CANTIDAD OFERTADA" in df_mostrar.columns:
                df_mostrar["CANTIDAD OFERTADA"] = df_mostrar[
                    "CANTIDAD OFERTADA"
                ].apply(
                    lambda x: f"{x:,.0f}"
                )

            st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

    # ======================================================
    # 3. GRÁFICA HISTÓRICA
    # ======================================================

    st.subheader("📈 Gráfica histórica")

    if not variaciones:
        st.info(
            "No hay claves repetidas suficientes para generar gráfica histórica."
        )
    else:
        claves_variacion = list(variaciones.keys())

        clave_grafica = st.selectbox(
            "Selecciona una clave para graficar",
            claves_variacion,
            key="selector_clave_grafica_proveedor"
        )

        df_grafica = variaciones[clave_grafica]["df"].copy()

        fig = px.line(
            df_grafica,
            x="INVESTIGACION",
            y="PRECIO UNITARIO",
            markers=True,
            text="PRECIO UNITARIO",
            title=f"Evolución histórica - {clave_grafica}",
            labels={
                "INVESTIGACION": "Investigación",
                "PRECIO UNITARIO": "Precio unitario"
            }
        )

        fig.update_traces(
            texttemplate="$%{y:,.2f}",
            textposition="top center"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    # ======================================================
    # 4. RESUMEN POR CLAVE
    # ======================================================

    st.subheader("📊 Resumen por clave")

    resumen_mostrar = resumen_claves.copy()

    if "precio_minimo" in resumen_mostrar.columns:
        resumen_mostrar["precio_minimo"] = resumen_mostrar[
            "precio_minimo"
        ].apply(formatear_moneda)

    if "precio_maximo" in resumen_mostrar.columns:
        resumen_mostrar["precio_maximo"] = resumen_mostrar[
            "precio_maximo"
        ].apply(formatear_moneda)

    if "precio_promedio" in resumen_mostrar.columns:
        resumen_mostrar["precio_promedio"] = resumen_mostrar[
            "precio_promedio"
        ].apply(formatear_moneda)

    st.dataframe(
        resumen_mostrar,
        use_container_width=True,
        hide_index=True
    )