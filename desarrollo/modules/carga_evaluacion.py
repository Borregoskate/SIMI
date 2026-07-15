"""
Módulo visual para la Carga 3: Evaluación Técnica.
"""

import pandas as pd
import streamlit as st

from services.evaluacion_import_service import (
    importar_evaluaciones_tecnicas,
    obtener_procedimientos_activos,
)
from services.prevalidacion_evaluacion_service import (
    prevalidar_archivo_evaluacion,
)


def mostrar_resultado_importacion(resultado):
    """Muestra el resumen devuelto por el motor de importación."""
    if resultado.get("success"):
        st.success(
            "Las evaluaciones técnicas se importaron correctamente."
        )
    else:
        st.error(
            "La importación no se completó. "
            "La transacción fue revertida y no se guardaron "
            "registros parciales."
        )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Procesados",
        resultado.get("procesados", 0),
    )
    col2.metric(
        "Insertados",
        resultado.get("insertados", 0),
    )
    col3.metric(
        "Actualizados",
        resultado.get("actualizados", 0),
    )
    col4.metric(
        "Omitidos",
        resultado.get("omitidos", 0),
    )

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


def mostrar_carga_evaluacion():
    """Renderiza la interfaz completa de la Carga 3."""
    st.header("Carga 3 - Evaluación Técnica")

    st.info(
        "SIMI utilizará únicamente Procedimiento, RFC, Razón social, "
        "Clave y Opinión técnica. La columna OBSERVACIONES será "
        "ignorada completamente."
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

    seleccion = st.selectbox(
        "Selecciona el procedimiento",
        list(opciones.keys()),
        key="procedimiento_evaluacion_tecnica",
    )
    id_procedimiento = opciones[seleccion]

    archivo = st.file_uploader(
        "Carga el archivo Excel de evaluación técnica",
        type=["xlsx", "xls"],
        key="archivo_evaluacion_tecnica",
    )

    if archivo is None:
        return

    prevalidacion = prevalidar_archivo_evaluacion(
        archivo
    )

    if not prevalidacion.get("valido"):
        st.error(
            "El archivo contiene errores de prevalidación."
        )
        st.dataframe(
            pd.DataFrame(
                prevalidacion.get("errores", [])
            ),
            width="stretch",
            hide_index=True,
        )
        return

    df_evaluacion = prevalidacion.get("df")

    if df_evaluacion is None or df_evaluacion.empty:
        st.warning(
            "El archivo no contiene evaluaciones para importar."
        )
        return

    st.success(
        "Archivo prevalidado correctamente."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Evaluaciones",
        len(df_evaluacion),
    )
    col2.metric(
        "Positivas",
        int(
            (df_evaluacion["RESULTADO"] == "POSITIVA").sum()
        ),
    )
    col3.metric(
        "Negativas",
        int(
            (df_evaluacion["RESULTADO"] == "NEGATIVA").sum()
        ),
    )

    st.dataframe(
        df_evaluacion.head(50),
        width="stretch",
        hide_index=True,
    )

    if st.button(
        "Importar evaluaciones técnicas",
        type="primary",
        key="boton_importar_evaluacion_tecnica",
    ):
        resultado = importar_evaluaciones_tecnicas(
            df=df_evaluacion,
            id_procedimiento=id_procedimiento,
        )
        mostrar_resultado_importacion(resultado)


__all__ = [
    "mostrar_resultado_importacion",
    "mostrar_carga_evaluacion",
]
