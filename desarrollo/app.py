"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

app.py

Punto de entrada principal del sistema.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st

from config.config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    SIDEBAR
)

from core.session import inicializar_sesion
from modules.dashboard import mostrar_dashboard
from modules.procedimientos import mostrar_procedimientos
from modules.investigaciones import mostrar_investigaciones
from modules.evaluacion import mostrar_evaluacion
from modules.subasta import mostrar_subasta
from modules.adjudicaciones import mostrar_adjudicaciones
from modules.historicos import mostrar_historicos
from modules.catalogos import mostrar_catalogos
from modules.usuarios import mostrar_usuarios
from modules.reportes import mostrar_reportes
from modules.configuracion import mostrar_configuracion

from modules.carga import mostrar_pantalla_carga_archivos

mostrar_pantalla_carga_archivos()


def configurar_pagina():
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=SIDEBAR
    )


def mostrar_menu():
    st.sidebar.title("SIMI")
    st.sidebar.caption("Sistema Inteligente de Mercado e Investigaciones")

    return st.sidebar.radio(
        "Menú principal",
        [
            "Dashboard",
            "Procedimientos",
            "Investigaciones",
            "Evaluación técnica",
            "Subasta privada",
            "Adjudicaciones",
            "Históricos",
            "Catálogos",
            "Usuarios",
            "Reportes",
            "Configuración"
        ]
    )


def main():
    configurar_pagina()
    inicializar_sesion()

    opcion = mostrar_menu()

    if opcion == "Dashboard":
        mostrar_dashboard()

    elif opcion == "Procedimientos":
        mostrar_procedimientos()

    elif opcion == "Investigaciones":
        mostrar_investigaciones()

    elif opcion == "Evaluación técnica":
        mostrar_evaluacion()

    elif opcion == "Subasta privada":
        mostrar_subasta()

    elif opcion == "Adjudicaciones":
        mostrar_adjudicaciones()

    elif opcion == "Históricos":
        mostrar_historicos()

    elif opcion == "Catálogos":
        mostrar_catalogos()

    elif opcion == "Usuarios":
        mostrar_usuarios()

    elif opcion == "Reportes":
        mostrar_reportes()

    elif opcion == "Configuración":
        mostrar_configuracion()


if __name__ == "__main__":
    main()