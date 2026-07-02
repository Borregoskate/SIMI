"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/analisis_claves.py

Descripción:
Pestaña de análisis por clave.
Esta versión usa analytics_service.py como motor analítico.

Versión: 1.1.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from services.analytics_service import analizar_clave

from utils.helpers import (
    obtener_lista_claves,
    formatear_moneda,
    formatear_porcentaje,
)


def mostrar_analisis_clave(df: pd.DataFrame) -> None:
    """
    Muestra el análisis detallado por clave.
    """

    st.header("🔑 Análisis por Clave")

    claves = obtener_lista_claves(df)

    if not claves:
        st.warning("No se encontraron claves disponibles.")
        return

    clave_seleccionada = st.selectbox(
        "Selecciona una clave",
        claves,
        key="selector_clave"
    )

    analisis = analizar_clave(
        df,
        clave_seleccionada
    )

    if not analisis["existe"]:
        st.warning("No hay información para la clave seleccionada.")
        return

    df_clave = analisis["df"]
    resumen = analisis["resumen"]
    precios = analisis["precios"]
    detalle = analisis["detalle"]
    pivot = analisis["pivot"]

    st.subheader(f"📌 Clave: {resumen['clave']}")
    st.info(f"📝 {resumen['descripcion']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏢 Proveedores",
            resumen["total_proveedores"]
        )

    with col2:
        st.metric(
            "📁 Investigaciones",
            resumen["total_investigaciones"]
        )

    with col3:
        st.metric(
            "💰 Mejor precio",
            formatear_moneda(precios["minimo"])
        )

    with col4:
        st.metric(
            "📈 Variación",
            formatear_porcentaje(precios["variacion_pct"])
        )

    st.markdown("---")

    st.subheader("🏆 Mejor y peor precio")

    col1, col2 = st.columns(2)

    with col1:
        mejor = precios["mejor"]

        st.success(
            f"""
            **Mejor precio**  
            Proveedor: **{mejor['proveedor']}**  
            RFC: **{mejor['rfc']}**  
            Investigación: **{mejor['investigacion']}**  
            País: **{mejor['pais']}**  
            Precio: **{formatear_moneda(mejor['precio'])}**
            """
        )

    with col2:
        peor = precios["peor"]

        st.error(
            f"""
            **Precio más alto**  
            Proveedor: **{peor['proveedor']}**  
            RFC: **{peor['rfc']}**  
            Investigación: **{peor['investigacion']}**  
            País: **{peor['pais']}**  
            Precio: **{formatear_moneda(peor['precio'])}**
            """
        )

    st.markdown("---")

    st.subheader("📋 Detalle por investigación y proveedor")

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

    st.subheader("📊 Gráfica comparativa de precios")

    fig = px.bar(
        df_clave,
        x="INVESTIGACION",
        y="PRECIO UNITARIO",
        color="RAZON SOCIAL",
        text="PRECIO UNITARIO",
        title=f"Comparativo de precios - Clave {clave_seleccionada}",
        labels={
            "INVESTIGACION": "Investigación",
            "PRECIO UNITARIO": "Precio unitario",
            "RAZON SOCIAL": "Proveedor"
        },
        barmode="group"
    )

    fig.update_traces(
        texttemplate="$%{text:,.2f}",
        textposition="outside"
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("---")

    with st.expander("📊 Tabla comparativa Investigación vs Proveedor"):
        st.dataframe(
            pivot,
            use_container_width=True
        )