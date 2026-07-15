"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

app.py

Archivo principal de la aplicación Streamlit.

Autor: Jorge Saavedra
Versión: 1.2.0
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

from modules.carga_universo import mostrar_carga_universo
from modules.carga_propuestas import mostrar_carga_propuestas
from modules.carga_evaluacion import mostrar_carga_evaluacion
from modules.carga_subasta import mostrar_carga_subasta
from modules.carga_adjudicaciones import (
    mostrar_carga_adjudicaciones,
)


def configurar_pagina():
    """
    Configura la página principal de Streamlit.
    """

    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=SIDEBAR,
    )


def mostrar_encabezado():
    """
    Muestra el encabezado general del sistema.
    """

    st.title(APP_NAME)
    st.caption(APP_DESCRIPTION)


def mostrar_menu():
    """
    Muestra el menú lateral principal.
    """

    return st.sidebar.selectbox(
        "Selecciona un módulo",
        [
            "Carga 1 — Universo del Procedimiento",
            "Categorías",
            "Claves",
            "Proveedores",
            "Carga 2 - Propuestas Iniciales",
            "Carga 3 - Evaluación Técnica",
            "Carga 4 - Subasta Privada",
            "Carga 5 - Adjudicaciones",
        ],
    )


def main():
    """
    Función principal de la aplicación.
    """

    configurar_pagina()
    mostrar_encabezado()

    opcion = mostrar_menu()

    if opcion == "Carga 1 — Universo del Procedimiento":
        mostrar_carga_universo()

    elif opcion == "Categorías":
        st.info("Módulo de categorías ya existente.")

    elif opcion == "Claves":
        st.info("Módulo de claves ya existente.")

    elif opcion == "Proveedores":
        st.info("Módulo de proveedores ya existente.")

    elif opcion == "Carga 2 - Propuestas Iniciales":
        mostrar_carga_propuestas()

    elif opcion == "Carga 3 - Evaluación Técnica":
        mostrar_carga_evaluacion()

    elif opcion == "Carga 4 - Subasta Privada":
        mostrar_carga_subasta()

    elif opcion == "Carga 5 - Adjudicaciones":
        mostrar_carga_adjudicaciones()


if __name__ == "__main__":
    main()