"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_propuestas.py

Módulo Streamlit para la Carga 2:
Propuestas Iniciales.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import streamlit as st
import pandas as pd

from repositories.procedimientos_repository import ProcedimientosRepository
from services.prevalidacion_propuestas_service import prevalidar_archivo_propuestas
from services.import_engine import procesar_dataframe
from services.propuestas_import_service import procesar_fila_propuesta
from services.database_service import get_connection


COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS = {
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "CANTIDAD_OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS_ORIGEN": "PAIS_ORIGEN",
    "PRECIO_UNITARIO": "PRECIO_UNITARIO",
}


def obtener_procedimientos_activos():
    procedimientos_repository = ProcedimientosRepository()

    conn = get_connection()

    try:
        return procedimientos_repository.get_activos(conn=conn)
    finally:
        conn.close()


def mostrar_carga_propuestas():
    st.header("Carga 2 - Propuestas Iniciales")

    st.info(
        "Esta carga registra las propuestas iniciales de los proveedores "
        "para un procedimiento previamente cargado."
    )

    procedimientos = obtener_procedimientos_activos()

    if not procedimientos:
        st.warning("No hay procedimientos activos disponibles.")
        return

    opciones = {
        f"{p['numero_procedimiento']} | Ejercicio {p['ejercicio']}": p["id_procedimiento"]
        for p in procedimientos
    }

    procedimiento_seleccionado = st.selectbox(
        "Selecciona el procedimiento",
        options=list(opciones.keys())
    )

    id_procedimiento = opciones[procedimiento_seleccionado]

    archivo = st.file_uploader(
        "Carga el archivo Excel de propuestas iniciales",
        type=["xlsx", "xls"]
    )

    if archivo is None:
        return

    resultado_prevalidacion = prevalidar_archivo_propuestas(archivo)

    if not resultado_prevalidacion["valido"]:
        st.error("El archivo contiene errores de prevalidación.")

        errores = pd.DataFrame(resultado_prevalidacion["errores"])
        st.dataframe(errores, use_container_width=True)

        return

    df_propuestas = resultado_prevalidacion["df"]

    st.success("Archivo prevalidado correctamente.")

    st.subheader("Vista previa de datos normalizados")
    st.dataframe(df_propuestas.head(20), use_container_width=True)

    if st.button("Importar propuestas iniciales"):
        conn = get_connection()

        try:
            resultado_importacion = procesar_dataframe(
                df=df_propuestas,
                tabla="propuestas",
                columnas_requeridas=COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS,
                funcion_procesar_fila=procesar_fila_propuesta,
                fila_inicial_excel=2,
                conn=conn,
                id_procedimiento=id_procedimiento,
                usar_transaccion=True
            )

            st.success("Importación finalizada.")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Procesados",
                resultado_importacion.get("procesados", 0)
            )

            col2.metric(
                "Insertados",
                resultado_importacion.get("insertados", 0)
            )

            col3.metric(
                "Omitidos",
                resultado_importacion.get("omitidos", 0)
            )

            if resultado_importacion.get("errores"):
                st.warning("Algunas filas no pudieron importarse.")
                st.dataframe(
                    pd.DataFrame(resultado_importacion["errores"]),
                    use_container_width=True
                )

        except Exception as e:
            st.error("Ocurrió un error durante la importación.")
            st.exception(e)

        finally:
            conn.close()