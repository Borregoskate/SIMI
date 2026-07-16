"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_clave.py

Controlador principal del módulo Streamlit Análisis por Clave.

Responsabilidades:
- Crear AnalisisClaveService.
- Coordinar la selección de filtros.
- Solicitar al Service el análisis completo de la clave.
- Distribuir la respuesta a los componentes visuales.
- Manejar errores y ausencia de información.

Este módulo:
- No ejecuta SQL.
- No abre conexiones.
- No calcula precios, variaciones ni clasificaciones.
- No modifica la información recibida del Service.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import streamlit as st

from modules.analisis_clave_ui.filtros import (
    mostrar_filtros_analisis_clave,
)
from modules.analisis_clave_ui.graficas import (
    mostrar_graficas_analisis_clave,
)
from modules.analisis_clave_ui.historial import (
    mostrar_historial_precios,
)
from modules.analisis_clave_ui.indicadores import (
    mostrar_indicadores_generales,
)
from modules.analisis_clave_ui.proveedores import (
    mostrar_detalle_proveedores,
)
from modules.analisis_clave_ui.resumen import (
    mostrar_resumen_procedimientos,
)
from services.analisis_clave_service import AnalisisClaveService


def _mostrar_encabezado():
    """Muestra el encabezado general del módulo."""
    st.header("Análisis por Clave")
    st.caption(
        "Consulta la evolución económica de una clave desde las "
        "propuestas iniciales hasta la adjudicación."
    )


def _mostrar_informacion_clave(resultado):
    """Muestra la información general de la clave seleccionada."""
    clave = resultado.get("clave", {}) or {}

    if not clave:
        st.warning(
            "No se encontró información general de la clave "
            "seleccionada."
        )
        return

    st.subheader("Información de la clave")

    columna_1, columna_2, columna_3 = st.columns([1, 2, 1])

    columna_1.metric(
        "Clave",
        clave.get("clave", "Sin información"),
    )

    columna_2.markdown("**Descripción**")
    columna_2.write(
        clave.get("descripcion") or "Sin descripción"
    )

    columna_3.metric(
        "Categoría",
        clave.get("categoria") or "Sin categoría",
    )


def _tiene_informacion_analitica(resultado):
    """
    Determina si la respuesta contiene información analítica.

    Esta validación no calcula resultados; solo comprueba si
    existen registros preparados por el Service.
    """
    tablas = resultado.get("tablas", {}) or {}

    return any(
        (
            tablas.get("resumen_procedimientos"),
            tablas.get("detalle_proveedores"),
            tablas.get("historial_precios"),
        )
    )


def _mostrar_contenido(resultado):
    """Distribuye el resultado entre los componentes visuales."""
    _mostrar_informacion_clave(resultado)

    st.divider()
    mostrar_indicadores_generales(resultado)

    st.divider()

    pestana_resumen, pestana_proveedores, pestana_historial = (
        st.tabs(
            [
                "Resumen por procedimiento",
                "Detalle por proveedor",
                "Historial de precios",
            ]
        )
    )

    with pestana_resumen:
        mostrar_resumen_procedimientos(resultado)

    with pestana_proveedores:
        mostrar_detalle_proveedores(resultado)

    with pestana_historial:
        mostrar_historial_precios(resultado)

    st.divider()
    mostrar_graficas_analisis_clave(resultado)


def mostrar_analisis_clave():
    """Renderiza y coordina la pantalla de Análisis por Clave."""
    _mostrar_encabezado()

    service = AnalisisClaveService()

    try:
        filtros = mostrar_filtros_analisis_clave(service)
    except Exception as error:
        st.error(
            "No fue posible cargar los filtros del análisis "
            "por clave."
        )
        st.exception(error)
        return

    if filtros is None:
        st.info(
            "No existen claves disponibles para realizar "
            "el análisis."
        )
        return

    id_clave = filtros.get("id_clave")

    if id_clave is None:
        st.info(
            "Selecciona una clave para consultar su análisis."
        )
        return

    try:
        resultado = service.obtener_analisis_clave(
            id_clave=id_clave,
            id_procedimiento=filtros.get("id_procedimiento"),
            ejercicio=filtros.get("ejercicio"),
        )
    except ValueError as error:
        st.warning(str(error))
        return
    except Exception as error:
        st.error(
            "No fue posible consultar el análisis de la clave "
            "seleccionada."
        )
        st.exception(error)
        return

    if not resultado:
        st.info(
            "No se encontró información para los filtros "
            "seleccionados."
        )
        return

    if not _tiene_informacion_analitica(resultado):
        _mostrar_informacion_clave(resultado)
        st.info(
            "La clave seleccionada existe, pero no cuenta con "
            "información analítica para los filtros aplicados."
        )
        return

    st.divider()
    _mostrar_contenido(resultado)