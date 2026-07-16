"""Gráficas del módulo Análisis por Proveedor."""

import altair as alt
import pandas as pd
import streamlit as st

from modules.analisis_proveedor_ui.utilidades import etiqueta_procedimiento


ETAPAS_PRECIO = ["Inicial", "Subasta", "Adjudicación"]


def _grafica_embudo(registros):
    df = pd.DataFrame([dict(item) for item in registros or []])
    if df.empty:
        return None
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    return alt.Chart(df).mark_bar().encode(
        x=alt.X("etapa:N", title=None, sort=list(df["etapa"])),
        y=alt.Y("total:Q", title="Participaciones"),
        tooltip=[alt.Tooltip("etapa:N", title="Etapa"), alt.Tooltip("total:Q", format=",")],
    ).properties(height=360)


def _grafica_competidores(registros):
    filas = []
    for registro in registros or []:
        item = dict(registro)
        nombre = item.get("razon_social_competidor") or item.get("rfc_competidor") or "Sin nombre"
        filas.extend(
            [
                {"Competidor": nombre, "Resultado": "Victorias", "Total": item.get("victorias_proveedor", 0)},
                {"Competidor": nombre, "Resultado": "Derrotas", "Total": item.get("derrotas_proveedor", 0)},
                {"Competidor": nombre, "Resultado": "Compartidas", "Total": item.get("adjudicaciones_compartidas", 0)},
            ]
        )
    df = pd.DataFrame(filas)
    if df.empty:
        return None
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    return alt.Chart(df).mark_bar().encode(
        y=alt.Y("Competidor:N", sort="-x", title=None),
        x=alt.X("Total:Q", title="Coincidencias"),
        color=alt.Color("Resultado:N", title=None),
        tooltip=["Competidor:N", "Resultado:N", alt.Tooltip("Total:Q", format=",")],
    ).properties(height=max(360, min(700, 36 * max(1, df["Competidor"].nunique()))))


def _mapa_evolucion(registros):
    opciones = {}
    for grupo in registros or []:
        item = dict(grupo)
        id_clave = item.get("id_clave")
        if id_clave is None:
            continue
        clave = item.get("clave") or f"Clave {id_clave}"
        descripcion = item.get("descripcion_clave")
        etiqueta = f"{clave} — {descripcion}" if descripcion else str(clave)
        opciones[etiqueta] = item
    return opciones


def _grafica_evolucion(grupo):
    filas = []
    for punto in grupo.get("puntos", []) or []:
        procedimiento = etiqueta_procedimiento(punto)
        for etapa, campo in (
            ("Inicial", "precio_inicial"),
            ("Subasta", "precio_subasta"),
            ("Adjudicación", "precio_adjudicado"),
        ):
            valor = punto.get(campo)
            if valor is not None:
                filas.append(
                    {
                        "Procedimiento": procedimiento,
                        "Etapa": etapa,
                        "Precio": valor,
                        "Origen": punto.get("origen_dato"),
                    }
                )
    df = pd.DataFrame(filas)
    if df.empty:
        return None
    df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce")
    df = df.dropna(subset=["Precio"])
    orden = list(dict.fromkeys(df["Procedimiento"].tolist()))
    return alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Procedimiento:N", sort=orden, title=None, axis=alt.Axis(labelAngle=-90, labelLimit=300)),
        y=alt.Y("Precio:Q", title="Precio unitario", scale=alt.Scale(zero=False)),
        color=alt.Color("Etapa:N", sort=ETAPAS_PRECIO, title=None),
        strokeDash=alt.StrokeDash("Origen:N", title="Origen"),
        tooltip=[
            "Procedimiento:N",
            "Etapa:N",
            "Origen:N",
            alt.Tooltip("Precio:Q", format=",.2f"),
        ],
    ).properties(height=430).interactive()


def mostrar_graficas_proveedor(resultado):
    graficas = (resultado or {}).get("graficas", {}) or {}
    tab_evolucion, tab_embudo, tab_competencia = st.tabs(
        ["Evolución de precios por clave", "Embudo operativo", "Competencia"]
    )

    with tab_evolucion:
        mapa = _mapa_evolucion(graficas.get("evolucion_por_clave", []))
        if not mapa:
            st.info("No existen precios suficientes para construir la evolución por clave.")
        else:
            etiqueta = st.selectbox(
                "Clave para visualizar",
                options=list(mapa.keys()),
                key="analisis_proveedor_grafica_clave",
            )
            grafica = _grafica_evolucion(mapa[etiqueta])
            if grafica is None:
                st.info("La clave seleccionada no tiene precios comparables.")
            else:
                st.altair_chart(grafica, width="stretch")

    with tab_embudo:
        grafica = _grafica_embudo(graficas.get("embudo_tecnico", []))
        if grafica is None:
            st.info("No existe información suficiente para el embudo.")
        else:
            st.altair_chart(grafica, width="stretch")

    with tab_competencia:
        grafica = _grafica_competidores(graficas.get("competidores", []))
        if grafica is None:
            st.info("No existe información suficiente de competencia.")
        else:
            st.altair_chart(grafica, width="stretch")
