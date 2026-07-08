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
        "Esta pantalla valida el archivo cargado. "
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
        mensajes = resultado.get("mensajes", [])
        resumen = resultado.get("resumen", {})

        errores = resumen.get("errores", 0)
        advertencias = resumen.get("advertencias", 0)
        informativos = resumen.get("informativos", 0)
        total_registros = resumen.get("total_registros", 0)
        claves_unicas = resumen.get("claves_unicas", 0)
        duplicados_clave = resumen.get("duplicados_clave", 0)

        st.divider()

        if valido:
            st.success("Archivo validado correctamente. Está listo para importación futura.")
        else:
            st.error("El archivo contiene errores críticos. No debe guardarse en base de datos.")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Registros válidos", total_registros)

        with col2:
            st.metric("Claves únicas", claves_unicas)

        with col3:
            st.metric("Duplicados de clave", duplicados_clave)

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric("Errores", errores)

        with col5:
            st.metric("Advertencias", advertencias)

        with col6:
            st.metric("Informativos", informativos)

        st.divider()

        if not datos.empty:
            st.subheader("Vista previa de datos validados")
            st.dataframe(
                datos,
                width="stretch"
            )
        else:
            st.warning("No se encontraron registros válidos para mostrar.")

        if mensajes:
            st.subheader("Reporte de validación")

            df_mensajes = pd.DataFrame(mensajes)

            columnas_orden = [
                "nivel",
                "fila",
                "campo",
                "valor",
                "mensaje"
            ]

            columnas_existentes = [
                columna for columna in columnas_orden
                if columna in df_mensajes.columns
            ]

            df_mensajes = df_mensajes[columnas_existentes]

            st.dataframe(
                df_mensajes,
                width="stretch"
            )

        st.divider()

        st.info(
            "Validación terminada. "
            "No se insertó información en la base de datos."
        )