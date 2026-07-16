"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_dashboard_module.py

Pruebas unitarias para funciones auxiliares del módulo Dashboard.

No ejecutan la interfaz completa ni requieren base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

import pandas as pd

from modules.dashboard import (
    OPCION_TODOS,
    _formatear_decimal,
    _formatear_moneda,
    _formatear_porcentaje,
    _mapa_procedimientos,
    _normalizar_dataframe,
    _obtener_ejercicios,
    _valor_entero,
)


def test_valor_entero():
    assert _valor_entero(5) == 5
    assert _valor_entero(Decimal("4")) == 4
    assert _valor_entero(None) == 0
    assert _valor_entero("incorrecto") == 0


def test_formatear_decimal():
    assert _formatear_decimal(Decimal("1234.5")) == "1,234.50"
    assert _formatear_decimal(None) == "Sin información"


def test_formatear_porcentaje():
    assert _formatear_porcentaje(Decimal("75")) == "75.00%"
    assert _formatear_porcentaje(None) == "Sin evaluaciones"


def test_formatear_moneda():
    assert _formatear_moneda(Decimal("120.5")) == "$120.50"
    assert _formatear_moneda(None) == "Sin información"


def test_normalizar_dataframe_vacio():
    resultado = _normalizar_dataframe([])

    assert isinstance(resultado, pd.DataFrame)
    assert resultado.empty


def test_normalizar_dataframe_con_registros():
    resultado = _normalizar_dataframe(
        [{"clave": "001", "total": 2}]
    )

    assert list(resultado.columns) == ["clave", "total"]
    assert resultado.iloc[0]["clave"] == "001"


def test_mapa_procedimientos():
    procedimientos = [
        {
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-010",
            "ejercicio": 2026,
        },
        {
            "id_procedimiento": 11,
            "numero_procedimiento": "PROC-011",
            "ejercicio": None,
        },
    ]

    resultado = _mapa_procedimientos(procedimientos)

    assert resultado[OPCION_TODOS] is None
    assert resultado["PROC-010 — 2026"] == 10
    assert resultado["PROC-011"] == 11


def test_obtener_ejercicios_elimina_duplicados():
    ejercicios = [
        {"ejercicio": 2026},
        {"ejercicio": 2025},
        {"ejercicio": 2026},
        {"ejercicio": None},
    ]

    resultado = _obtener_ejercicios(ejercicios)

    assert resultado == [2026, 2025]