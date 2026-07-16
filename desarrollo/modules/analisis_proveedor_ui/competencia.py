"""Visualización de competencia del proveedor."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import dataframe_desde_registros


def mostrar_competencia(resultado):
    registros = ((resultado or {}).get("tablas", {}) or {}).get("competidores", []) or []
    st.caption(
        "La competencia se calcula únicamente con información operativa y "
        "coincidencias en el mismo procedimiento y clave."
    )
    df = dataframe_desde_registros(
        registros,
        [
            "rfc_competidor",
            "razon_social_competidor",
            "coincidencias",
            "procedimientos_compartidos",
            "claves_compartidas",
            "victorias_proveedor",
            "derrotas_proveedor",
            "adjudicaciones_compartidas",
            "sin_adjudicacion",
            "porcentaje_victorias",
            "porcentaje_derrotas",
        ],
    )
    if df.empty:
        st.info("No existen competidores para los filtros aplicados.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
