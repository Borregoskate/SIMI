"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

resumen.py

Componente visual del resumen por procedimiento para
Análisis por Clave.

Responsabilidades:
- Mostrar la tabla analítica por procedimiento.
- Mostrar precios, variaciones, estados y clasificaciones
  preparados por AnalisisClaveService.
- Facilitar la comparación entre etapas.

Este componente:
- No ejecuta SQL.
- No calcula precios.
- No calcula variaciones.
- No clasifica estados.
- No modifica la información recibida.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
import streamlit as st

from modules.analisis_clave_ui.utilidades import (
    formatear_entero,
    formatear_moneda,
    formatear_porcentaje,
)


COLUMNAS_RESUMEN = {
    "numero_procedimiento": "Procedimiento",
    "ejercicio": "Ejercicio",
    "estado_analitico": "Estado analítico",
    "total_propuestas_iniciales": "Propuestas iniciales",
    "evaluaciones_positivas": "Evaluaciones positivas",
    "evaluaciones_negativas": "Evaluaciones negativas",
    "total_subastas": "Subastas",
    "proveedores_adjudicados": "Proveedores adjudicados",
    "mejor_precio_inicial": "Mejor precio inicial",
    "mejor_precio_viable": "Mejor precio viable",
    "mejor_precio_subasta": "Mejor precio subasta",
    "precio_adjudicado_ponderado": "Precio adjudicado ponderado",
    "variacion_inicial_viable": "Variación Inicial → Viable",
    "variacion_viable_subasta": "Variación Viable → Subasta",
    "variacion_subasta_adjudicacion": (
        "Variación Subasta → Adjudicación"
    ),
    "variacion_viable_adjudicacion": (
        "Variación Viable → Adjudicación"
    ),
    "clasificacion_viable_adjudicacion": (
        "Clasificación Viable → Adjudicación"
    ),
}


def _preparar_dataframe(registros):
    """
    Construye un DataFrame exclusivamente para presentación.

    No altera la lista original recibida.
    """
    filas = []

    for registro in registros or []:
        item = dict(registro)

        fila = {
            "numero_procedimiento": (
                item.get("numero_procedimiento")
                or "Sin procedimiento"
            ),
            "ejercicio": item.get("ejercicio"),
            "estado_analitico": item.get(
                "estado_analitico",
                "SIN INFORMACIÓN",
            ),
            "total_propuestas_iniciales": formatear_entero(
                item.get("total_propuestas_iniciales")
            ),
            "evaluaciones_positivas": formatear_entero(
                item.get("evaluaciones_positivas")
            ),
            "evaluaciones_negativas": formatear_entero(
                item.get("evaluaciones_negativas")
            ),
            "total_subastas": formatear_entero(
                item.get("total_subastas")
            ),
            "proveedores_adjudicados": formatear_entero(
                item.get("proveedores_adjudicados")
            ),
            "mejor_precio_inicial": formatear_moneda(
                item.get("mejor_precio_inicial")
            ),
            "mejor_precio_viable": formatear_moneda(
                item.get("mejor_precio_viable")
            ),
            "mejor_precio_subasta": formatear_moneda(
                item.get("mejor_precio_subasta")
            ),
            "precio_adjudicado_ponderado": formatear_moneda(
                item.get("precio_adjudicado_ponderado")
            ),
            "variacion_inicial_viable": formatear_porcentaje(
                item.get("variacion_inicial_viable")
            ),
            "variacion_viable_subasta": formatear_porcentaje(
                item.get("variacion_viable_subasta")
            ),
            "variacion_subasta_adjudicacion": (
                formatear_porcentaje(
                    item.get(
                        "variacion_subasta_adjudicacion"
                    )
                )
            ),
            "variacion_viable_adjudicacion": (
                formatear_porcentaje(
                    item.get(
                        "variacion_viable_adjudicacion"
                    )
                )
            ),
            "clasificacion_viable_adjudicacion": item.get(
                "clasificacion_viable_adjudicacion",
                "INFORMACIÓN INSUFICIENTE",
            ),
        }

        filas.append(fila)

    dataframe = pd.DataFrame(filas)

    if dataframe.empty:
        return dataframe

    dataframe = dataframe.rename(columns=COLUMNAS_RESUMEN)

    return dataframe


def mostrar_resumen_procedimientos(resultado):
    """
    Muestra la tabla principal del análisis por procedimiento.
    """
    resultado = resultado or {}
    tablas = resultado.get("tablas", {}) or {}
    registros = tablas.get("resumen_procedimientos", []) or []

    st.subheader("Resumen por procedimiento")

    if not registros:
        st.info(
            "No existen procedimientos para los filtros "
            "seleccionados."
        )
        return

    dataframe = _preparar_dataframe(registros)

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Los precios, variaciones, estados y clasificaciones "
        "son calculados previamente por AnalisisClaveService."
    )
