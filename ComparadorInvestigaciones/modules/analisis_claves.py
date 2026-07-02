"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/analisis_claves.py

Descripción:
Pestaña de análisis por clave.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helpers import (
    obtener_lista_claves,
    filtrar_por_clave,
    obtener_resumen_clave,
    obtener_detalle_clave,
    obtener_resumen_precios,
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

    df_clave = filtrar_por_clave(df, clave_seleccionada)

    if df_clave.empty:
        st.warning("No hay información para la clave seleccionada.")
        return

    resumen = obtener_resumen_clave(df_clave)
    precios = obtener_resumen_precios(df_clave)

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

    detalle = obtener_detalle_clave(df_clave)

    detalle_mostrar = detalle.copy()
    detalle_mostrar["PRECIO UNITARIO"] = detalle_mostrar["PRECIO UNITARIO"].apply(formatear_moneda)
    detalle_mostrar["CANTIDAD OFERTADA"] = detalle_mostrar["CANTIDAD OFERTADA"].apply(
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

    with st.expander("📊 Tabla comparativa Archivo vs Proveedor"):
        tabla_pivot = (
            df_clave
            .pivot_table(
                values="PRECIO UNITARIO",
                index="INVESTIGACION",
                columns="RAZON SOCIAL",
                aggfunc="first"
            )
            .round(2)
        )

        st.dataframe(
            tabla_pivot,
            use_container_width=True
        )