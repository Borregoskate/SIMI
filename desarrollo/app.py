"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

app.py

Archivo principal de la aplicación Streamlit.

Autor: Jorge Saavedra
Versión: 1.0.0
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


if __name__ == "__main__":
    main()