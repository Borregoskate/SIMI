"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

indicadores.py

Componente visual de indicadores para Análisis por Clave.

Responsabilidades:
- Mostrar KPIs generales de la clave.
- Mostrar el estado analítico consolidado.
- Mostrar porcentajes ya calculados por AnalisisClaveService.
- Mostrar precios consolidados ya preparados por el Service.

Este componente:
- No ejecuta SQL.
- No calcula porcentajes.
- No calcula variaciones.
- No clasifica resultados.
- No modifica los datos recibidos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

import streamlit as st

from modules.analisis_clave_ui.utilidades import (
    formatear_entero,
    formatear_moneda,
    formatear_porcentaje,
    obtener_icono_clasificacion,
    obtener_icono_estado,
)


def _obtener_valor(diccionario, clave, default=None):
    """Obtiene un valor de un diccionario de manera segura."""
    if not isinstance(diccionario, dict):
        return default

    return diccionario.get(clave, default)


def mostrar_indicadores_generales(resultado):
    """
    Muestra los indicadores generales del análisis de la clave.

    Parámetros:
        resultado:
            Respuesta completa de
            AnalisisClaveService.obtener_analisis_clave().
    """
    resultado = resultado or {}

    indicadores = resultado.get("indicadores", {}) or {}
    consolidado = resultado.get("consolidado", {}) or {}
    precios = consolidado.get("precios", {}) or {}
    variaciones = consolidado.get("variaciones", {}) or {}

    st.subheader("Indicadores principales")

    fila_1 = st.columns(5)

    fila_1[0].metric(
        "Procedimientos",
        formatear_entero(
            indicadores.get("total_procedimientos")
        ),
    )
    fila_1[1].metric(
        "Proveedores participantes",
        formatear_entero(
            indicadores.get(
                "total_proveedores_participantes"
            )
        ),
    )
    fila_1[2].metric(
        "Propuestas iniciales",
        formatear_entero(
            indicadores.get("total_propuestas_iniciales")
        ),
    )
    fila_1[3].metric(
        "Propuestas de subasta",
        formatear_entero(
            indicadores.get("total_propuestas_subasta")
        ),
    )
    fila_1[4].metric(
        "Proveedores adjudicados",
        formatear_entero(
            indicadores.get(
                "total_proveedores_adjudicados"
            )
        ),
    )

    fila_2 = st.columns(5)

    fila_2[0].metric(
        "Evaluaciones positivas",
        formatear_entero(
            indicadores.get(
                "total_evaluaciones_positivas"
            )
        ),
    )
    fila_2[1].metric(
        "Evaluaciones negativas",
        formatear_entero(
            indicadores.get(
                "total_evaluaciones_negativas"
            )
        ),
    )
    fila_2[2].metric(
        "Aprobación técnica",
        formatear_porcentaje(
            indicadores.get(
                "porcentaje_aprobacion_tecnica"
            )
        ),
    )
    fila_2[3].metric(
        "Procedimientos adjudicados",
        formatear_entero(
            indicadores.get(
                "total_procedimientos_adjudicados"
            )
        ),
    )
    fila_2[4].metric(
        "% procedimientos adjudicados",
        formatear_porcentaje(
            indicadores.get(
                "porcentaje_procedimientos_adjudicados"
            )
        ),
    )

    st.divider()

    estado = consolidado.get(
        "estado_analitico",
        indicadores.get(
            "estado_analitico_consolidado",
            "SIN INFORMACIÓN",
        ),
    )

    st.subheader("Estado analítico consolidado")

    st.info(
        f"{obtener_icono_estado(estado)} {estado}"
    )

    st.subheader("Precios consolidados")

    fila_3 = st.columns(4)

    fila_3[0].metric(
        "Mejor precio inicial",
        formatear_moneda(
            precios.get("mejor_precio_inicial")
        ),
    )
    fila_3[1].metric(
        "Mejor precio viable",
        formatear_moneda(
            precios.get("mejor_precio_viable")
        ),
        delta=formatear_porcentaje(
            variaciones.get("variacion_inicial_viable")
        ),
        delta_color="inverse",
    )
    fila_3[2].metric(
        "Mejor precio de subasta",
        formatear_moneda(
            precios.get("mejor_precio_subasta")
        ),
        delta=formatear_porcentaje(
            variaciones.get("variacion_viable_subasta")
        ),
        delta_color="inverse",
    )
    fila_3[3].metric(
        "Precio adjudicado ponderado",
        formatear_moneda(
            precios.get("precio_adjudicado_ponderado")
        ),
        delta=formatear_porcentaje(
            variaciones.get(
                "variacion_viable_adjudicacion"
            )
        ),
        delta_color="inverse",
    )

    clasificacion = variaciones.get(
        "clasificacion_viable_adjudicacion",
        "INFORMACIÓN INSUFICIENTE",
    )

    st.caption(
        f"{obtener_icono_clasificacion(clasificacion)} "
        f"Clasificación consolidada Viable → Adjudicación: "
        f"{clasificacion}"
    )
