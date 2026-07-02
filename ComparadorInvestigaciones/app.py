"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo Principal (app.py)

Versión: 1.0.0
Autor: Jorge Saavedra / OpenAI
==============================================================
"""

import streamlit as st
from config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    SIDEBAR,
    APP_NAME,
    APP_DESCRIPTION,
    VERSION
)

from modules.analisis_desiertas import mostrar_analisis_desiertas

# ==============================
# Configuración de la página
# ==============================

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR
)

# ==============================
# Importación de módulos
# ==============================

from modules.carga import cargar_investigaciones
from modules.resumen import mostrar_resumen
from modules.analisis_claves import mostrar_analisis_clave
from modules.analisis_proveedores import mostrar_analisis_proveedor

# ==============================
# Encabezado
# ==============================

st.title(f"{PAGE_ICON} {APP_NAME}")
st.subheader(APP_DESCRIPTION)

st.markdown("---")

# ==============================
# Carga de archivos
# ==============================

investigaciones_df = cargar_investigaciones()

# Si todavía no existen datos no continúa
if investigaciones_df is None:

    st.info(
        "👆 Carga una o más investigaciones de mercado "
        "para comenzar el análisis."
    )

    st.stop()

# ==============================
# Menú principal
# ==============================

tab_resumen, tab_claves, tab_proveedores, tab_desiertas = st.tabs(
    [
        "📊 Resumen General",
        "🔑 Análisis por Clave",
        "🏢 Análisis por Proveedor",
        "🚫 Claves Desiertas"
    ]
)

# ==============================
# Pestaña Resumen
# ==============================

with tab_resumen:

    mostrar_resumen(investigaciones_df)

# ==============================
# Pestaña Claves
# ==============================

with tab_claves:

    mostrar_analisis_clave(investigaciones_df)

# ==============================
# Pestaña Proveedores
# ==============================

with tab_proveedores:

    mostrar_analisis_proveedor(investigaciones_df)

# ==============================
# Pestaña Desiertas
# ==============================

with tab_desiertas:
    mostrar_analisis_desiertas(investigaciones_df)

# ==============================
# Pie de página
# ==============================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("SIMI v1.0.0")

with col2:
    st.caption("© 2026 Jorge Saavedra")

with col3:
    st.caption(f"{APP_NAME} v{VERSION}")