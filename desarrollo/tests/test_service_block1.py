"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_service_block1.py

Pruebas del Paso 009.3.2 - Bloque 1.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

import pandas as pd
import pytest

from services.import_engine import procesar_dataframe
from services.import_service import (
    normalizar_dataframe,
    validar_columnas_requeridas,
    validar_dataframe_no_vacio,
)
from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_nombres_columnas,
    normalizar_pais,
    normalizar_rfc,
    normalizar_texto,
)


def test_normalizadores_centrales():
    assert normalizar_texto("  información médica  ") == (
        "INFORMACION MEDICA"
    )

    assert normalizar_rfc(" abc-010101-xy1 ") == "ABC010101XY1"

    assert normalizar_clave(" 010. 000.1234 ") == "010.000.1234"

    assert normalizar_pais("USA / México") == (
        "ESTADOS UNIDOS/MEXICO"
    )

    assert normalizar_decimal("1,250.50") == Decimal("1250.50")


def test_normalizar_nombres_columnas():
    df = pd.DataFrame(
        {
            "RAZÓN SOCIAL": ["PROVEEDOR"],
            "País de Origen": ["MÉXICO"],
            "PRECIO UNITARIO": [100],
        }
    )

    resultado = normalizar_nombres_columnas(df)

    assert list(resultado.columns) == [
        "razon_social",
        "pais_de_origen",
        "precio_unitario",
    ]


def test_normalizar_dataframe_compatibilidad():
    df = pd.DataFrame(
        {
            "RAZÓN SOCIAL": ["PROVEEDOR"],
        }
    )

    resultado = normalizar_dataframe(df)

    assert "razon_social" in resultado.columns


def test_validar_dataframe_vacio():
    df = pd.DataFrame()

    with pytest.raises(ValueError):
        validar_dataframe_no_vacio(df)


def test_validar_columnas_requeridas():
    df = pd.DataFrame(
        {
            "RFC": ["ABC010101XY1"],
            "CLAVE": ["010.000.1234"],
        }
    )

    assert validar_columnas_requeridas(
        df=df,
        columnas_requeridas=["RFC", "CLAVE"],
    )


def test_validar_columnas_faltantes():
    df = pd.DataFrame(
        {
            "RFC": ["ABC010101XY1"],
        }
    )

    with pytest.raises(ValueError) as error:
        validar_columnas_requeridas(
            df=df,
            columnas_requeridas=["RFC", "CLAVE"],
        )

    assert "CLAVE" in str(error.value)


def test_import_engine_resultados():
    df = pd.DataFrame(
        {
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-2",
                "CLAVE-3",
            ]
        }
    )

    def procesar_fila(row):
        if row["CLAVE"] == "CLAVE-1":
            return {
                "accion": "insertado",
            }

        if row["CLAVE"] == "CLAVE-2":
            return {
                "accion": "actualizado",
            }

        return {
            "accion": "omitido",
            "advertencia": "Registro omitido para prueba.",
        }

    resultado = procesar_dataframe(
        df=df,
        columnas_requeridas=["CLAVE"],
        funcion_procesar_fila=procesar_fila,
        tabla="prueba",
        fila_inicial_excel=2,
    )

    assert resultado["success"] is True
    assert resultado["procesados"] == 2
    assert resultado["insertados"] == 1
    assert resultado["actualizados"] == 1
    assert resultado["omitidos"] == 1
    assert len(resultado["advertencias"]) == 1
    assert resultado["advertencias"][0]["fila"] == 4


def test_import_engine_registra_error_de_fila():
    df = pd.DataFrame(
        {
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-2",
            ]
        },
        index=[10, 20],
    )

    def procesar_fila(row):
        if row["CLAVE"] == "CLAVE-2":
            raise ValueError("Error controlado.")

        return {
            "accion": "insertado",
        }

    resultado = procesar_dataframe(
        df=df,
        columnas_requeridas=["CLAVE"],
        funcion_procesar_fila=procesar_fila,
        tabla="prueba",
        fila_inicial_excel=8,
    )

    assert resultado["success"] is False
    assert resultado["insertados"] == 1
    assert len(resultado["errores"]) == 1

    # La segunda posición corresponde a la fila 9 de Excel,
    # independientemente de que su índice Pandas sea 20.
    assert resultado["errores"][0]["fila"] == 9