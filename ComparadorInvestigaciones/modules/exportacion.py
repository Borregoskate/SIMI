"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

Archivo:
modules/exportacion.py

Descripción:
Generación y descarga de archivo Excel con análisis consolidado.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from utils.helpers import (
    formatear_moneda,
    limpiar_nombre_hoja_excel,
)


def generar_excel_analisis(df: pd.DataFrame) -> BytesIO:
    """
    Genera un archivo Excel con varias hojas de análisis.
    """

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # Hoja 1: Datos completos
        df.to_excel(
            writer,
            sheet_name="Datos completos",
            index=False
        )

        # Hoja 2: Resumen general
        resumen_general = pd.DataFrame(
            {
                "Indicador": [
                    "Total investigaciones",
                    "Total registros",
                    "Total claves",
                    "Total proveedores",
                    "Precio mínimo",
                    "Precio máximo",
                    "Precio promedio",
                ],
                "Valor": [
                    df["INVESTIGACION"].nunique(),
                    len(df),
                    df["CLAVE"].nunique(),
                    df["RAZON SOCIAL"].nunique(),
                    df["PRECIO UNITARIO"].min(),
                    df["PRECIO UNITARIO"].max(),
                    df["PRECIO UNITARIO"].mean(),
                ],
            }
        )

        resumen_general.to_excel(
            writer,
            sheet_name="Resumen general",
            index=False
        )

        # Hoja 3: Resumen por clave
        resumen_clave = (
            df.groupby("CLAVE")
            .agg(
                descripcion=("DESCRIPCION", "first"),
                investigaciones=("INVESTIGACION", "nunique"),
                proveedores=("RAZON SOCIAL", "nunique"),
                registros=("CLAVE", "count"),
                cantidad_total=("CANTIDAD OFERTADA", "sum"),
                precio_minimo=("PRECIO UNITARIO", "min"),
                precio_maximo=("PRECIO UNITARIO", "max"),
                precio_promedio=("PRECIO UNITARIO", "mean"),
            )
            .reset_index()
            .sort_values("CLAVE")
        )

        resumen_clave.to_excel(
            writer,
            sheet_name="Resumen por clave",
            index=False
        )

        # Hoja 4: Resumen por proveedor
        resumen_proveedor = (
            df.groupby(["RFC", "RAZON SOCIAL"])
            .agg(
                investigaciones=("INVESTIGACION", "nunique"),
                claves=("CLAVE", "nunique"),
                registros=("CLAVE", "count"),
                cantidad_total=("CANTIDAD OFERTADA", "sum"),
                precio_minimo=("PRECIO UNITARIO", "min"),
                precio_maximo=("PRECIO UNITARIO", "max"),
                precio_promedio=("PRECIO UNITARIO", "mean"),
            )
            .reset_index()
            .sort_values("RAZON SOCIAL")
        )

        resumen_proveedor.to_excel(
            writer,
            sheet_name="Resumen proveedor",
            index=False
        )

        # Hoja 5: Proveedores unificados
        proveedores = (
            df[["RFC", "RAZON SOCIAL"]]
            .drop_duplicates()
            .sort_values("RAZON SOCIAL")
        )

        proveedores.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False
        )

        # Hoja 6: Resumen por investigación
        resumen_investigacion = (
            df.groupby("INVESTIGACION")
            .agg(
                archivo=("ARCHIVO", "first"),
                registros=("CLAVE", "count"),
                claves=("CLAVE", "nunique"),
                proveedores=("RAZON SOCIAL", "nunique"),
                precio_minimo=("PRECIO UNITARIO", "min"),
                precio_maximo=("PRECIO UNITARIO", "max"),
                precio_promedio=("PRECIO UNITARIO", "mean"),
            )
            .reset_index()
            .sort_values("INVESTIGACION")
        )

        resumen_investigacion.to_excel(
            writer,
            sheet_name="Resumen investigacion",
            index=False
        )

    output.seek(0)

    return output


def mostrar_exportacion(df: pd.DataFrame) -> None:
    """
    Muestra el botón de descarga del Excel.
    """

    st.subheader("📥 Exportación")

    archivo_excel = generar_excel_analisis(df)

    st.download_button(
        label="📥 Descargar análisis completo en Excel",
        data=archivo_excel,
        file_name="SIMI_analisis_investigaciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )