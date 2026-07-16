"""Controlador principal del módulo Streamlit Análisis por Proveedor."""

import streamlit as st

from modules.analisis_proveedor_ui.competencia import mostrar_competencia
from modules.analisis_proveedor_ui.economia import mostrar_desempeno_economico
from modules.analisis_proveedor_ui.filtros import mostrar_filtros_analisis_proveedor
from modules.analisis_proveedor_ui.graficas import mostrar_graficas_proveedor
from modules.analisis_proveedor_ui.historial import mostrar_historial_proveedor
from modules.analisis_proveedor_ui.indicadores import mostrar_indicadores_proveedor
from modules.analisis_proveedor_ui.participacion import mostrar_participacion
from modules.analisis_proveedor_ui.tecnico import mostrar_desempeno_tecnico
from services.analisis_proveedor_service import AnalisisProveedorService


def _mostrar_encabezado():
    st.header("Análisis por Proveedor")
    st.caption(
        "Inteligencia comercial, técnica, económica y competitiva de un proveedor."
    )


def _mostrar_informacion_proveedor(resultado):
    proveedor = (resultado or {}).get("proveedor", {}) or {}
    st.subheader("Información del proveedor")
    columna_1, columna_2 = st.columns([2, 1])
    columna_1.markdown("**Razón social**")
    columna_1.write(proveedor.get("razon_social") or "Sin información")
    columna_2.metric("RFC", proveedor.get("rfc") or "Sin información")


def _tiene_informacion(resultado):
    tablas = (resultado or {}).get("tablas", {}) or {}
    return any(
        tablas.get(nombre)
        for nombre in (
            "participacion_operativa",
            "historial_adjudicaciones",
            "competidores",
        )
    )


def _mostrar_contenido(resultado):
    _mostrar_informacion_proveedor(resultado)
    st.divider()
    mostrar_indicadores_proveedor(resultado)
    st.divider()

    participacion, economia, tecnico, competencia, historial = st.tabs(
        [
            "Participación",
            "Desempeño económico",
            "Desempeño técnico",
            "Competencia",
            "Historial",
        ]
    )
    with participacion:
        mostrar_participacion(resultado)
    with economia:
        mostrar_desempeno_economico(resultado)
    with tecnico:
        mostrar_desempeno_tecnico(resultado)
    with competencia:
        mostrar_competencia(resultado)
    with historial:
        mostrar_historial_proveedor(resultado)

    st.divider()
    st.subheader("Visualización analítica")
    mostrar_graficas_proveedor(resultado)

    limitaciones = resultado.get("limitaciones", {}) or {}
    if not limitaciones.get("tipo_procedimiento_disponible", True):
        st.info(limitaciones.get("mensaje_tipo_procedimiento"))


def mostrar_analisis_proveedor():
    _mostrar_encabezado()
    service = AnalisisProveedorService()

    try:
        filtros = mostrar_filtros_analisis_proveedor(service)
    except Exception as error:
        st.error("No fue posible cargar los filtros del análisis por proveedor.")
        st.exception(error)
        return

    if filtros is None:
        st.info("No existen proveedores disponibles para realizar el análisis.")
        return

    try:
        resultado = service.obtener_analisis_proveedor(**filtros)
    except ValueError as error:
        st.warning(str(error))
        return
    except Exception as error:
        st.error("No fue posible consultar el análisis del proveedor seleccionado.")
        st.exception(error)
        return

    if not resultado:
        st.info("No se encontró información para los filtros seleccionados.")
        return

    if not _tiene_informacion(resultado):
        _mostrar_informacion_proveedor(resultado)
        st.info("El proveedor existe, pero no cuenta con información analítica para los filtros aplicados.")
        return

    st.divider()
    _mostrar_contenido(resultado)
