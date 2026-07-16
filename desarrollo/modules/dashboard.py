"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

dashboard.py

Módulo Streamlit del Dashboard Ejecutivo.

Responsabilidades:
- Mostrar filtros.
- Mostrar indicadores.
- Mostrar gráficas.
- Mostrar tablas ejecutivas.
- Consumir exclusivamente DashboardService.

Este módulo:
- No ejecuta SQL.
- No calcula reglas de negocio.
- No abre conexiones directamente.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from services.dashboard_service import DashboardService


OPCION_TODOS = "Todos"


def _valor_entero(valor):
    """Convierte valores numéricos a entero para presentación."""
    if valor is None:
        return 0

    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _formatear_decimal(valor, decimales=2):
    """Formatea valores decimales sin alterar la regla analítica."""
    if valor is None:
        return "Sin información"

    try:
        numero = Decimal(str(valor))
    except (TypeError, ValueError):
        return "Sin información"

    return f"{numero:,.{decimales}f}"


def _formatear_porcentaje(valor):
    """Formatea un porcentaje para la interfaz."""
    if valor is None:
        return "Sin evaluaciones"

    return f"{_formatear_decimal(valor)}%"


def _formatear_moneda(valor):
    """Formatea precios unitarios en moneda."""
    if valor is None:
        return "Sin información"

    return f"${_formatear_decimal(valor)}"


def _normalizar_dataframe(registros):
    """Convierte una lista de registros en DataFrame controlado."""
    if not registros:
        return pd.DataFrame()

    return pd.DataFrame([dict(registro) for registro in registros])


def _mapa_procedimientos(procedimientos):
    """Construye las opciones de procedimiento para el selector."""
    opciones = {OPCION_TODOS: None}

    for procedimiento in procedimientos or []:
        id_procedimiento = procedimiento.get("id_procedimiento")
        numero = procedimiento.get("numero_procedimiento")
        ejercicio = procedimiento.get("ejercicio")

        etiqueta = str(numero or f"Procedimiento {id_procedimiento}")

        if ejercicio is not None:
            etiqueta = f"{etiqueta} — {ejercicio}"

        opciones[etiqueta] = id_procedimiento

    return opciones


def _obtener_ejercicios(ejercicios):
    """Extrae ejercicios únicos para el filtro."""
    resultado = []

    for registro in ejercicios or []:
        ejercicio = registro.get("ejercicio")

        if ejercicio is not None and ejercicio not in resultado:
            resultado.append(ejercicio)

    return resultado


def mostrar_filtros(catalogos):
    """Muestra filtros y devuelve sus valores normalizados."""
    procedimientos = catalogos.get("procedimientos", [])
    ejercicios = catalogos.get("ejercicios", [])

    mapa_procedimientos = _mapa_procedimientos(procedimientos)
    opciones_ejercicio = [OPCION_TODOS, *_obtener_ejercicios(ejercicios)]

    st.subheader("Filtros")

    columna_procedimiento, columna_ejercicio = st.columns(2)

    with columna_procedimiento:
        etiqueta_procedimiento = st.selectbox(
            "Procedimiento",
            options=list(mapa_procedimientos.keys()),
            key="dashboard_filtro_procedimiento",
        )

    with columna_ejercicio:
        ejercicio_seleccionado = st.selectbox(
            "Ejercicio",
            options=opciones_ejercicio,
            key="dashboard_filtro_ejercicio",
        )

    return {
        "id_procedimiento": mapa_procedimientos[
            etiqueta_procedimiento
        ],
        "ejercicio": (
            None
            if ejercicio_seleccionado == OPCION_TODOS
            else ejercicio_seleccionado
        ),
    }


def mostrar_indicadores(indicadores):
    """Muestra las tarjetas principales del Dashboard."""
    fila_1 = st.columns(4)

    fila_1[0].metric(
        "Procedimientos",
        _valor_entero(
            indicadores.get("total_procedimientos")
        ),
    )
    fila_1[1].metric(
        "Claves",
        _valor_entero(indicadores.get("total_claves")),
    )
    fila_1[2].metric(
        "Proveedores participantes",
        _valor_entero(
            indicadores.get(
                "total_proveedores_participantes"
            )
        ),
    )
    fila_1[3].metric(
        "Propuestas iniciales",
        _valor_entero(
            indicadores.get("total_propuestas_iniciales")
        ),
    )

    fila_2 = st.columns(4)

    fila_2[0].metric(
        "Claves adjudicadas",
        _valor_entero(
            indicadores.get("total_claves_adjudicadas")
        ),
    )
    fila_2[1].metric(
        "Claves desiertas",
        _valor_entero(
            indicadores.get("total_claves_desiertas")
        ),
    )
    fila_2[2].metric(
        "Porcentaje adjudicado",
        _formatear_porcentaje(
            indicadores.get(
                "porcentaje_claves_adjudicadas"
            )
        ),
    )
    fila_2[3].metric(
        "Promedio proveedores por clave",
        _formatear_decimal(
            indicadores.get(
                "promedio_proveedores_por_clave"
            )
        ),
    )

    st.info(
        "Nivel general de competencia: "
        f"**{indicadores.get('nivel_competencia', 'SIN DATOS')}**"
    )


def mostrar_grafica_estado_claves(estado_claves):
    """Muestra distribución de estados analíticos de las claves."""
    df = _normalizar_dataframe(estado_claves)

    if df.empty or "estado_analitico" not in df.columns:
        st.info("No existen datos para mostrar el estado de las claves.")
        return

    resumen = (
        df.groupby("estado_analitico", dropna=False)
        .size()
        .reset_index(name="total_claves")
    )

    figura = px.pie(
        resumen,
        names="estado_analitico",
        values="total_claves",
        title="Distribución del estado de las claves",
        hole=0.45,
    )

    st.plotly_chart(figura, width="stretch")


def mostrar_grafica_competencia(competencia_claves):
    """Muestra proveedores con oferta inicial por clave."""
    df = _normalizar_dataframe(competencia_claves)

    columnas = {
        "clave",
        "total_proveedores",
        "nivel_competencia",
    }

    if df.empty or not columnas.issubset(df.columns):
        st.info("No existen datos de competencia para mostrar.")
        return

    df = df.sort_values(
        by=["total_proveedores", "clave"],
        ascending=[False, True],
    )

    figura = px.bar(
        df,
        x="clave",
        y="total_proveedores",
        color="nivel_competencia",
        title="Competencia por clave",
        labels={
            "clave": "Clave",
            "total_proveedores": "Proveedores",
            "nivel_competencia": "Nivel",
        },
    )

    st.plotly_chart(figura, width="stretch")


def mostrar_grafica_aprobacion(aprobacion_proveedores):
    """Muestra porcentaje de aprobación técnica por proveedor."""
    df = _normalizar_dataframe(aprobacion_proveedores)

    columnas = {
        "razon_social",
        "porcentaje_aprobacion",
    }

    if df.empty or not columnas.issubset(df.columns):
        st.info("No existen evaluaciones técnicas para mostrar.")
        return

    df = df[df["porcentaje_aprobacion"].notna()].copy()

    if df.empty:
        st.info("Los proveedores seleccionados no tienen evaluaciones.")
        return

    df["porcentaje_aprobacion"] = pd.to_numeric(
        df["porcentaje_aprobacion"],
        errors="coerce",
    )
    df = df.dropna(subset=["porcentaje_aprobacion"])
    df = df.sort_values(
        by="porcentaje_aprobacion",
        ascending=False,
    )

    figura = px.bar(
        df,
        x="razon_social",
        y="porcentaje_aprobacion",
        title="Aprobación técnica por proveedor",
        labels={
            "razon_social": "Proveedor",
            "porcentaje_aprobacion": "Aprobación (%)",
        },
    )
    figura.update_yaxes(range=[0, 100])

    st.plotly_chart(figura, width="stretch")


def mostrar_grafica_ahorro(precios_claves):
    """Muestra ahorro porcentual de subasta por clave."""
    df = _normalizar_dataframe(precios_claves)

    columnas = {
        "clave",
        "ahorro_porcentual_subasta",
    }

    if df.empty or not columnas.issubset(df.columns):
        st.info("No existe información suficiente de subastas.")
        return

    df = df[df["ahorro_porcentual_subasta"].notna()].copy()

    if df.empty:
        st.info(
            "No existen claves con precio viable y precio de subasta."
        )
        return

    df["ahorro_porcentual_subasta"] = pd.to_numeric(
        df["ahorro_porcentual_subasta"],
        errors="coerce",
    )
    df = df.dropna(subset=["ahorro_porcentual_subasta"])
    df = df.sort_values(
        by="ahorro_porcentual_subasta",
        ascending=False,
    )

    figura = px.bar(
        df,
        x="clave",
        y="ahorro_porcentual_subasta",
        title="Ahorro porcentual por subasta",
        labels={
            "clave": "Clave",
            "ahorro_porcentual_subasta": "Variación (%)",
        },
    )

    st.plotly_chart(figura, width="stretch")


def mostrar_tabla_resumen_procedimientos(registros):
    """Muestra el resumen de competencia por procedimiento."""
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existen procedimientos para mostrar.")
        return

    columnas = {
        "id_procedimiento": "ID",
        "numero_procedimiento": "Procedimiento",
        "ejercicio": "Ejercicio",
        "total_claves": "Total de claves",
        "promedio_proveedores_por_clave": (
            "Promedio de proveedores por clave"
        ),
        "claves_desiertas": "Claves desiertas",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        df[disponibles].rename(columns=columnas),
        width="stretch",
        hide_index=True,
    )


def mostrar_tabla_estado_claves(registros):
    """Muestra el estado detallado de cada clave."""
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existen claves para mostrar.")
        return

    columnas = {
        "numero_procedimiento": "Procedimiento",
        "clave": "Clave",
        "descripcion": "Descripción",
        "proveedores_oferta_inicial": "Proveedores",
        "evaluaciones_positivas": "Evaluaciones positivas",
        "tiene_subasta": "Tiene subasta",
        "tiene_adjudicacion": "Tiene adjudicación",
        "estado_analitico": "Estado analítico",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        df[disponibles].rename(columns=columnas),
        width="stretch",
        hide_index=True,
    )


def mostrar_tabla_proveedores(participacion, aprobacion):
    """Muestra el detalle consolidado de proveedores."""
    df_participacion = _normalizar_dataframe(participacion)
    df_aprobacion = _normalizar_dataframe(aprobacion)

    if df_participacion.empty:
        st.info("No existen proveedores participantes.")
        return

    if not df_aprobacion.empty and "id_proveedor" in df_aprobacion:
        columnas_aprobacion = [
            columna
            for columna in [
                "id_proveedor",
                "total_evaluaciones",
                "evaluaciones_positivas",
                "evaluaciones_negativas",
                "porcentaje_aprobacion",
                "estado_aprobacion",
            ]
            if columna in df_aprobacion.columns
        ]

        df_participacion = df_participacion.merge(
            df_aprobacion[columnas_aprobacion],
            on="id_proveedor",
            how="left",
            suffixes=("", "_tecnica"),
        )

    columnas = {
        "razon_social": "Proveedor",
        "rfc": "RFC",
        "procedimientos_participados": "Procedimientos",
        "presento_oferta_inicial": "Oferta inicial",
        "claves_ofertadas": "Claves ofertadas",
        "evaluaciones_positivas": "Evaluaciones positivas",
        "evaluaciones_negativas": "Evaluaciones negativas",
        "porcentaje_aprobacion": "Aprobación (%)",
        "participo_subasta": "Subasta",
        "claves_adjudicadas": "Claves adjudicadas",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df_participacion.columns
    ]

    st.dataframe(
        df_participacion[disponibles].rename(columns=columnas),
        width="stretch",
        hide_index=True,
    )


def mostrar_tabla_precios(registros):
    """Muestra precios y ahorro de subasta por clave."""
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existe información de precios para mostrar.")
        return

    columnas = {
        "numero_procedimiento": "Procedimiento",
        "clave": "Clave",
        "descripcion": "Descripción",
        "mejor_precio_inicial": "Mejor precio inicial",
        "mejor_precio_viable": "Mejor precio viable",
        "mejor_precio_subasta": "Mejor precio subasta",
        "ahorro_unitario_subasta": "Ahorro unitario",
        "ahorro_porcentual_subasta": "Ahorro (%)",
        "estado_ahorro_subasta": "Resultado",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        df[disponibles].rename(columns=columnas),
        width="stretch",
        hide_index=True,
    )


def mostrar_dashboard():
    """Renderiza el Dashboard Ejecutivo."""
    st.header("Dashboard Ejecutivo")
    st.caption(
        "Indicadores analíticos de procedimientos, claves, "
        "proveedores, evaluaciones, subastas y adjudicaciones."
    )

    service = DashboardService()

    try:
        catalogos = service.obtener_catalogos_filtros()
        filtros = mostrar_filtros(catalogos)

        resultado = service.obtener_dashboard(
            id_procedimiento=filtros["id_procedimiento"],
            ejercicio=filtros["ejercicio"],
        )
    except Exception as error:
        st.error(
            "No fue posible consultar la información del Dashboard."
        )
        st.exception(error)
        return

    indicadores = resultado.get("indicadores", {})
    graficas = resultado.get("graficas", {})
    tablas = resultado.get("tablas", {})

    st.divider()
    mostrar_indicadores(indicadores)

    st.divider()
    st.subheader("Visualizaciones")

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        mostrar_grafica_estado_claves(
            tablas.get("estado_claves", [])
        )

    with columna_2:
        mostrar_grafica_competencia(
            graficas.get("competencia_claves", [])
        )

    columna_3, columna_4 = st.columns(2)

    with columna_3:
        mostrar_grafica_aprobacion(
            graficas.get("aprobacion_proveedores", [])
        )

    with columna_4:
        mostrar_grafica_ahorro(
            graficas.get("precios_claves", [])
        )

    st.divider()
    st.subheader("Detalle ejecutivo")

    pestañas = st.tabs(
        [
            "Procedimientos",
            "Estado de claves",
            "Proveedores",
            "Precios y subasta",
        ]
    )

    with pestañas[0]:
        mostrar_tabla_resumen_procedimientos(
            tablas.get("resumen_procedimientos", [])
        )

    with pestañas[1]:
        mostrar_tabla_estado_claves(
            tablas.get("estado_claves", [])
        )

    with pestañas[2]:
        mostrar_tabla_proveedores(
            tablas.get("participacion_proveedores", []),
            tablas.get("aprobacion_proveedores", []),
        )

    with pestañas[3]:
        mostrar_tabla_precios(
            tablas.get("precios_claves", [])
        )