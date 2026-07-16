"""Visualización de participación operativa y por ejercicio."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import dataframe_desde_registros


def mostrar_participacion(resultado):
    tablas = (resultado or {}).get("tablas", {}) or {}
    participacion = tablas.get("participacion_operativa", []) or []
    ejercicios = tablas.get("participacion_por_ejercicio", []) or []

    st.subheader("Participación por ejercicio")
    df_ejercicios = dataframe_desde_registros(
        ejercicios,
        [
            "etiqueta_ejercicio",
            "procedimientos_participados",
            "claves_ofertadas",
            "evaluaciones_positivas",
            "evaluaciones_negativas",
            "claves_adjudicadas_operativas",
            "adjudicaciones_historicas",
            "valor_adjudicado_total",
        ],
    )
    if df_ejercicios.empty:
        st.info("No existe información de participación por ejercicio.")
    else:
        st.dataframe(df_ejercicios, width="stretch", hide_index=True)

    st.subheader("Detalle operativo por procedimiento y clave")
    df = dataframe_desde_registros(
        participacion,
        [
            "numero_procedimiento",
            "ejercicio",
            "clave",
            "descripcion_clave",
            "resultado_tecnico",
            "estado_participacion",
            "cantidad_inicial",
            "precio_inicial",
            "cantidad_subasta",
            "precio_subasta",
            "cantidad_adjudicada",
            "precio_adjudicado",
        ],
    )
    if df.empty:
        st.info("No existen participaciones operativas para los filtros aplicados.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
