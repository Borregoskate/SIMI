"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/carga.py

Descripción:
Módulo de interfaz para cargar investigaciones de mercado
desde Streamlit.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from services.excel_service import procesar_archivos


# ==========================================================
# CARGA PRINCIPAL
# ==========================================================

def cargar_investigaciones() -> pd.DataFrame | None:
    """
    Muestra el cargador de archivos y devuelve el DataFrame
    consolidado de investigaciones.

    Esta función es llamada directamente desde app.py.
    """

    st.sidebar.header("📁 Carga de investigaciones")

    uploaded_files = st.sidebar.file_uploader(
        "Carga tus investigaciones homologadas",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        return None

    resultado = procesar_archivos(uploaded_files)

    df_consolidado = resultado["df_consolidado"]
    archivos_validos = resultado["archivos_validos"]
    archivos_invalidos = resultado["archivos_invalidos"]

    if df_consolidado.empty:
        st.error("❌ No se pudo cargar ningún archivo válido.")

        if archivos_invalidos:
            with st.expander("Ver errores de carga"):
                for archivo in archivos_invalidos:
                    st.error(f"Archivo: {archivo['archivo']}")
                    for error in archivo["errores"]:
                        st.write(f"- {error}")

        return None

    st.sidebar.success(
        f"✅ {len(archivos_validos)} archivo(s) cargado(s)"
    )

    st.sidebar.info(
        f"📊 {len(df_consolidado):,} registros consolidados"
    )

    with st.sidebar.expander("📋 Archivos cargados"):
        for archivo in archivos_validos:
            st.write(
                f"✅ {archivo['archivo']} — "
                f"{archivo['registros']:,} registros"
            )

    if archivos_invalidos:
        with st.sidebar.expander("⚠️ Archivos con error"):
            for archivo in archivos_invalidos:
                st.write(f"❌ {archivo['archivo']}")
                for error in archivo["errores"]:
                    st.caption(error)

    return df_consolidado