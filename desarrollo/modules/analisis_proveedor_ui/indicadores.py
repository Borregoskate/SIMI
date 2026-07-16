"""Indicadores visuales para Análisis por Proveedor."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import (
    formatear_entero,
    formatear_moneda,
    formatear_porcentaje,
)


def mostrar_indicadores_proveedor(resultado):
    indicadores = (resultado or {}).get("indicadores", {}) or {}
    economico = (resultado or {}).get("resumen_economico", {}) or {}

    st.subheader("Indicadores principales")
    fila_1 = st.columns(6)
    fila_1[0].metric("Procedimientos", formatear_entero(indicadores.get("total_procedimientos_participados")))
    fila_1[1].metric("Claves ofertadas", formatear_entero(indicadores.get("total_claves_ofertadas")))
    fila_1[2].metric("Participaciones", formatear_entero(indicadores.get("total_participaciones_procedimiento_clave")))
    fila_1[3].metric("Claves adjudicadas", formatear_entero(indicadores.get("total_claves_adjudicadas_operativas")))
    fila_1[4].metric("Adjudicaciones históricas", formatear_entero(indicadores.get("total_adjudicaciones_historicas")))
    fila_1[5].metric("Aprobación técnica", formatear_porcentaje(indicadores.get("porcentaje_aprobacion_tecnica")))

    fila_2 = st.columns(6)
    fila_2[0].metric("Evaluaciones positivas", formatear_entero(indicadores.get("total_evaluaciones_positivas")))
    fila_2[1].metric("Evaluaciones negativas", formatear_entero(indicadores.get("total_evaluaciones_negativas")))
    fila_2[2].metric("Reducciones en subasta", formatear_entero(economico.get("claves_con_reduccion")))
    fila_2[3].metric("Sin cambio", formatear_entero(economico.get("claves_sin_cambio")))
    fila_2[4].metric("Incrementos en subasta", formatear_entero(economico.get("claves_con_incremento")))
    fila_2[5].metric("Ahorro estimado", formatear_moneda(economico.get("ahorro_estimado_total")))
