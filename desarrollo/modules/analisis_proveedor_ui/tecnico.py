"""Visualización del desempeño técnico del proveedor."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import (
    dataframe_desde_registros,
    formatear_entero,
    formatear_porcentaje,
)


def mostrar_desempeno_tecnico(resultado):
    tecnico = (resultado or {}).get("desempeno_tecnico", {}) or {}
    columnas = st.columns(4)
    columnas[0].metric("Evaluaciones", formatear_entero(tecnico.get("total_evaluaciones")))
    columnas[1].metric("Positivas", formatear_entero(tecnico.get("evaluaciones_positivas")))
    columnas[2].metric("Negativas", formatear_entero(tecnico.get("evaluaciones_negativas")))
    columnas[3].metric("Aprobación", formatear_porcentaje(tecnico.get("porcentaje_aprobacion")))

    st.subheader("Claves descartadas por evaluación")
    descartadas = ((resultado or {}).get("tablas", {}) or {}).get("claves_descartadas", []) or []
    df = dataframe_desde_registros(
        descartadas,
        ["numero_procedimiento", "ejercicio", "clave", "descripcion_clave", "resultado_tecnico"],
    )
    if df.empty:
        st.info("No existen evaluaciones técnicas negativas para los filtros aplicados.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
