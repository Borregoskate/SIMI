"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/analisis_proveedores.py

Descripción:
Pestaña de análisis por proveedor.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helpers import (
    obtener_lista_proveedores,
    filtrar_por_proveedor,
    obtener_resumen_proveedor,
    obtener_detalle_proveedor,
    formatear_moneda,
    formatear_porcentaje,
    extraer_numero_investigacion,
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

    df_proveedor = filtrar_por_proveedor(
        df,
        proveedor_seleccionado
    )

    if df_proveedor.empty:
        st.warning("No hay información para el proveedor seleccionado.")
        return

    df_proveedor = df_proveedor.copy()
    df_proveedor["NUM_INVESTIGACION"] = df_proveedor["INVESTIGACION"].apply(
        extraer_numero_investigacion
    )

    resumen = obtener_resumen_proveedor(df_proveedor)

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

    detalle = obtener_detalle_proveedor(df_proveedor)

    detalle_mostrar = detalle.copy()

    if "PRECIO UNITARIO" in detalle_mostrar.columns:
        detalle_mostrar["PRECIO UNITARIO"] = detalle_mostrar["PRECIO UNITARIO"].apply(
            formatear_moneda
        )

    if "CANTIDAD OFERTADA" in detalle_mostrar.columns:
        detalle_mostrar["CANTIDAD OFERTADA"] = detalle_mostrar["CANTIDAD OFERTADA"].apply(
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

    claves_conteo = (
        df_proveedor
        .groupby("CLAVE")["INVESTIGACION"]
        .nunique()
    )

    claves_repetidas = claves_conteo[
        claves_conteo > 1
    ].index.tolist()

    if not claves_repetidas:
        st.info(
            "Este proveedor no tiene claves repetidas en múltiples investigaciones."
        )
    else:
        st.info(
            f"Se encontraron {len(claves_repetidas)} clave(s) con participación en múltiples investigaciones."
        )

        for clave in sorted(claves_repetidas):
            df_clave = (
                df_proveedor[
                    df_proveedor["CLAVE"] == clave
                ]
                .copy()
                .sort_values("NUM_INVESTIGACION")
            )

            st.markdown(f"### 🔑 Clave: {clave}")

            descripcion = df_clave["DESCRIPCION"].iloc[0]
            st.caption(descripcion)

            df_variacion = df_clave[
                [
                    "INVESTIGACION",
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

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Precio inicial",
                    formatear_moneda(precio_inicial)
                )

            with col2:
                st.metric(
                    "Precio final",
                    formatear_moneda(precio_final)
                )

            with col3:
                st.metric(
                    "Variación total",
                    formatear_porcentaje(cambio_total)
                )

            df_mostrar = df_variacion.copy()

            df_mostrar["PRECIO UNITARIO"] = df_mostrar["PRECIO UNITARIO"].apply(
                formatear_moneda
            )

            df_mostrar["DIFERENCIA VS ANTERIOR"] = df_mostrar[
                "DIFERENCIA VS ANTERIOR"
            ].apply(
                lambda x: "" if pd.isna(x) else formatear_moneda(x)
            )

            df_mostrar["% VARIACION"] = df_mostrar[
                "% VARIACION"
            ].apply(
                lambda x: "" if pd.isna(x) else formatear_porcentaje(x)
            )

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

    if not claves_repetidas:
        st.info(
            "No hay claves repetidas suficientes para generar gráfica histórica."
        )
    else:
        clave_grafica = st.selectbox(
            "Selecciona una clave para graficar",
            sorted(claves_repetidas),
            key="selector_clave_grafica_proveedor"
        )

        df_grafica = (
            df_proveedor[
                df_proveedor["CLAVE"] == clave_grafica
            ]
            .copy()
            .sort_values("NUM_INVESTIGACION")
        )

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

    resumen_claves = (
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

    resumen_mostrar = resumen_claves.copy()

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