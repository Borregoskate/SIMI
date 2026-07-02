"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

config.py

Configuración global del sistema.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

# ==========================================================
# INFORMACIÓN DEL SISTEMA
# ==========================================================

APP_NAME = "SIMI"

APP_DESCRIPTION = (
    "Sistema Inteligente de Mercado e Investigaciones"
)

VERSION = "1.0.0"

AUTHOR = "Jorge Saavedra"

YEAR = "2026"


# ==========================================================
# STREAMLIT
# ==========================================================

PAGE_TITLE = f"{APP_NAME} | {APP_DESCRIPTION}"

PAGE_ICON = "📊"

LAYOUT = "wide"

SIDEBAR = "expanded"


# ==========================================================
# ARCHIVOS PERMITIDOS
# ==========================================================

SUPPORTED_FILES = [
    "xlsx",
    "xls"
]

MAX_UPLOAD_FILES = 100


# ==========================================================
# COLUMNAS ESTÁNDAR
# ==========================================================

STANDARD_COLUMNS = [
    "RFC",
    "RAZON SOCIAL",
    "CLAVE",
    "DESCRIPCION",
    "CANTIDAD OFERTADA",
    "PAIS DE ORIGEN",
    "PRECIO UNITARIO"
]


# ==========================================================
# COLORES DEL SISTEMA
# ==========================================================

COLOR_PRIMARY = "#005A9C"

COLOR_SUCCESS = "#2E8B57"

COLOR_WARNING = "#FFA500"

COLOR_ERROR = "#C62828"


# ==========================================================
# EXPORTACIONES
# ==========================================================

EXPORT_EXCEL_NAME = "SIMI_Analisis.xlsx"

EXPORT_SHEET_CLAVES = "Analisis Claves"

EXPORT_SHEET_PROVEEDORES = "Analisis Proveedores"

EXPORT_SHEET_RESUMEN = "Resumen"


# ==========================================================
# FORMATO
# ==========================================================

DECIMALES = 2

FORMATO_MONEDA = "${:,.2f}"

FORMATO_PORCENTAJE = "{:.2f}%"


# ==========================================================
# CACHE
# ==========================================================

CACHE_TTL = 3600


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = "INFO"


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

MENU = [

    "Resumen",

    "Claves",

    "Proveedores"

]