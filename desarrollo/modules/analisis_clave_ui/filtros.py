"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

filtros.py

Componente visual de filtros para Análisis por Clave.

Responsabilidades:
- Mostrar el selector obligatorio de clave.
- Mostrar filtros opcionales de procedimiento y ejercicio.
- Solicitar catálogos exclusivamente mediante AnalisisClaveService.
- Devolver valores normalizados al controlador principal.

Este componente:
- No ejecuta SQL.
- No calcula indicadores.
- No consulta directamente el Repository.
- No contiene reglas analíticas.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st


OPCION_TODOS = "Todos"


def _crear_mapa_claves(claves):
    """
    Construye un mapa etiqueta -> id_clave.

    La etiqueta incluye clave y descripción para facilitar
    la selección sin alterar los datos originales.
    """
    opciones = {}

    for registro in claves or []:
        item = dict(registro)
        id_clave = item.get("id_clave")

        if id_clave is None:
            continue

        clave = item.get("clave") or f"Clave {id_clave}"
        descripcion = item.get("descripcion")

        etiqueta = str(clave)

        if descripcion:
            etiqueta = f"{etiqueta} — {descripcion}"

        opciones[etiqueta] = id_clave

    return opciones


def _crear_mapa_procedimientos(procedimientos):
    """Construye un mapa etiqueta -> id_procedimiento."""
    opciones = {OPCION_TODOS: None}

    for registro in procedimientos or []:
        item = dict(registro)
        id_procedimiento = item.get("id_procedimiento")

        if id_procedimiento is None:
            continue

        numero = (
            item.get("numero_procedimiento")
            or f"Procedimiento {id_procedimiento}"
        )
        ejercicio = item.get("ejercicio")

        etiqueta = str(numero)

        if ejercicio is not None:
            etiqueta = f"{etiqueta} — {ejercicio}"

        opciones[etiqueta] = id_procedimiento

    return opciones


def _obtener_ejercicios(ejercicios):
    """Extrae ejercicios únicos conservando el orden recibido."""
    resultado = []

    for registro in ejercicios or []:
        item = dict(registro)
        ejercicio = item.get("ejercicio")

        if ejercicio is None:
            continue

        if ejercicio not in resultado:
            resultado.append(ejercicio)

    return resultado


def _limpiar_filtros_dependientes():
    """
    Reinicia procedimiento y ejercicio cuando cambia la clave.

    Esto evita conservar opciones pertenecientes a otra clave.
    """
    st.session_state.pop(
        "analisis_clave_filtro_procedimiento",
        None,
    )
    st.session_state.pop(
        "analisis_clave_filtro_ejercicio",
        None,
    )


def mostrar_filtros_analisis_clave(service):
    """
    Muestra los filtros del módulo y devuelve sus valores.

    Retorno:
        {
            "id_clave": int,
            "id_procedimiento": int | None,
            "ejercicio": int | None,
        }

    Devuelve None cuando no existen claves disponibles.
    """
    catalogos_generales = service.obtener_catalogos_filtros()
    claves = catalogos_generales.get("claves", [])

    mapa_claves = _crear_mapa_claves(claves)

    if not mapa_claves:
        return None

    st.subheader("Filtros")

    etiqueta_clave = st.selectbox(
        "Clave",
        options=list(mapa_claves.keys()),
        key="analisis_clave_filtro_clave",
        on_change=_limpiar_filtros_dependientes,
    )

    id_clave = mapa_claves[etiqueta_clave]

    catalogos_clave = service.obtener_catalogos_filtros(
        id_clave=id_clave,
    )

    mapa_procedimientos = _crear_mapa_procedimientos(
        catalogos_clave.get("procedimientos", [])
    )
    opciones_ejercicio = [
        OPCION_TODOS,
        *_obtener_ejercicios(
            catalogos_clave.get("ejercicios", [])
        ),
    ]

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        etiqueta_procedimiento = st.selectbox(
            "Procedimiento",
            options=list(mapa_procedimientos.keys()),
            key="analisis_clave_filtro_procedimiento",
        )

    with columna_2:
        ejercicio_seleccionado = st.selectbox(
            "Ejercicio",
            options=opciones_ejercicio,
            key="analisis_clave_filtro_ejercicio",
        )

    return {
        "id_clave": id_clave,
        "id_procedimiento": mapa_procedimientos[
            etiqueta_procedimiento
        ],
        "ejercicio": (
            None
            if ejercicio_seleccionado == OPCION_TODOS
            else ejercicio_seleccionado
        ),
    }