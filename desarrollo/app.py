"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

app.py

Archivo principal de la aplicación Streamlit.

Autor: Jorge Saavedra
Versión: 1.4.0
==============================================================
"""

import streamlit as st

from config.config import (
    APP_NAME,
    APP_DESCRIPTION,
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    SIDEBAR,
)

from modules.dashboard import mostrar_dashboard
from modules.analisis_clave import mostrar_analisis_clave
from modules.carga_universo import mostrar_carga_universo
from modules.carga_propuestas import mostrar_carga_propuestas
from modules.carga_evaluacion import mostrar_carga_evaluacion
from modules.carga_subasta import mostrar_carga_subasta
from modules.carga_adjudicaciones import (
    mostrar_carga_adjudicaciones,
)


# ==========================================================
# OPCIONES DEL MENÚ
# ==========================================================

OPCION_DASHBOARD = "Dashboard Ejecutivo"
OPCION_ANALISIS_CLAVE = "Análisis por Clave"

OPCION_CARGA_UNIVERSO = (
    "Carga 1 — Universo del Procedimiento"
)
OPCION_CATEGORIAS = "Categorías"
OPCION_CLAVES = "Claves"
OPCION_PROVEEDORES = "Proveedores"
OPCION_CARGA_PROPUESTAS = (
    "Carga 2 - Propuestas Iniciales"
)
OPCION_CARGA_EVALUACION = (
    "Carga 3 - Evaluación Técnica"
)
OPCION_CARGA_SUBASTA = (
    "Carga 4 - Subasta Privada"
)
OPCION_CARGA_ADJUDICACIONES = (
    "Carga 5 - Adjudicaciones"
)


def configurar_pagina():
    """Configura la página principal de Streamlit."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=SIDEBAR,
    )


def mostrar_encabezado():
    """Muestra el encabezado general del sistema."""
    st.title(APP_NAME)
    st.caption(APP_DESCRIPTION)


def mostrar_menu():
    """Muestra el menú lateral principal."""
    return st.sidebar.selectbox(
        "Selecciona un módulo",
        [
            OPCION_DASHBOARD,
            OPCION_ANALISIS_CLAVE,
            OPCION_CARGA_UNIVERSO,
            OPCION_CATEGORIAS,
            OPCION_CLAVES,
            OPCION_PROVEEDORES,
            OPCION_CARGA_PROPUESTAS,
            OPCION_CARGA_EVALUACION,
            OPCION_CARGA_SUBASTA,
            OPCION_CARGA_ADJUDICACIONES,
        ],
    )


def ejecutar_modulo(opcion):
    """Ejecuta el módulo seleccionado."""
    if opcion == OPCION_DASHBOARD:
        mostrar_dashboard()

    elif opcion == OPCION_ANALISIS_CLAVE:
        mostrar_analisis_clave()

    elif opcion == OPCION_CARGA_UNIVERSO:
        mostrar_carga_universo()

    elif opcion == OPCION_CATEGORIAS:
        st.info("Módulo de categorías ya existente.")

    elif opcion == OPCION_CLAVES:
        st.info("Módulo de claves ya existente.")

    elif opcion == OPCION_PROVEEDORES:
        st.info("Módulo de proveedores ya existente.")

    elif opcion == OPCION_CARGA_PROPUESTAS:
        mostrar_carga_propuestas()

    elif opcion == OPCION_CARGA_EVALUACION:
        mostrar_carga_evaluacion()

    elif opcion == OPCION_CARGA_SUBASTA:
        mostrar_carga_subasta()

    elif opcion == OPCION_CARGA_ADJUDICACIONES:
        mostrar_carga_adjudicaciones()


def main():
    """Función principal de la aplicación."""
    configurar_pagina()
    mostrar_encabezado()

    opcion = mostrar_menu()
    ejecutar_modulo(opcion)


if __name__ == "__main__":
    main()