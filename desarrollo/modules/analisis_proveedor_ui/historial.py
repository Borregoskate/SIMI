"""Visualización del historial operativo e histórico del proveedor."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import dataframe_desde_registros


def mostrar_historial_proveedor(resultado):
    registros = ((resultado or {}).get("tablas", {}) or {}).get("historial_adjudicaciones", []) or []
    st.caption(
        "Los registros históricos conservan numero_procedimiento como texto y "
        "no se vinculan artificialmente con procedimientos operativos."
    )
    df = dataframe_desde_registros(
        registros,
        [
            "origen_dato",
            "numero_procedimiento",
            "ejercicio",
            "clave",
            "descripcion_clave",
            "cantidad_adjudicada",
            "porcentaje_adjudicado",
            "precio_adjudicado",
            "valor_adjudicado",
        ],
    )
    if df.empty:
        st.info("No existen adjudicaciones para los filtros aplicados.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
