"""Visualización del desempeño económico por procedimiento y clave."""

import streamlit as st

from modules.analisis_proveedor_ui.utilidades import (
    dataframe_desde_registros,
    formatear_moneda,
    formatear_porcentaje,
)


def _mostrar_extremo(titulo, registro):
    st.markdown(f"**{titulo}**")
    if not registro:
        st.caption("Sin información comparable.")
        return
    st.write(
        f"{registro.get('clave', 'Sin clave')} · "
        f"{registro.get('numero_procedimiento', 'Sin procedimiento')}"
    )
    st.caption(
        f"Variación: {formatear_porcentaje(registro.get('variacion_inicial_subasta'))} · "
        f"Impacto estimado: {formatear_moneda(registro.get('ahorro_estimado_subasta'))}"
    )


def mostrar_desempeno_economico(resultado):
    resumen = (resultado or {}).get("resumen_economico", {}) or {}
    registros = ((resultado or {}).get("tablas", {}) or {}).get("economia_por_clave", []) or []

    st.subheader("Resumen económico por clave")
    izquierda, derecha = st.columns(2)
    with izquierda:
        _mostrar_extremo("Mayor reducción", resumen.get("mayor_reduccion"))
    with derecha:
        _mostrar_extremo("Mayor incremento", resumen.get("mayor_incremento"))

    df = dataframe_desde_registros(
        registros,
        [
            "numero_procedimiento",
            "ejercicio",
            "clave",
            "descripcion_clave",
            "precio_inicial",
            "precio_subasta",
            "precio_adjudicado",
            "variacion_inicial_subasta",
            "clasificacion_inicial_subasta",
            "variacion_subasta_adjudicacion",
            "variacion_inicial_adjudicacion",
            "cantidad_referencia_ahorro",
            "origen_cantidad_ahorro",
            "ahorro_estimado_subasta",
        ],
    )
    if df.empty:
        st.info("No existe información económica para los filtros aplicados.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
