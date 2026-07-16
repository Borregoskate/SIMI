"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

proveedores.py

Componente visual del detalle por proveedor para
Análisis por Clave.

Responsabilidades:
- Mostrar la participación de cada proveedor.
- Mostrar oferta inicial, evaluación, subasta y adjudicación.
- Presentar únicamente datos ya preparados por
  AnalisisClaveService.

Este componente:
- No ejecuta SQL.
- No calcula estados.
- No evalúa reglas técnicas.
- No transforma datos de negocio.
- No modifica la información recibida.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
import streamlit as st

from modules.analisis_clave_ui.utilidades import (
    formatear_moneda,
    formatear_numero,
    formatear_porcentaje,
    formatear_si_no,
)


COLUMNAS_PROVEEDORES = {
    "numero_procedimiento": "Procedimiento",
    "ejercicio": "Ejercicio",
    "rfc": "RFC",
    "razon_social": "Razón social",
    "tiene_oferta_inicial": "Oferta inicial",
    "cantidad_inicial": "Cantidad inicial",
    "precio_inicial": "Precio inicial",
    "evaluado": "Evaluado",
    "resultado_tecnico": "Resultado técnico",
    "aprobado_tecnicamente": "Aprobado",
    "tiene_subasta": "Participó en subasta",
    "cantidad_subasta": "Cantidad subasta",
    "precio_subasta": "Precio subasta",
    "adjudicado": "Adjudicado",
    "cantidad_adjudicada": "Cantidad adjudicada",
    "porcentaje_adjudicado": "% adjudicado",
    "precio_adjudicado": "Precio adjudicado",
}


def _preparar_dataframe(registros):
    """Construye el DataFrame visual del detalle por proveedor."""
    filas = []

    for registro in registros or []:
        item = dict(registro)

        filas.append(
            {
                "numero_procedimiento": (
                    item.get("numero_procedimiento")
                    or "Sin procedimiento"
                ),
                "ejercicio": item.get("ejercicio"),
                "rfc": item.get("rfc") or "Sin RFC",
                "razon_social": (
                    item.get("razon_social")
                    or "Sin razón social"
                ),
                "tiene_oferta_inicial": formatear_si_no(
                    item.get("tiene_oferta_inicial")
                ),
                "cantidad_inicial": formatear_numero(
                    item.get("cantidad_inicial")
                ),
                "precio_inicial": formatear_moneda(
                    item.get("precio_inicial")
                ),
                "evaluado": formatear_si_no(
                    item.get("evaluado")
                ),
                "resultado_tecnico": (
                    item.get("resultado_tecnico")
                    or "Sin evaluación"
                ),
                "aprobado_tecnicamente": formatear_si_no(
                    item.get("aprobado_tecnicamente")
                ),
                "tiene_subasta": formatear_si_no(
                    item.get("tiene_subasta")
                ),
                "cantidad_subasta": formatear_numero(
                    item.get("cantidad_subasta")
                ),
                "precio_subasta": formatear_moneda(
                    item.get("precio_subasta")
                ),
                "adjudicado": formatear_si_no(
                    item.get("adjudicado")
                ),
                "cantidad_adjudicada": formatear_numero(
                    item.get("cantidad_adjudicada")
                ),
                "porcentaje_adjudicado": formatear_porcentaje(
                    item.get("porcentaje_adjudicado")
                ),
                "precio_adjudicado": formatear_moneda(
                    item.get("precio_adjudicado")
                ),
            }
        )

    dataframe = pd.DataFrame(filas)

    if dataframe.empty:
        return dataframe

    return dataframe.rename(columns=COLUMNAS_PROVEEDORES)


def mostrar_detalle_proveedores(resultado):
    """Muestra la tabla de participación por proveedor."""
    resultado = resultado or {}
    tablas = resultado.get("tablas", {}) or {}
    registros = tablas.get("detalle_proveedores", []) or []

    st.subheader("Detalle por proveedor")

    if not registros:
        st.info(
            "No existen proveedores para los filtros seleccionados."
        )
        return

    dataframe = _preparar_dataframe(registros)

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "La evaluación técnica se presenta únicamente con base en "
        "el resultado POSITIVA o NEGATIVA registrado para cada "
        "proveedor y clave."
    )
