"""Módulo visual para la Carga 1: Universo del Procedimiento."""

import streamlit as st

from services.prevalidacion_universo_service import (
    prevalidar_universo_contra_bd,
    prevalidar_universo_procedimiento,
)
from services.universo_import_service import importar_universo_procedimiento


def mostrar_carga_universo():
    st.title("Carga 1 — Universo del Procedimiento")
    st.markdown(
        """
        En este módulo se carga el universo inicial:
        - Claves
        - Descripciones
        - Cantidad requerida opcional
        """
    )

    numero_procedimiento = st.text_input("Número / Nombre del procedimiento")
    tipo_procedimiento = st.selectbox(
        "Tipo de procedimiento",
        [
            "Compra Consolidada",
            "Compra Emergente",
            "Patente y Fuente Única",
            "Faboterápicos",
            "Material de Curación",
        ],
    )
    ejercicio = st.number_input("Ejercicio", min_value=2020, max_value=2100, step=1)
    descripcion = st.text_area("Descripción del procedimiento (opcional)")
    archivo = st.file_uploader(
        "Carga el archivo Excel del universo",
        type=["xlsx", "xls"],
    )

    if archivo is None:
        return
    if not numero_procedimiento.strip():
        st.warning("Debes capturar el número o nombre del procedimiento.")
        return

    resultado = prevalidar_universo_procedimiento(archivo)
    if not resultado["valido"]:
        st.error("El archivo contiene errores estructurales.")
        for error in resultado["errores"]:
            st.warning(error)
        return

    st.success("El archivo fue prevalidado correctamente.")
    st.dataframe(resultado["dataframe"], width="stretch")

    resultado_bd = prevalidar_universo_contra_bd(
        df=resultado["dataframe"],
        numero_procedimiento=numero_procedimiento,
    )
    if not resultado_bd["success"]:
        st.error("Se encontraron errores contra la base de datos.")
        for error in resultado_bd["errores"]:
            st.warning(error)
        return

    st.success("La prevalidación contra base de datos fue correcta.")
    st.dataframe(resultado_bd["df"], width="stretch")

    confirmar = st.checkbox("Confirmo que deseo importar este universo.")
    if not confirmar:
        return

    if st.button("Importar universo del procedimiento", type="primary"):
        resultado_importacion = importar_universo_procedimiento(
            df=resultado["dataframe"],
            numero_procedimiento=numero_procedimiento,
            tipo_procedimiento=tipo_procedimiento,
            ejercicio=ejercicio,
            descripcion=descripcion,
        )
        if resultado_importacion["success"]:
            st.success("La Carga 1 fue importada correctamente.")
            st.info(
                f"Procedimiento creado con ID: "
                f"{resultado_importacion['id_procedimiento']}"
            )
        else:
            st.error("La importación no pudo completarse.")
            for error in resultado_importacion["errores"]:
                st.warning(error)


__all__ = ["mostrar_carga_universo"]
