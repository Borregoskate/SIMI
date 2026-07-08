"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

modules/carga.py

Pantalla temporal para prueba del módulo de carga de archivos.

Sprint 0.6 — Paso 006
Carga 1 — Universo del Procedimiento

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st
import pandas as pd

from modules.carga_archivos import procesar_carga_1_universo_procedimiento


def mostrar_pantalla_carga_archivos():
    """
    Muestra una pantalla temporal para probar la carga de archivos
    antes de conectar el módulo completo con base de datos.
    """

    st.title("Carga de Archivos SIMI")
    st.subheader("Carga 1 — Universo del Procedimiento")

    st.info(
        "Esta pantalla solo valida el archivo cargado. "
        "Todavía no inserta información en la base de datos."
    )

    archivo_excel = st.file_uploader(
        "Selecciona el archivo Excel de invitación",
        type=["xlsx", "xls"]
    )

    if archivo_excel is None:
        st.warning("Carga un archivo Excel para iniciar la validación.")
        return

    if st.button("Validar archivo"):
        resultado = procesar_carga_1_universo_procedimiento(archivo_excel)

        valido = resultado["valido"]
        datos = resultado["datos"]
        errores = resultado["errores"]
        total_registros = resultado["total_registros"]

        st.divider()

        if valido:
            st.success("Archivo validado correctamente.")
        else:
            st.error("El archivo contiene errores. No se debe guardar en base de datos.")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Registros detectados", total_registros)

        with col2:
            st.metric("Errores encontrados", len(errores))

        st.divider()

        if not datos.empty:
            st.subheader("Vista previa de datos limpios")
            st.dataframe(
                datos,
                width="stretch"
            )
        else:
            st.warning("No se encontraron registros válidos para mostrar.")

        if errores:
            st.subheader("Reporte de errores")

            df_errores = pd.DataFrame(errores)

            st.dataframe(
                df_errores,
                width="stretch"
            )

        st.divider()

        st.info(
            "Validación terminada. "
            "No se insertó información en la base de datos."
        )