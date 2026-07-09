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

    col1, col2, col3 = st.columns(3)

    col1.metric("Procesados", resultado["procesados"])
    col2.metric("Insertados", resultado["insertados"])
    col3.metric("Actualizados", resultado["actualizados"])

    if resultado.get("errores"):
        st.subheader("Errores encontrados")
        st.dataframe(pd.DataFrame(resultado["errores"]), use_container_width=True)


def mostrar_carga_catalogos_db():
    st.header("Carga de catálogos a base de datos")

    st.info(
        "Desde esta sección puedes cargar catálogos base del sistema SIMI "
        "directamente a PostgreSQL / Supabase."
    )

    tipo_carga = st.selectbox(
        "Selecciona el tipo de catálogo",
        [
            "Catálogo de claves",
            "Catálogo de proveedores"
        ]
    )

    archivo = st.file_uploader(
        "Selecciona archivo Excel",
        type=["xlsx", "xls"]
    )

    if archivo is None:
        st.warning("Carga un archivo Excel para continuar.")
        return

    try:
        df = pd.read_excel(archivo)
        df = normalizar_dataframe(df)

        st.subheader("Vista previa del archivo")
        st.dataframe(df.head(20), use_container_width=True)

        if st.button("Validar e importar a base de datos"):
            with st.spinner("Procesando archivo..."):

                if tipo_carga == "Catálogo de claves":
                    resultado = cargar_catalogo_claves(df)

                elif tipo_carga == "Catálogo de proveedores":
                    resultado = cargar_catalogo_proveedores(df)

                else:
                    st.error("Tipo de carga no reconocido.")
                    return

            mostrar_resultado_carga(resultado)

    except Exception as e:
        st.error("No fue posible procesar el archivo.")
        st.exception(e)