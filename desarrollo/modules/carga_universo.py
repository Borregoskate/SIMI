"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_universo.py

Módulo visual para la Carga 1:
Universo del Procedimiento.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st

from services.prevalidacion_universo_service import (
    prevalidar_universo_procedimiento
)


def mostrar_carga_universo():
    """
    Pantalla de prevalidación para la Carga 1.
    """

    st.title("Carga 1 — Universo del Procedimiento")

    st.markdown(
        """
        En este módulo se cargará el universo inicial del procedimiento:
        
        - Claves
        - Descripciones
        - Cantidades requeridas
        
        Esta etapa solo realiza la **prevalidación** del archivo.
        No inserta información en la base de datos.
        """
    )

    st.divider()

    st.subheader("Datos generales del procedimiento")

    numero_procedimiento = st.text_input("Número / Nombre del procedimiento")
    tipo_procedimiento = st.selectbox(
        "Tipo de procedimiento",
        [
            "Compra Consolidada",
            "Compra Emergente",
            "Patente y Fuente Única",
            "Faboterápicos",
            "Material de Curación",
        ]
    )

    ejercicio = st.number_input(
        "Ejercicio",
        min_value=2020,
        max_value=2100,
        step=1
    )

    descripcion = st.text_area("Descripción del procedimiento (opcional)")

    st.divider()

    archivo = st.file_uploader(
        "Carga el archivo Excel del universo del procedimiento",
        type=["xlsx", "xls"]
    )

    if archivo is not None:
        resultado = prevalidar_universo_procedimiento(archivo)

        st.subheader("Resultado de prevalidación")

        if resultado["valido"]:
            st.success("El archivo fue prevalidado correctamente.")

            resumen = resultado["resumen"]

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Registros", resumen["total_registros"])
            col2.metric("Claves únicas", resumen["total_claves_unicas"])
            col3.metric("Duplicados", resumen["total_duplicados"])
            col4.metric(
                "Cantidad total",
                f"{resumen['cantidad_total_requerida']:,.2f}"
            )

            st.subheader("Vista previa")

            st.dataframe(
                resultado["dataframe"],
                use_container_width=True
            )

            st.info(
                "El archivo está listo para la siguiente etapa: inserción en base de datos."
            )

        else:
            st.error("El archivo contiene errores y no puede continuar.")

            for error in resultado["errores"]:
                st.warning(error)

            if resultado["dataframe"] is not None:
                st.subheader("Vista previa del archivo recibido")
                st.dataframe(
                    resultado["dataframe"],
                    use_container_width=True
                )