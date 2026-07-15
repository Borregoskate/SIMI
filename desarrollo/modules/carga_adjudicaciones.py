"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

carga_adjudicaciones.py

Módulo visual para la Carga 5:
Adjudicaciones.

Responsabilidades:
- Mostrar procedimientos activos.
- Recibir el archivo Excel.
- Ejecutar la prevalidación.
- Mostrar una vista previa normalizada.
- Mostrar cantidades y porcentajes calculados.
- Solicitar confirmación antes de importar.
- Mostrar insertados, actualizados, omitidos y errores.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
import streamlit as st

from services.adjudicaciones_import_service import (
    importar_adjudicaciones,
    obtener_procedimientos_activos,
)
from services.prevalidacion_adjudicaciones_service import (
    prevalidar_archivo_adjudicaciones,
)


def mostrar_resultado_importacion(resultado):
    """Muestra el resumen devuelto por el motor de importación."""
    if resultado.get("success"):
        st.success(
            "Las adjudicaciones se importaron correctamente."
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


def mostrar_resumen_por_clave(df_adjudicaciones):
    """
    Muestra el resumen de cantidades y porcentajes por clave.
    """
    resumen = (
        df_adjudicaciones.groupby(
            "CLAVE",
            as_index=False,
        )
        .agg(
            PROVEEDORES=("RFC", "nunique"),
            CANTIDAD_TOTAL=(
                "CANTIDAD_ADJUDICADA",
                "sum",
            ),
            PORCENTAJE_TOTAL=(
                "PORCENTAJE_ADJUDICADO",
                "sum",
            ),
        )
    )

    st.subheader("Resumen por clave")

    st.dataframe(
        resumen,
        width="stretch",
        hide_index=True,
    )

    porcentajes_invalidos = resumen[
        resumen["PORCENTAJE_TOTAL"] != 100
    ]

    if porcentajes_invalidos.empty:
        st.success(
            "Todas las claves tienen porcentajes que suman "
            "exactamente 100."
        )
    else:
        st.error(
            "Existen claves cuyos porcentajes no suman 100."
        )


def mostrar_carga_adjudicaciones():
    """Renderiza la interfaz completa de la Carga 5."""
    st.header("Carga 5 - Adjudicaciones")

    st.info(
        "La cantidad adjudicada se obtiene de la columna "
        "'Cantidad Max.' del archivo. El porcentaje se calcula "
        "automáticamente por clave y se guarda como número entero."
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
        key="procedimiento_adjudicaciones",
    )
    id_procedimiento = opciones[seleccion]

    archivo = st.file_uploader(
        "Carga el archivo Excel de adjudicaciones",
        type=["xlsx", "xls"],
        key="archivo_adjudicaciones",
    )

    if archivo is None:
        return

    prevalidacion = prevalidar_archivo_adjudicaciones(
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

        df_error = prevalidacion.get("df")

        if df_error is not None and not df_error.empty:
            st.subheader("Vista previa disponible")

            st.dataframe(
                df_error.head(50),
                width="stretch",
                hide_index=True,
            )

        return

    df_adjudicaciones = prevalidacion.get("df")

    if (
        df_adjudicaciones is None
        or df_adjudicaciones.empty
    ):
        st.warning(
            "El archivo no contiene adjudicaciones "
            "para importar."
        )
        return

    st.success(
        "Archivo prevalidado correctamente."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Adjudicaciones",
        len(df_adjudicaciones),
    )
    col2.metric(
        "Proveedores",
        int(df_adjudicaciones["RFC"].nunique()),
    )
    col3.metric(
        "Claves",
        int(df_adjudicaciones["CLAVE"].nunique()),
    )
    col4.metric(
        "Cantidad total",
        float(
            df_adjudicaciones[
                "CANTIDAD_ADJUDICADA"
            ].sum()
        ),
    )

    st.subheader("Vista previa normalizada")

    columnas_vista = [
        "PROCEDIMIENTO",
        "CLAVE",
        "DESCRIPCION",
        "RFC",
        "RAZON_SOCIAL",
        "CANTIDAD_ADJUDICADA",
        "PORCENTAJE_ADJUDICADO",
        "PRECIO_UNITARIO_ADJUDICADO",
    ]

    st.dataframe(
        df_adjudicaciones[
            columnas_vista
        ].head(100),
        width="stretch",
        hide_index=True,
    )

    mostrar_resumen_por_clave(
        df_adjudicaciones
    )

    st.warning(
        "Al importar, SIMI insertará nuevas adjudicaciones, "
        "actualizará las existentes cuando cambien cantidad, "
        "porcentaje o precio, y omitirá las que ya sean idénticas."
    )

    confirmar = st.checkbox(
        "Confirmo que deseo importar estas adjudicaciones.",
        key="confirmar_importacion_adjudicaciones",
    )

    if st.button(
        "Importar adjudicaciones",
        type="primary",
        key="boton_importar_adjudicaciones",
        disabled=not confirmar,
    ):
        resultado = importar_adjudicaciones(
            df=df_adjudicaciones,
            id_procedimiento=id_procedimiento,
        )

        mostrar_resultado_importacion(
            resultado
        )


__all__ = [
    "mostrar_resultado_importacion",
    "mostrar_resumen_por_clave",
    "mostrar_carga_adjudicaciones",
]