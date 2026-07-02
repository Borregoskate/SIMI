"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/analisis_desiertas.py

Descripción:
Análisis de claves invitadas vs claves ofertadas.
Permite identificar claves desiertas.

Versión: 0.3.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from services.invitacion_service import (
    procesar_invitacion,
    obtener_resumen_desiertas,
)

from utils.helpers import formatear_porcentaje


def mostrar_analisis_desiertas(df_ofertas: pd.DataFrame) -> None:
    """
    Muestra el módulo de análisis de claves desiertas.
    """

    st.header("🚫 Claves Desiertas")
    st.markdown(
        "Carga el archivo de invitación para comparar las claves solicitadas "
        "contra las claves que recibieron oferta."
    )

    investigaciones = sorted(
        df_ofertas["INVESTIGACION"].dropna().unique().tolist()
    )

    investigacion = st.selectbox(
        "Selecciona la investigación correspondiente",
        investigaciones,
        key="selector_investigacion_desiertas"
    )

    archivo_invitacion = st.file_uploader(
        "Carga el archivo de invitación protegido",
        type=["xlsx", "xls"],
        key="uploader_invitacion"
    )

    if archivo_invitacion is None:
        st.info("Carga el archivo de invitación para iniciar el análisis.")
        return

    resultado = procesar_invitacion(
        archivo_invitacion,
        investigacion
    )

    if not resultado["valido"]:
        st.error("No se pudo procesar el archivo de invitación.")

        for error in resultado["errores"]:
            st.write(f"- {error}")

        return

    df_invitacion = resultado["df"]

    df_ofertas_inv = df_ofertas[
        df_ofertas["INVESTIGACION"] == investigacion
    ].copy()

    resumen = obtener_resumen_desiertas(
        df_invitacion,
        df_ofertas_inv
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🔑 Claves invitadas",
            resumen["total_invitadas"]
        )

    with col2:
        st.metric(
            "✅ Claves ofertadas",
            resumen["total_ofertadas"]
        )

    with col3:
        st.metric(
            "🚫 Claves desiertas",
            resumen["total_desiertas"]
        )

    with col4:
        st.metric(
            "📉 % desiertas",
            formatear_porcentaje(resumen["porcentaje_desiertas"])
        )

    st.markdown("---")

    st.subheader("🚫 Detalle de claves desiertas")

    df_desiertas = resumen["df_desiertas"]

    if df_desiertas.empty:
        st.success("No se detectaron claves desiertas para esta investigación.")
    else:
        st.dataframe(
            df_desiertas,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    with st.expander("📋 Ver claves invitadas"):
        st.dataframe(
            df_invitacion,
            use_container_width=True,
            hide_index=True
        )