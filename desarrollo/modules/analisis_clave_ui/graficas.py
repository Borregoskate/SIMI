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
- Respetar el orden cronológico y numérico de los procedimientos.

Este componente:
- No ejecuta SQL.
- No calcula precios.
- No calcula variaciones.
- No clasifica resultados.
- No modifica la información recibida.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import re

import pandas as pd
import streamlit as st


COLUMNAS_PRECIOS = [
    "Inicial",
    "Viable",
    "Subasta",
    "Adjudicación",
]

COLUMNAS_VARIACIONES = [
    "Inicial → Viable",
    "Viable → Subasta",
    "Subasta → Adjudicación",
    "Viable → Adjudicación",
]


def _entero_seguro(valor, default=0):
    """Convierte un valor a entero sin propagar errores."""
    if valor is None:
        return default

    try:
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return default


def _extraer_consecutivo_procedimiento(numero_procedimiento):
    """
    Extrae el consecutivo numérico de un número de procedimiento.

    Ejemplos:
        IM-001-2025 -> 1
        IM-097-2025 -> 97
        PROCEDIMIENTO-15-2026 -> 15

    Cuando no encuentra un consecutivo reconocible, devuelve cero.
    """
    if numero_procedimiento is None:
        return 0

    texto = str(numero_procedimiento).strip().upper()

    if not texto:
        return 0

    # Caso principal: consecutivo situado antes del ejercicio.
    coincidencia = re.search(
        r"(?:^|[-_/ ])(\d+)(?:[-_/ ])\d{4}$",
        texto,
    )

    if coincidencia:
        return int(coincidencia.group(1))

    # Caso alternativo: primer bloque numérico que no sea un año.
    bloques = re.findall(r"\d+", texto)

    for bloque in bloques:
        if len(bloque) != 4:
            return int(bloque)

    return 0


def _extraer_ejercicio(numero_procedimiento, ejercicio):
    """
    Obtiene el ejercicio para ordenar.

    Prioridad:
    1. Campo ejercicio recibido desde el Service.
    2. Año de cuatro dígitos contenido en numero_procedimiento.
    """
    ejercicio_normalizado = _entero_seguro(ejercicio)

    if ejercicio_normalizado > 0:
        return ejercicio_normalizado

    if numero_procedimiento is None:
        return 0

    coincidencias = re.findall(
        r"(?<!\d)(19\d{2}|20\d{2}|21\d{2})(?!\d)",
        str(numero_procedimiento),
    )

    if coincidencias:
        return int(coincidencias[-1])

    return 0


def _construir_etiqueta_procedimiento(item):
    """
    Construye la etiqueta visible del procedimiento.

    No agrega nuevamente el ejercicio cuando ya forma parte del número
    de procedimiento, evitando etiquetas como IM-001-2025 — 2025.
    """
    numero_procedimiento = item.get("numero_procedimiento")

    etiqueta = (
        str(numero_procedimiento).strip()
        if numero_procedimiento
        else f"Procedimiento {item.get('id_procedimiento', '')}"
    )

    ejercicio = _extraer_ejercicio(
        numero_procedimiento,
        item.get("ejercicio"),
    )

    if ejercicio > 0 and str(ejercicio) not in etiqueta:
        etiqueta = f"{etiqueta} — {ejercicio}"

    return etiqueta


def _llave_orden_procedimiento(item):
    """
    Construye la llave de orden jerárquico:

    1. Ejercicio.
    2. Consecutivo numérico del procedimiento.
    3. Número de procedimiento como desempate.
    4. ID interno como último desempate.
    """
    numero_procedimiento = item.get("numero_procedimiento")

    return (
        _extraer_ejercicio(
            numero_procedimiento,
            item.get("ejercicio"),
        ),
        _extraer_consecutivo_procedimiento(numero_procedimiento),
        str(numero_procedimiento or ""),
        _entero_seguro(item.get("id_procedimiento")),
    )


def _convertir_columnas_numericas(dataframe, columnas):
    """
    Convierte Decimal, enteros, flotantes y textos numéricos a valores
    compatibles con las gráficas de Streamlit.
    """
    for columna in columnas:
        if columna in dataframe.columns:
            dataframe[columna] = pd.to_numeric(
                dataframe[columna],
                errors="coerce",
            )

    return dataframe


def _ordenar_y_limpiar_dataframe(
    dataframe,
    columnas_numericas,
):
    """
    Ordena por la jerarquía definida y elimina columnas auxiliares.

    También elimina filas que no contienen ningún dato numérico para
    evitar categorías vacías en las gráficas.
    """
    if dataframe.empty:
        return dataframe

    dataframe = _convertir_columnas_numericas(
        dataframe,
        columnas_numericas,
    )

    dataframe = dataframe.sort_values(
        by=[
            "_orden_ejercicio",
            "_orden_consecutivo",
            "_orden_texto",
            "_orden_id",
        ],
        kind="stable",
    )

    dataframe = dataframe.dropna(
        how="all",
        subset=columnas_numericas,
    )

    return dataframe.drop(
        columns=[
            "_orden_ejercicio",
            "_orden_consecutivo",
            "_orden_texto",
            "_orden_id",
        ]
    ).reset_index(drop=True)


def _dataframe_historial(registros):
    """Prepara y ordena los datos para la gráfica de precios."""
    filas = []

    for registro in registros or []:
        item = dict(registro)
        orden = _llave_orden_procedimiento(item)

        filas.append(
            {
                "_orden_ejercicio": orden[0],
                "_orden_consecutivo": orden[1],
                "_orden_texto": orden[2],
                "_orden_id": orden[3],
                "Procedimiento": _construir_etiqueta_procedimiento(
                    item
                ),
                "Inicial": item.get("mejor_precio_inicial"),
                "Viable": item.get("mejor_precio_viable"),
                "Subasta": item.get("mejor_precio_subasta"),
                "Adjudicación": item.get(
                    "precio_adjudicado_ponderado"
                ),
            }
        )

    dataframe = pd.DataFrame(filas)

    return _ordenar_y_limpiar_dataframe(
        dataframe=dataframe,
        columnas_numericas=COLUMNAS_PRECIOS,
    )


def _dataframe_variaciones(registros):
    """Prepara y ordena los datos para la gráfica de variaciones."""
    filas = []

    for registro in registros or []:
        item = dict(registro)
        orden = _llave_orden_procedimiento(item)

        filas.append(
            {
                "_orden_ejercicio": orden[0],
                "_orden_consecutivo": orden[1],
                "_orden_texto": orden[2],
                "_orden_id": orden[3],
                "Procedimiento": _construir_etiqueta_procedimiento(
                    item
                ),
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

    dataframe = pd.DataFrame(filas)

    return _ordenar_y_limpiar_dataframe(
        dataframe=dataframe,
        columnas_numericas=COLUMNAS_VARIACIONES,
    )


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

    dataframe["Procedimientos"] = pd.to_numeric(
        dataframe["Procedimientos"],
        errors="coerce",
    ).fillna(0)

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