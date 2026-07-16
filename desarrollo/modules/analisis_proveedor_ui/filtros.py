"""Filtros visuales para Análisis por Proveedor."""

import streamlit as st


OPCION_TODOS = "Todos"


def _mapa_proveedores(registros):
    opciones = {}
    for registro in registros or []:
        item = dict(registro)
        id_proveedor = item.get("id_proveedor")
        if id_proveedor is None:
            continue
        razon_social = item.get("razon_social") or f"Proveedor {id_proveedor}"
        rfc = item.get("rfc")
        etiqueta = f"{razon_social} — {rfc}" if rfc else str(razon_social)
        opciones[etiqueta] = id_proveedor
    return opciones


def _mapa_procedimientos(registros):
    opciones = {OPCION_TODOS: None}
    for registro in registros or []:
        item = dict(registro)
        id_procedimiento = item.get("id_procedimiento")
        if id_procedimiento is None:
            continue
        numero = item.get("numero_procedimiento") or f"Procedimiento {id_procedimiento}"
        ejercicio = item.get("ejercicio")
        etiqueta = str(numero)
        if ejercicio is not None and str(ejercicio) not in etiqueta:
            etiqueta = f"{etiqueta} — {ejercicio}"
        opciones[etiqueta] = id_procedimiento
    return opciones


def _mapa_claves(registros):
    opciones = {OPCION_TODOS: None}
    for registro in registros or []:
        item = dict(registro)
        id_clave = item.get("id_clave")
        if id_clave is None:
            continue
        clave = item.get("clave") or f"Clave {id_clave}"
        descripcion = item.get("descripcion") or item.get("descripcion_clave")
        etiqueta = f"{clave} — {descripcion}" if descripcion else str(clave)
        opciones[etiqueta] = id_clave
    return opciones


def _ejercicios(registros):
    valores = []
    for registro in registros or []:
        ejercicio = dict(registro).get("ejercicio")
        if ejercicio is not None and ejercicio not in valores:
            valores.append(ejercicio)
    return valores


def _limpiar_dependientes():
    for clave in (
        "analisis_proveedor_filtro_procedimiento",
        "analisis_proveedor_filtro_ejercicio",
        "analisis_proveedor_filtro_clave",
    ):
        st.session_state.pop(clave, None)


def mostrar_filtros_analisis_proveedor(service):
    catalogos = service.obtener_catalogos_filtros()
    mapa_proveedores = _mapa_proveedores(catalogos.get("proveedores", []))
    if not mapa_proveedores:
        return None

    st.subheader("Filtros")
    etiqueta_proveedor = st.selectbox(
        "Proveedor",
        options=list(mapa_proveedores.keys()),
        key="analisis_proveedor_filtro_proveedor",
        on_change=_limpiar_dependientes,
    )
    id_proveedor = mapa_proveedores[etiqueta_proveedor]

    dependientes = service.obtener_catalogos_filtros(id_proveedor=id_proveedor)
    mapa_procedimientos = _mapa_procedimientos(dependientes.get("procedimientos", []))
    mapa_claves = _mapa_claves(dependientes.get("claves", []))
    opciones_ejercicio = [OPCION_TODOS, *_ejercicios(dependientes.get("ejercicios", []))]

    columna_1, columna_2, columna_3 = st.columns(3)
    with columna_1:
        procedimiento = st.selectbox(
            "Procedimiento",
            options=list(mapa_procedimientos.keys()),
            key="analisis_proveedor_filtro_procedimiento",
        )
    with columna_2:
        ejercicio = st.selectbox(
            "Ejercicio",
            options=opciones_ejercicio,
            key="analisis_proveedor_filtro_ejercicio",
        )
    with columna_3:
        clave = st.selectbox(
            "Clave",
            options=list(mapa_claves.keys()),
            key="analisis_proveedor_filtro_clave",
        )

    return {
        "id_proveedor": id_proveedor,
        "id_procedimiento": mapa_procedimientos[procedimiento],
        "ejercicio": None if ejercicio == OPCION_TODOS else ejercicio,
        "id_clave": mapa_claves[clave],
    }
