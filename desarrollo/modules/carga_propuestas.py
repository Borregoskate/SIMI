"""Módulo visual para la Carga 2: Propuestas Iniciales."""

import pandas as pd
import streamlit as st

from services.prevalidacion_propuestas_service import prevalidar_archivo_propuestas
from services.propuestas_import_service import (
    importar_propuestas_iniciales,
    obtener_procedimientos_activos,
)


def mostrar_resultado_importacion(resultado):
    if resultado.get("success"):
        st.success("Las propuestas iniciales se importaron correctamente.")
    else:
        st.error(
            "La importación no se completó. La transacción fue revertida "
            "y no se guardaron registros parciales."
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Procesados", resultado.get("procesados", 0))
    col2.metric("Insertados", resultado.get("insertados", 0))
    col3.metric("Actualizados", resultado.get("actualizados", 0))
    col4.metric("Omitidos", resultado.get("omitidos", 0))

    if resultado.get("errores"):
        st.dataframe(
            pd.DataFrame(resultado["errores"]),
            width="stretch",
            hide_index=True,
        )
    if resultado.get("advertencias"):
        st.dataframe(
            pd.DataFrame(resultado["advertencias"]),
            width="stretch",
            hide_index=True,
        )


def mostrar_carga_propuestas():
    st.header("Carga 2 - Propuestas Iniciales")

    try:
        procedimientos = obtener_procedimientos_activos()
    except Exception as error:
        st.error("No fue posible consultar los procedimientos activos.")
        st.exception(error)
        return

    if not procedimientos:
        st.warning("No hay procedimientos activos disponibles.")
        return

    opciones = {
        (
            f"{procedimiento['numero_procedimiento']} "
            f"| Ejercicio {procedimiento['ejercicio']}"
        ): procedimiento["id_procedimiento"]
        for procedimiento in procedimientos
    }
    seleccion = st.selectbox("Selecciona el procedimiento", list(opciones.keys()))
    id_procedimiento = opciones[seleccion]

    archivo = st.file_uploader(
        "Carga el archivo Excel de propuestas iniciales",
        type=["xlsx", "xls"],
        key="archivo_propuestas_iniciales",
    )
    if archivo is None:
        return

    prevalidacion = prevalidar_archivo_propuestas(archivo)
    if not prevalidacion.get("valido"):
        st.error("El archivo contiene errores de prevalidación.")
        st.dataframe(
            pd.DataFrame(prevalidacion.get("errores", [])),
            width="stretch",
            hide_index=True,
        )
        return

    df_propuestas = prevalidacion.get("df")
    if df_propuestas is None or df_propuestas.empty:
        st.warning("El archivo no contiene propuestas para importar.")
        return

    st.success("Archivo prevalidado correctamente.")
    st.dataframe(df_propuestas.head(20), width="stretch", hide_index=True)

    if st.button("Importar propuestas iniciales", type="primary"):
        resultado = importar_propuestas_iniciales(
            df=df_propuestas,
            id_procedimiento=id_procedimiento,
        )
        mostrar_resultado_importacion(resultado)


__all__ = ["mostrar_resultado_importacion", "mostrar_carga_propuestas"]
