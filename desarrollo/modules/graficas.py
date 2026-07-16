"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

graficas.py

Componente visual de gráficas para Análisis por Clave.

Responsabilidades:
- Mostrar la evolución de precios por procedimiento.
- Mostrar variaciones económicas por procedimiento.
- Mostrar la distribución de estados analíticos.

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


def _dataframe_historial(registros):
    """Prepara datos numéricos para la gráfica de precios."""
    filas = []

    for registro in registros or []:
        item = dict(registro)

        etiqueta = (
            item.get("numero_procedimiento")
            or f"Procedimiento {item.get('id_procedimiento', '')}"
        )

        if item.get("ejercicio") is not None:
            etiqueta = f"{etiqueta} — {item.get('ejercicio')}"

        filas.append(
            {
                "Procedimiento": etiqueta,
                "Inicial": item.get("mejor_precio_inicial"),
                "Viable": item.get("mejor_precio_viable"),
                "Subasta": item.get("mejor_precio_subasta"),
                "Adjudicación": item.get(
                    "precio_adjudicado_ponderado"
                ),
            }
        )

    return pd.DataFrame(filas)


def _dataframe_variaciones(registros):
    """Prepara datos numéricos para la gráfica de variaciones."""
    filas = []

    for registro in registros or []:
        item = dict(registro)

        etiqueta = (
            item.get("numero_procedimiento")
            or f"Procedimiento {item.get('id_procedimiento', '')}"
        )

        if item.get("ejercicio") is not None:
            etiqueta = f"{etiqueta} — {item.get('ejercicio')}"

        filas.append(
            {
                "Procedimiento": etiqueta,
                "Inicial → Viable": item.get(
                    "variacion_inicial_viable"
                ),
                "Viable → Subasta": item.get(
                    "variacion_viable_subasta"
                ),
                "Subasta → Adjudicación": item.get(
                    "variacion_subasta_adjudicacion"
                ),
                "Viable → Adjudicación": item.get(
                    "variacion_viable_adjudicacion"
                ),
            }
        )

    return pd.DataFrame(filas)


def _dataframe_estados(registros):
    """Prepara datos para la gráfica de estados."""
    filas = []

    for registro in registros or []:
        item = dict(registro)

        filas.append(
            {
                "Estado": item.get(
                    "estado_analitico",
                    "SIN INFORMACIÓN",
                ),
                "Procedimientos": item.get(
                    "total_procedimientos",
                    0,
                ),
            }
        )

    dataframe = pd.DataFrame(filas)

    if dataframe.empty:
        return dataframe

    return dataframe[
        dataframe["Procedimientos"] > 0
    ].reset_index(drop=True)


def mostrar_graficas_analisis_clave(resultado):
    """Muestra las gráficas analíticas de la clave."""
    resultado = resultado or {}
    graficas = resultado.get("graficas", {}) or {}

    historial = graficas.get("historial_precios", []) or []
    variaciones = (
        graficas.get("variaciones_por_procedimiento", [])
        or []
    )
    estados = (
        graficas.get("procedimientos_por_estado", [])
        or []
    )

    st.subheader("Visualización analítica")

    tab_precios, tab_variaciones, tab_estados = st.tabs(
        [
            "Evolución de precios",
            "Variaciones",
            "Estados",
        ]
    )

    with tab_precios:
        dataframe = _dataframe_historial(historial)

        if dataframe.empty:
            st.info(
                "No existen precios suficientes para generar "
                "la gráfica."
            )
        else:
            dataframe = dataframe.set_index("Procedimiento")
            st.line_chart(
                dataframe,
                use_container_width=True,
            )

    with tab_variaciones:
        dataframe = _dataframe_variaciones(variaciones)

        if dataframe.empty:
            st.info(
                "No existen variaciones suficientes para generar "
                "la gráfica."
            )
        else:
            dataframe = dataframe.set_index("Procedimiento")
            st.bar_chart(
                dataframe,
                use_container_width=True,
            )

    with tab_estados:
        dataframe = _dataframe_estados(estados)

        if dataframe.empty:
            st.info(
                "No existen estados analíticos para representar."
            )
        else:
            dataframe = dataframe.set_index("Estado")
            st.bar_chart(
                dataframe,
                use_container_width=True,
            )
