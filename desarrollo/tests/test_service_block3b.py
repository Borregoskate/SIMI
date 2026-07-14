"""
Pruebas unitarias del Bloque 3B.

Ejecutar desde /desarrollo:

    python -m pytest tests/test_service_block3b.py -v
"""

from decimal import Decimal
from numbers import Integral

import pandas as pd
import pytest

from services.adjudicaciones_service import preparar_adjudicaciones
from services.evaluaciones_tecnicas_service import preparar_evaluaciones
from services.subasta_service import preparar_subasta
from utils.normalizadores import (
    normalizar_entero,
    normalizar_razon_social,
)


# ==========================================================
# NORMALIZADORES TRANSVERSALES
# ==========================================================

@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (
            "Laboratorios ejemplo sa de cv",
            "LABORATORIOS EJEMPLO S.A. DE C.V.",
        ),
        (
            "Empresa Médica, S. de R.L. de C.V.",
            "EMPRESA MEDICA S. DE R.L. DE C.V.",
        ),
        (
            "  proveedor   nacional S A DE C V ",
            "PROVEEDOR NACIONAL S.A. DE C.V.",
        ),
    ],
)
def test_normalizar_razon_social_societaria(entrada, esperado):
    assert normalizar_razon_social(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (100, 100),
        (100.0, 100),
        ("100", 100),
        ("1,000", 1000),
    ],
)
def test_normalizar_entero_acepta_enteros(entrada, esperado):
    assert normalizar_entero(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [100.5, "100.50", "ABC", True],
)
def test_normalizar_entero_rechaza_fracciones_o_invalidos(entrada):
    assert normalizar_entero(entrada) is None


# ==========================================================
# EVALUACIÓN TÉCNICA
# ==========================================================

def test_preparar_evaluaciones_rellena_procedimiento_y_descarta_observaciones():
    df = pd.DataFrame(
        {
            "Procedimiento": ["IM-014-2026", None],
            "RFC": ["abc010101abc", "xyz010101xyz"],
            "Razón social": [
                "Proveedor uno sa de cv",
                "Proveedor dos s de rl de cv",
            ],
            "Clave": ["010.001", "010.002"],
            "Opinión Técnica": [
                "OPINION POSITIVA",
                "Opinión negativa",
            ],
            "Observaciones": [
                "No debe conservarse",
                "Tampoco debe conservarse",
            ],
        }
    )

    resultado = preparar_evaluaciones(df)

    assert resultado["procedimiento"].tolist() == [
        "IM-014-2026",
        "IM-014-2026",
    ]
    assert resultado["resultado"].tolist() == [
        "POSITIVA",
        "NEGATIVA",
    ]
    assert "observaciones" not in resultado.columns
    assert resultado.loc[0, "razon_social"].endswith("S.A. DE C.V.")
    assert resultado.loc[1, "razon_social"].endswith(
        "S. DE R.L. DE C.V."
    )


def test_preparar_evaluaciones_rechaza_resultado_desconocido():
    df = pd.DataFrame(
        {
            "Procedimiento": ["IM-014-2026"],
            "RFC": ["ABC010101ABC"],
            "Razón social": ["Proveedor sa de cv"],
            "Clave": ["010.001"],
            "Opinión Técnica": ["PENDIENTE"],
        }
    )

    with pytest.raises(ValueError, match="resultado"):
        preparar_evaluaciones(df)


def test_preparar_evaluaciones_rechaza_duplicado_logico():
    df = pd.DataFrame(
        {
            "Procedimiento": ["IM-014-2026", "IM-014-2026"],
            "RFC": ["ABC010101ABC", "ABC010101ABC"],
            "Razón social": [
                "Proveedor sa de cv",
                "Proveedor sa de cv",
            ],
            "Clave": ["010.001", "010.001"],
            "Opinión Técnica": [
                "OPINION POSITIVA",
                "OPINION NEGATIVA",
            ],
        }
    )

    with pytest.raises(ValueError, match="duplicadas"):
        preparar_evaluaciones(df)


# ==========================================================
# SUBASTA
# ==========================================================

def dataframe_subasta():
    return pd.DataFrame(
        {
            "RFC": ["ABC010101ABC"],
            "Razón social": ["Laboratorios ejemplo sa de cv"],
            "Clave": ["010.001"],
            "Descripción": ["Medicamento de prueba"],
            "Cantidad ofertada": [100.0],
            "País de origen": ["México"],
            "Precio unitario": ["125.50"],
        }
    )


def test_preparar_subasta_normaliza_y_asigna_tipo():
    resultado = preparar_subasta(dataframe_subasta())

    assert resultado.loc[0, "rfc"] == "ABC010101ABC"
    assert resultado.loc[0, "razon_social"] == (
        "LABORATORIOS EJEMPLO S.A. DE C.V."
    )
    assert resultado.loc[0, "cantidad_ofertada"] == 100
    assert isinstance(resultado.loc[0, "cantidad_ofertada"], Integral)
    assert resultado.loc[0, "pais_origen"] == "MEXICO"
    assert resultado.loc[0, "precio_unitario"] == Decimal("125.50")
    assert resultado.loc[0, "tipo_propuesta"] == "SUBASTA"


def test_preparar_subasta_rechaza_cantidad_fraccionaria():
    df = dataframe_subasta()
    df.loc[0, "Cantidad ofertada"] = 100.5

    with pytest.raises(ValueError, match="cantidad_ofertada"):
        preparar_subasta(df)


def test_preparar_subasta_rechaza_precio_no_positivo():
    df = dataframe_subasta()
    df.loc[0, "Precio unitario"] = "0"

    with pytest.raises(ValueError, match="precio unitario"):
        preparar_subasta(df)


def test_preparar_subasta_rechaza_duplicado_rfc_clave():
    df = pd.concat(
        [dataframe_subasta(), dataframe_subasta()],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicadas"):
        preparar_subasta(df)


# ==========================================================
# ADJUDICACIONES
# ==========================================================

def dataframe_adjudicaciones():
    return pd.DataFrame(
        {
            "Procedimiento": ["IM-014-2026", "IM-014-2026"],
            "Clave": ["010.001", "010.001"],
            "RFC": ["AAA010101AAA", "BBB010101BBB"],
            "Licitante": [
                "Proveedor uno sa de cv",
                "Proveedor dos s de rl de cv",
            ],
            "Precio Unitario": ["10.50", "11.00"],
            "Cantidad Max.": [60, 40],
            # Deben ignorarse completamente:
            "Cantidad Min.": [20, 10],
            "Monto Máx.": [630, 440],
            "IVA Max": [0, 0],
            "Monto Total MAX.": [999999, 999999],
        }
    )


def test_preparar_adjudicaciones_mapea_cantidad_maxima():
    resultado = preparar_adjudicaciones(dataframe_adjudicaciones())

    assert resultado["cantidad_adjudicada"].tolist() == [60, 40]
    assert resultado["precio_unitario_adjudicado"].tolist() == [
        Decimal("10.50"),
        Decimal("11.00"),
    ]


def test_preparar_adjudicaciones_calcula_porcentajes_por_clave():
    resultado = preparar_adjudicaciones(dataframe_adjudicaciones())

    assert resultado["porcentaje_adjudicado"].tolist() == [
        Decimal("60.00"),
        Decimal("40.00"),
    ]


def test_adjudicacion_unico_proveedor_recibe_cien_por_ciento():
    df = dataframe_adjudicaciones().iloc[[0]].copy()

    resultado = preparar_adjudicaciones(df)

    assert resultado.loc[0, "porcentaje_adjudicado"] == Decimal("100.00")


def test_porcentajes_se_calculan_independientemente_por_clave():
    df = pd.DataFrame(
        {
            "Procedimiento": [
                "IM-014-2026",
                "IM-014-2026",
                "IM-014-2026",
            ],
            "Clave": ["A", "A", "B"],
            "RFC": [
                "AAA010101AAA",
                "BBB010101BBB",
                "CCC010101CCC",
            ],
            "Licitante": [
                "Proveedor uno sa de cv",
                "Proveedor dos sa de cv",
                "Proveedor tres sa de cv",
            ],
            "Precio Unitario": [10, 10, 10],
            "Cantidad Max.": [30, 70, 25],
        }
    )

    resultado = preparar_adjudicaciones(df)

    assert resultado["porcentaje_adjudicado"].tolist() == [
        Decimal("30.00"),
        Decimal("70.00"),
        Decimal("100.00"),
    ]


def test_preparar_adjudicaciones_rechaza_cantidad_fraccionaria():
    df = dataframe_adjudicaciones()
    df["Cantidad Max."] = df["Cantidad Max."].astype(object)
    df.loc[0, "Cantidad Max."] = 60.5

    with pytest.raises(ValueError, match="cantidad_adjudicada"):
        preparar_adjudicaciones(df)


def test_preparar_adjudicaciones_permite_dos_proveedores_misma_clave():
    resultado = preparar_adjudicaciones(dataframe_adjudicaciones())

    assert len(resultado) == 2
    assert resultado["clave"].nunique() == 1
    assert resultado["rfc"].nunique() == 2


def test_preparar_adjudicaciones_rechaza_mismo_proveedor_duplicado():
    df = dataframe_adjudicaciones()
    df.loc[1, "RFC"] = df.loc[0, "RFC"]

    with pytest.raises(ValueError, match="duplicadas"):
        preparar_adjudicaciones(df)
