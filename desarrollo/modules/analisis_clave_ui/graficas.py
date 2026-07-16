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
- Respetar explícitamente el orden cronológico y numérico
  de los procedimientos en el eje X.

Este componente:
- No ejecuta SQL.
- No calcula precios.
- No calcula variaciones.
- No clasifica resultados.
- No modifica la información recibida.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

import re

import altair as alt
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


def _extraer_ejercicio(numero_procedimiento, ejercicio):
    """
    Obtiene el ejercicio para ordenar.

    Prioridad:
    1. Campo ejercicio recibido desde el Service.
    2. Último año de cuatro dígitos contenido en numero_procedimiento.
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


def _extraer_consecutivo_procedimiento(numero_procedimiento):
    """
    Extrae el consecutivo numérico principal del procedimiento.

    Ejemplos:
        IM-001-2025 -> 1
        IM-097-2025 -> 97
        IM-041-2026 -> 41

    Si no encuentra el patrón principal, usa el primer bloque numérico
    que no represente un año.
    """
    if numero_procedimiento is None:
        return 0

    texto = str(numero_procedimiento).strip().upper()

    if not texto:
        return 0

    coincidencia = re.search(
        r"(?:^|[-_/ ])(\d+)(?:[-_/ ])(?:19|20|21)\d{2}$",
        texto,
    )

    if coincidencia:
        return int(coincidencia.group(1))

    bloques = re.findall(r"\d+", texto)

    for bloque in bloques:
        numero = int(bloque)

        if not (
            len(bloque) == 4
            and 1900 <= numero <= 2199
        ):
            return numero

    return 0


def _construir_etiqueta_procedimiento(item):
    """
    Construye la etiqueta visible del procedimiento.

    No duplica el ejercicio cuando ya está incluido en el texto.
    """
    numero_procedimiento = item.get("numero_procedimiento")

    if numero_procedimiento:
        etiqueta = str(numero_procedimiento).strip()
    else:
        etiqueta = (
            f"Procedimiento "
            f"{item.get('id_procedimiento', '')}"
        ).strip()

    ejercicio = _extraer_ejercicio(
        numero_procedimiento,
        item.get("ejercicio"),
    )

    if ejercicio > 0 and str(ejercicio) not in etiqueta:
        etiqueta = f"{etiqueta} — {ejercicio}"

    return etiqueta


def _llave_orden_procedimiento(item):
    """
    Define el orden jerárquico del procedimiento:

    1. Ejercicio.
    2. Consecutivo numérico.
    3. Número de procedimiento.
    4. ID interno.
    """
    numero_procedimiento = item.get("numero_procedimiento")

    return (
        _extraer_ejercicio(
            numero_procedimiento,
            item.get("ejercicio"),
        ),
        _extraer_consecutivo_procedimiento(
            numero_procedimiento
        ),
        str(numero_procedimiento or ""),
        _entero_seguro(item.get("id_procedimiento")),
    )


def _convertir_columnas_numericas(dataframe, columnas):
    """Convierte las columnas indicadas a valores numéricos."""
    for columna in columnas:
        if columna in dataframe.columns:
            dataframe[columna] = pd.to_numeric(
                dataframe[columna],
                errors="coerce",
            )

    return dataframe


def _ordenar_dataframe(dataframe, columnas_numericas):
    """
    Ordena el DataFrame y elimina filas sin información numérica.
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

    return dataframe.reset_index(drop=True)


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
                "Procedimiento": (
                    _construir_etiqueta_procedimiento(item)
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

    return _ordenar_dataframe(
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
                "Procedimiento": (
                    _construir_etiqueta_procedimiento(item)
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

    return _ordenar_dataframe(
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


def _grafica_lineas_precios(dataframe):
    """
    Construye la gráfica de precios con orden explícito del eje X.

    Altair recibe directamente la lista ordenada de procedimientos,
    evitando que Streamlit/Vega-Lite aplique orden alfabético.
    """
    orden_procedimientos = (
        dataframe["Procedimiento"].drop_duplicates().tolist()
    )

    datos = dataframe[
        ["Procedimiento", *COLUMNAS_PRECIOS]
    ].melt(
        id_vars=["Procedimiento"],
        value_vars=COLUMNAS_PRECIOS,
        var_name="Etapa",
        value_name="Precio",
    )

    datos = datos.dropna(subset=["Precio"])

    return (
        alt.Chart(datos)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "Procedimiento:N",
                sort=orden_procedimientos,
                title=None,
                axis=alt.Axis(
                    labelAngle=-90,
                    labelLimit=300,
                ),
            ),
            y=alt.Y(
                "Precio:Q",
                title="Precio unitario",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "Etapa:N",
                title=None,
                sort=COLUMNAS_PRECIOS,
            ),
            tooltip=[
                alt.Tooltip(
                    "Procedimiento:N",
                    title="Procedimiento",
                ),
                alt.Tooltip(
                    "Etapa:N",
                    title="Etapa",
                ),
                alt.Tooltip(
                    "Precio:Q",
                    title="Precio",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=420)
        .interactive()
    )


def _grafica_barras_variaciones(dataframe):
    """
    Construye la gráfica de variaciones con orden explícito del eje X.
    """
    orden_procedimientos = (
        dataframe["Procedimiento"].drop_duplicates().tolist()
    )

    datos = dataframe[
        ["Procedimiento", *COLUMNAS_VARIACIONES]
    ].melt(
        id_vars=["Procedimiento"],
        value_vars=COLUMNAS_VARIACIONES,
        var_name="Variación",
        value_name="Porcentaje",
    )

    datos = datos.dropna(subset=["Porcentaje"])

    return (
        alt.Chart(datos)
        .mark_bar()
        .encode(
            x=alt.X(
                "Procedimiento:N",
                sort=orden_procedimientos,
                title=None,
                axis=alt.Axis(
                    labelAngle=-90,
                    labelLimit=300,
                ),
            ),
            y=alt.Y(
                "Porcentaje:Q",
                title="Variación (%)",
            ),
            color=alt.Color(
                "Variación:N",
                title=None,
                sort=COLUMNAS_VARIACIONES,
            ),
            xOffset="Variación:N",
            tooltip=[
                alt.Tooltip(
                    "Procedimiento:N",
                    title="Procedimiento",
                ),
                alt.Tooltip(
                    "Variación:N",
                    title="Comparación",
                ),
                alt.Tooltip(
                    "Porcentaje:Q",
                    title="Variación",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=420)
    )


def _grafica_barras_estados(dataframe):
    """Construye la gráfica de distribución de estados."""
    return (
        alt.Chart(dataframe)
        .mark_bar()
        .encode(
            x=alt.X(
                "Estado:N",
                title=None,
                sort=None,
                axis=alt.Axis(labelAngle=-25),
            ),
            y=alt.Y(
                "Procedimientos:Q",
                title="Procedimientos",
            ),
            tooltip=[
                alt.Tooltip("Estado:N"),
                alt.Tooltip(
                    "Procedimientos:Q",
                    format=",",
                ),
            ],
        )
        .properties(height=380)
    )


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
            grafica = _grafica_lineas_precios(dataframe)
            st.altair_chart(
                grafica,
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
            grafica = _grafica_barras_variaciones(dataframe)
            st.altair_chart(
                grafica,
                use_container_width=True,
            )

    with tab_estados:
        dataframe = _dataframe_estados(estados)

        if dataframe.empty:
            st.info(
                "No existen estados analíticos para representar."
            )
        else:
            grafica = _grafica_barras_estados(dataframe)
            st.altair_chart(
                grafica,
                use_container_width=True,
            )