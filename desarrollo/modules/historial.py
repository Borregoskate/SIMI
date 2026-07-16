"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

historial.py

Componente visual del historial de precios para
Análisis por Clave.

Responsabilidades:
- Mostrar la evolución histórica por procedimiento.
- Mostrar precios por etapa y precio adjudicado ponderado.
- Mostrar la variación viable contra adjudicación.

Este componente:
- No ejecuta SQL.
- No calcula precios.
- No calcula variaciones.
- No clasifica resultados.
- No modifica la información recibida.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
import streamlit as st

from modules.analisis_clave_ui.utilidades import (
    formatear_moneda,
    formatear_numero,
    formatear_porcentaje,
)


COLUMNAS_HISTORIAL = {
    "numero_procedimiento": "Procedimiento",
    "ejercicio": "Ejercicio",
    "mejor_precio_inicial": "Mejor precio inicial",
    "mejor_precio_viable": "Mejor precio viable",
    "mejor_precio_subasta": "Mejor precio subasta",
    "precio_adjudicado_ponderado": "Precio adjudicado ponderado",
    "cantidad_total_adjudicada": "Cantidad adjudicada",
    "variacion_viable_adjudicacion": (
        "Variación Viable → Adjudicación"
    ),
    "clasificacion_viable_adjudicacion": "Clasificación",
}


def _preparar_dataframe(registros):
    """Construye el DataFrame visual del historial."""
    filas = []

    for registro in registros or []:
        item = dict(registro)

        filas.append(
            {
                "numero_procedimiento": (
                    item.get("numero_procedimiento")
                    or "Sin procedimiento"
                ),
                "ejercicio": item.get("ejercicio"),
                "mejor_precio_inicial": formatear_moneda(
                    item.get("mejor_precio_inicial")
                ),
                "mejor_precio_viable": formatear_moneda(
                    item.get("mejor_precio_viable")
                ),
                "mejor_precio_subasta": formatear_moneda(
                    item.get("mejor_precio_subasta")
                ),
                "precio_adjudicado_ponderado": (
                    formatear_moneda(
                        item.get(
                            "precio_adjudicado_ponderado"
                        )
                    )
                ),
                "cantidad_total_adjudicada": formatear_numero(
                    item.get("cantidad_total_adjudicada")
                ),
                "variacion_viable_adjudicacion": (
                    formatear_porcentaje(
                        item.get(
                            "variacion_viable_adjudicacion"
                        )
                    )
                ),
                "clasificacion_viable_adjudicacion": (
                    item.get(
                        "clasificacion_viable_adjudicacion"
                    )
                    or "INFORMACIÓN INSUFICIENTE"
                ),
            }
        )

    dataframe = pd.DataFrame(filas)

    if dataframe.empty:
        return dataframe

    return dataframe.rename(columns=COLUMNAS_HISTORIAL)


def mostrar_historial_precios(resultado):
    """Muestra la tabla histórica de precios."""
    resultado = resultado or {}
    tablas = resultado.get("tablas", {}) or {}
    registros = tablas.get("historial_precios", []) or []

    st.subheader("Historial de precios")

    if not registros:
        st.info(
            "No existe historial de precios para los filtros "
            "seleccionados."
        )
        return

    dataframe = _preparar_dataframe(registros)

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
    )
