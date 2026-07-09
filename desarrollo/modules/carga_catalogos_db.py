"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_catalogos_db.py

Pantalla para carga de catálogos a base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st
import pandas as pd

from services.import_service import normalizar_dataframe
from services.catalogos_service import cargar_catalogo_claves
from services.proveedores_service import cargar_catalogo_proveedores


def mostrar_resultado_carga(resultado):
    if resultado["success"]:
        st.success("Carga finalizada correctamente.")
    else:
        st.warning("La carga terminó con errores.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Procesados", resultado.get("procesados", 0))
    col2.metric("Insertados", resultado.get("insertados", 0))
    col3.metric("Actualizados", resultado.get("actualizados", 0))
    col4.metric("Omitidos", resultado.get("omitidos", 0))

    if resultado.get("errores"):
        st.subheader("Errores encontrados")
        st.dataframe(pd.DataFrame(resultado["errores"]), use_container_width=True)


def mostrar_carga_catalogos_db():
    st.header("Carga de catálogos a base de datos")

    st.info(
        "Desde esta sección puedes cargar catálogos base del sistema SIMI "
        "directamente a PostgreSQL / Supabase."
    )

    tipo_carga = st.radio(
        "Selecciona el tipo de catálogo",
        [
            "Catálogo de proveedores",
            "Catálogo de claves"
        ],
        horizontal=True
    )

    archivo = st.file_uploader(
        "Selecciona archivo Excel",
        type=["xlsx", "xls"],
        key=f"archivo_{tipo_carga}"
    )

    if archivo is None:
        st.warning("Carga un archivo Excel para continuar.")
        return

    try:
        df = pd.read_excel(archivo)
        df = normalizar_dataframe(df)

        st.subheader("Columnas detectadas")
        st.code(", ".join(df.columns.tolist()))

        st.subheader("Vista previa del archivo")
        st.dataframe(df.head(20), use_container_width=True)

        if st.button("Validar e importar a base de datos", type="primary"):
            with st.spinner("Procesando archivo..."):

                if tipo_carga == "Catálogo de proveedores":
                    resultado = cargar_catalogo_proveedores(df)

                elif tipo_carga == "Catálogo de claves":
                    resultado = cargar_catalogo_claves(df)

                else:
                    st.error("Tipo de carga no reconocido.")
                    return

            mostrar_resultado_carga(resultado)

    except Exception as e:
        st.error("No fue posible procesar el archivo.")
        st.exception(e)