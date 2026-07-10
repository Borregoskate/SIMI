"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_propuestas.py

Módulo Streamlit para la Carga 2:
Propuestas Iniciales.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import pandas as pd
import streamlit as st

from repositories.procedimientos_repository import (
    ProcedimientosRepository
)
from services.database_service import get_connection
from services.import_engine import procesar_dataframe
from services.prevalidacion_propuestas_service import (
    prevalidar_archivo_propuestas
)
from services.propuestas_import_service import (
    procesar_fila_propuesta
)


COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS = {
    "RFC": "RFC",
    "RAZON_SOCIAL": "RAZON_SOCIAL",
    "CLAVE": "CLAVE",
    "CANTIDAD_OFERTADA": "CANTIDAD_OFERTADA",
    "PAIS_ORIGEN": "PAIS_ORIGEN",
    "PRECIO_UNITARIO": "PRECIO_UNITARIO",
}


def obtener_procedimientos_activos():
    """
    Obtiene los procedimientos activos disponibles.
    """

    repository = ProcedimientosRepository()
    conn = get_connection()

    try:
        return repository.get_activos(conn=conn)
    finally:
        conn.close()


def mostrar_resultado_importacion(resultado):
    """
    Muestra el resumen devuelto por el motor general.
    """

    if resultado.get("success"):
        st.success(
            "Las propuestas iniciales se importaron correctamente."
        )
    else:
        st.error(
            "La importación no se completó. "
            "La transacción fue revertida y no se guardaron "
            "registros del archivo."
        )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Procesados",
        resultado.get("procesados", 0)
    )

    col2.metric(
        "Insertados",
        resultado.get("insertados", 0)
    )

    col3.metric(
        "Actualizados",
        resultado.get("actualizados", 0)
    )

    col4.metric(
        "Omitidos",
        resultado.get("omitidos", 0)
    )

    errores = resultado.get("errores", [])

    if errores:
        st.subheader("Errores de importación")
        st.dataframe(
            pd.DataFrame(errores),
            use_container_width=True,
            hide_index=True
        )

    advertencias = resultado.get("advertencias", [])

    if advertencias:
        st.subheader("Advertencias")
        st.dataframe(
            pd.DataFrame(advertencias),
            use_container_width=True,
            hide_index=True
        )


def mostrar_carga_propuestas():
    """
    Renderiza la interfaz de Carga 2.
    """

    st.header("Carga 2 - Propuestas Iniciales")

    st.info(
        "Esta carga registra las propuestas iniciales de los "
        "proveedores para un procedimiento previamente cargado."
    )

    try:
        procedimientos = obtener_procedimientos_activos()
    except Exception as error:
        st.error(
            "No fue posible consultar los procedimientos activos."
        )
        st.exception(error)
        return

    if not procedimientos:
        st.warning(
            "No hay procedimientos activos disponibles."
        )
        return

    opciones = {
        (
            f"{procedimiento['numero_procedimiento']} "
            f"| Ejercicio {procedimiento['ejercicio']}"
        ): procedimiento["id_procedimiento"]
        for procedimiento in procedimientos
    }

    procedimiento_seleccionado = st.selectbox(
        "Selecciona el procedimiento",
        options=list(opciones.keys())
    )

    id_procedimiento = opciones[
        procedimiento_seleccionado
    ]

    archivo = st.file_uploader(
        "Carga el archivo Excel de propuestas iniciales",
        type=["xlsx", "xls"],
        key="archivo_propuestas_iniciales"
    )

    if archivo is None:
        return

    resultado_prevalidacion = (
        prevalidar_archivo_propuestas(archivo)
    )

    if not resultado_prevalidacion.get("valido"):
        st.error(
            "El archivo contiene errores de prevalidación."
        )

        st.dataframe(
            pd.DataFrame(
                resultado_prevalidacion.get("errores", [])
            ),
            use_container_width=True,
            hide_index=True
        )

        return

    df_propuestas = resultado_prevalidacion.get("df")

    if df_propuestas is None or df_propuestas.empty:
        st.warning(
            "El archivo no contiene propuestas para importar."
        )
        return

    st.success("Archivo prevalidado correctamente.")

    st.subheader("Vista previa de datos normalizados")

    st.dataframe(
        df_propuestas.head(20),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Registros preparados para importar: "
        f"{len(df_propuestas)}"
    )

    if not st.button(
        "Importar propuestas iniciales",
        type="primary"
    ):
        return

    conn = None

    try:
        conn = get_connection()

        resultado_importacion = procesar_dataframe(
            df=df_propuestas,
            columnas_requeridas=(
                COLUMNAS_REQUERIDAS_CARGA_PROPUESTAS
            ),
            funcion_procesar_fila=procesar_fila_propuesta,
            tabla="propuestas",
            fila_inicial_excel=2,
            conn=conn,
            usar_transaccion=True,
            detener_en_error=True,
            id_procedimiento=id_procedimiento
        )

        mostrar_resultado_importacion(
            resultado_importacion
        )

    except Exception as error:
        if conn:
            conn.rollback()

        st.error(
            "Ocurrió un error inesperado durante la importación."
        )
        st.exception(error)

    finally:
        if conn:
            conn.close()