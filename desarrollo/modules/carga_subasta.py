"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_subasta.py

Módulo visual para la Carga 4:
Subasta Privada.

Responsabilidades:
- Mostrar procedimientos activos.
- Recibir el archivo Excel.
- Ejecutar la prevalidación.
- Mostrar una vista previa normalizada.
- Solicitar la importación.
- Mostrar insertados, actualizados, omitidos y errores.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
import streamlit as st

from services.prevalidacion_subasta_service import (
    prevalidar_archivo_subasta,
)
from services.subasta_import_service import (
    importar_subasta_privada,
    obtener_procedimientos_activos,
)


def mostrar_resultado_importacion(resultado):
    """Muestra el resumen devuelto por el motor de importación."""
    if resultado.get("success"):
        st.success(
            "Las propuestas de subasta se importaron correctamente."
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
        st.subheader("Errores")
        st.dataframe(
            pd.DataFrame(resultado["errores"]),
            width="stretch",
            hide_index=True,
        )

    if resultado.get("advertencias"):
        st.subheader("Advertencias")
        st.dataframe(
            pd.DataFrame(resultado["advertencias"]),
            width="stretch",
            hide_index=True,
        )


def mostrar_carga_subasta():
    """Renderiza la interfaz completa de la Carga 4."""
    st.header("Carga 4 - Subasta Privada")

    st.info(
        "Solo podrán importarse posturas de proveedores que tengan "
        "una propuesta inicial y una evaluación técnica POSITIVA "
        "para la clave seleccionada."
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
        key="procedimiento_subasta_privada",
    )
    id_procedimiento = opciones[seleccion]

    archivo = st.file_uploader(
        "Carga el archivo Excel de subasta privada",
        type=["xlsx", "xls"],
        key="archivo_subasta_privada",
    )

    if archivo is None:
        return

    prevalidacion = prevalidar_archivo_subasta(
        archivo
    )

    if not prevalidacion.get("valido"):
        st.error(
            "El archivo contiene errores de prevalidación."
        )

        errores = prevalidacion.get("errores", [])

        if errores:
            st.dataframe(
                pd.DataFrame(errores),
                width="stretch",
                hide_index=True,
            )

        return

    df_subasta = prevalidacion.get("df")

    if df_subasta is None or df_subasta.empty:
        st.warning(
            "El archivo no contiene propuestas de subasta "
            "para importar."
        )
        return

    st.success(
        "Archivo prevalidado correctamente."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Posturas",
        len(df_subasta),
    )
    col2.metric(
        "Proveedores",
        int(df_subasta["RFC"].nunique()),
    )
    col3.metric(
        "Claves",
        int(df_subasta["CLAVE"].nunique()),
    )

    st.subheader("Vista previa normalizada")

    st.dataframe(
        df_subasta.head(50),
        width="stretch",
        hide_index=True,
    )

    st.warning(
        "Al importar, SIMI insertará nuevas propuestas SUBASTA, "
        "actualizará las existentes cuando cambien sus valores y "
        "omitirá las que ya sean idénticas."
    )

    confirmar = st.checkbox(
        "Confirmo que deseo importar estas propuestas de subasta.",
        key="confirmar_importacion_subasta_privada",
    )

    if st.button(
        "Importar propuestas de subasta",
        type="primary",
        key="boton_importar_subasta_privada",
        disabled=not confirmar,
    ):
        resultado = importar_subasta_privada(
            df=df_subasta,
            id_procedimiento=id_procedimiento,
        )
        mostrar_resultado_importacion(resultado)


__all__ = [
    "mostrar_resultado_importacion",
    "mostrar_carga_subasta",
]