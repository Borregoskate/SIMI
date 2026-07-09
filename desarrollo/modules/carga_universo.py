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

from config.database import get_connection

from services.prevalidacion_universo_service import (
    prevalidar_universo_procedimiento,
    prevalidar_universo_contra_bd
)


def mostrar_carga_universo():
    """
    Pantalla de prevalidación para la Carga 1.
    """

    st.title("Carga 1 — Universo del Procedimiento")

    st.markdown(
        """
        En este módulo se carga el universo inicial del procedimiento:

        - Claves
        - Descripciones

        La cantidad requerida es opcional y no bloquea la carga.
        """
    )

    st.divider()

    st.subheader("Datos generales del procedimiento")

    numero_procedimiento = st.text_input(
        "Número / Nombre del procedimiento"
    )

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

    descripcion = st.text_area(
        "Descripción del procedimiento (opcional)"
    )

    st.divider()

    archivo = st.file_uploader(
        "Carga el archivo Excel del universo del procedimiento",
        type=["xlsx", "xls"]
    )

    if archivo is None:
        return

    if not numero_procedimiento.strip():
        st.warning(
            "Debes capturar el número o nombre del procedimiento antes de validar."
        )
        return

    resultado = prevalidar_universo_procedimiento(archivo)

    st.subheader("Resultado de prevalidación estructural")

    if not resultado["valido"]:
        st.error(
            "El archivo contiene errores estructurales y no puede continuar."
        )

        for error in resultado["errores"]:
            st.warning(error)

        if resultado["dataframe"] is not None:
            st.subheader("Vista previa del archivo recibido")
            st.dataframe(
                resultado["dataframe"],
                use_container_width=True
            )

        return

    st.success("El archivo fue prevalidado estructuralmente correctamente.")

    resumen = resultado["resumen"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Registros", resumen["total_registros"])
    col2.metric("Claves únicas", resumen["total_claves_unicas"])
    col3.metric("Duplicados", resumen["total_duplicados"])
    col4.metric("Errores", resumen["total_errores"])

    st.divider()

    st.subheader("Prevalidación contra base de datos")

    conn = None

    try:
        conn = get_connection()

        resultado_bd = prevalidar_universo_contra_bd(
            df=resultado["dataframe"],
            conn=conn,
            numero_procedimiento=numero_procedimiento
        )

    except Exception as error:
        st.error(
            "Ocurrió un error al conectar o validar contra la base de datos."
        )
        st.exception(error)
        return

    finally:
        if conn is not None:
            conn.close()

    if resultado_bd["success"]:
        st.success(
            "La prevalidación contra base de datos fue correcta."
        )

        resumen_bd = resultado_bd["resumen"]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Registros", resumen_bd["total_registros"])
        col2.metric("Claves existentes", resumen_bd["claves_existentes"])
        col3.metric("Claves nuevas", resumen_bd["claves_nuevas"])
        col4.metric("Errores BD", resumen_bd["errores"])

        st.subheader("Vista previa enriquecida")

        st.dataframe(
            resultado_bd["df"],
            use_container_width=True
        )

        st.info(
            "El archivo está listo para la siguiente etapa: inserción en base de datos."
        )

    else:
        st.error(
            "Se encontraron errores contra la base de datos."
        )

        for error in resultado_bd["errores"]:
            st.warning(error)

        st.subheader("Vista previa con validación contra BD")

        st.dataframe(
            resultado_bd["df"],
            use_container_width=True
        )