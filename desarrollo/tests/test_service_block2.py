"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_service_block2.py

Pruebas del Paso 009.3.2 - Bloque 2.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

import pandas as pd

from services.prevalidacion_propuestas_service import (
    eliminar_filas_vacias_propuestas,
    normalizar_archivo_propuestas,
    preparar_dataframe_propuestas,
    validar_contenido_propuestas,
    validar_duplicados_propuestas,
)
from services.prevalidacion_universo_service import (
    eliminar_filas_vacias_universo,
    normalizar_dataframe_universo,
)
from services.validacion_catalogos_service import (
    validar_claves_contra_catalogo,
    validar_procedimiento_existente,
)
from services.validacion_service import (
    NIVEL_ERROR,
    generar_resumen_validacion,
    validar_campos_obligatorios,
    validar_carga_1_universo,
    validar_duplicados,
)


def test_validar_campos_obligatorios_con_indice_irregular():
    df = pd.DataFrame(
        {
            "CLAVE": [
                "CLAVE-1",
                None,
            ],
        },
        index=[10, 25],
    )

    mensajes = validar_campos_obligatorios(
        df=df,
        campos_obligatorios=["CLAVE"],
        fila_inicio_excel=8,
    )

    assert len(mensajes) == 1
    assert mensajes[0]["fila"] == 9
    assert mensajes[0]["nivel"] == NIVEL_ERROR


def test_validar_duplicados_por_varios_campos():
    df = pd.DataFrame(
        {
            "RFC": [
                "RFC001",
                "RFC001",
                "RFC002",
            ],
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-1",
                "CLAVE-1",
            ],
        }
    )

    mensajes = validar_duplicados(
        df=df,
        campos=["RFC", "CLAVE"],
        fila_inicio_excel=2,
    )

    assert len(mensajes) == 2
    assert mensajes[0]["fila"] == 2
    assert mensajes[1]["fila"] == 3


def test_validar_carga_universo_cantidad_opcional():
    df = pd.DataFrame(
        {
            "CLAVE": ["CLAVE-1"],
            "DESCRIPCION": ["DESCRIPCION DE PRUEBA"],
            "CANTIDAD_REQUERIDA": [None],
        }
    )

    resultado = validar_carga_1_universo(
        df=df,
        fila_inicio_excel=8,
    )

    assert resultado["valido"] is True
    assert resultado["resumen"]["errores"] == 0


def test_validar_carga_universo_detecta_clave_duplicada():
    df = pd.DataFrame(
        {
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-1",
            ],
            "DESCRIPCION": [
                "DESCRIPCION",
                "DESCRIPCION",
            ],
            "CANTIDAD_REQUERIDA": [
                None,
                None,
            ],
        }
    )

    resultado = validar_carga_1_universo(
        df=df,
        fila_inicio_excel=8,
    )

    assert resultado["valido"] is False
    assert resultado["resumen"]["errores"] == 2


def test_normalizar_dataframe_universo():
    df = pd.DataFrame(
        {
            "CLAVE": [" 010. 000.1234 "],
            "DESCRIPCION": [" información médica "],
            "CANTIDAD_REQUERIDA": ["1,250.50"],
        }
    )

    resultado = normalizar_dataframe_universo(df)

    assert resultado.iloc[0]["CLAVE"] == "010.000.1234"
    assert (
        resultado.iloc[0]["DESCRIPCION"]
        == "INFORMACION MEDICA"
    )
    assert (
        resultado.iloc[0]["CANTIDAD_REQUERIDA"]
        == Decimal("1250.50")
    )


def test_eliminar_filas_vacias_universo():
    df = pd.DataFrame(
        {
            "CLAVE": [
                None,
                "CLAVE-1",
            ],
            "DESCRIPCION": [
                None,
                "DESCRIPCION",
            ],
            "CANTIDAD_REQUERIDA": [
                None,
                None,
            ],
        }
    )

    resultado = eliminar_filas_vacias_universo(df)

    assert len(resultado) == 1
    assert resultado.iloc[0]["CLAVE"] == "CLAVE-1"


def test_preparar_y_normalizar_propuestas():
    df = pd.DataFrame(
        {
            "rfc": [" abc-010101-xy1 "],
            "razon_social": [" proveedor de prueba "],
            "clave": [" 010. 000.1234 "],
            "descripcion": [" insumo médico "],
            "cantidad_ofertada": ["10"],
            "pais_de_origen": ["México"],
            "precio_unitario": ["1,250.50"],
        }
    )

    preparado = preparar_dataframe_propuestas(df)
    normalizado = normalizar_archivo_propuestas(
        preparado
    )

    assert normalizado.iloc[0]["RFC"] == "ABC010101XY1"
    assert (
        normalizado.iloc[0]["RAZON_SOCIAL"]
        == "PROVEEDOR DE PRUEBA"
    )
    assert (
        normalizado.iloc[0]["CLAVE"]
        == "010.000.1234"
    )
    assert (
        normalizado.iloc[0]["PAIS_ORIGEN"]
        == "MEXICO"
    )
    assert (
        normalizado.iloc[0]["PRECIO_UNITARIO"]
        == Decimal("1250.50")
    )


def test_validar_contenido_propuestas_correcto():
    df = pd.DataFrame(
        {
            "RFC": ["ABC010101XY1"],
            "RAZON_SOCIAL": ["PROVEEDOR"],
            "CLAVE": ["CLAVE-1"],
            "DESCRIPCION": ["DESCRIPCION"],
            "CANTIDAD_OFERTADA": [Decimal("10")],
            "PAIS_ORIGEN": ["MEXICO"],
            "PRECIO_UNITARIO": [Decimal("100")],
        }
    )

    errores = validar_contenido_propuestas(df)

    assert errores == []


def test_validar_contenido_propuestas_numero_invalido():
    df = pd.DataFrame(
        {
            "RFC": ["ABC010101XY1"],
            "RAZON_SOCIAL": ["PROVEEDOR"],
            "CLAVE": ["CLAVE-1"],
            "DESCRIPCION": ["DESCRIPCION"],
            "CANTIDAD_OFERTADA": [Decimal("0")],
            "PAIS_ORIGEN": ["MEXICO"],
            "PRECIO_UNITARIO": [Decimal("-1")],
        }
    )

    errores = validar_contenido_propuestas(df)

    assert len(errores) == 2


def test_validar_duplicados_propuestas():
    df = pd.DataFrame(
        {
            "RFC": [
                "ABC010101XY1",
                "ABC010101XY1",
            ],
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-1",
            ],
        }
    )

    errores = validar_duplicados_propuestas(df)

    assert len(errores) == 2
    assert errores[0]["fila"] == 2
    assert errores[1]["fila"] == 3


def test_eliminar_filas_vacias_propuestas():
    df = pd.DataFrame(
        {
            "RFC": [
                None,
                "ABC010101XY1",
            ],
            "CLAVE": [
                None,
                "CLAVE-1",
            ],
        }
    )

    resultado = eliminar_filas_vacias_propuestas(df)

    assert len(resultado) == 1


def test_validar_procedimiento_existente_repository(
    monkeypatch,
):
    def mock_get_by_numero_procedimiento(
        self,
        numero_procedimiento,
        conn=None,
    ):
        return {
            "id_procedimiento": 15,
            "numero_procedimiento": numero_procedimiento,
        }

    monkeypatch.setattr(
        (
            "repositories.procedimientos_repository."
            "ProcedimientosRepository."
            "get_by_numero_procedimiento"
        ),
        mock_get_by_numero_procedimiento,
    )

    resultado = validar_procedimiento_existente(
        numero_procedimiento=" procedimiento 2026 ",
        conn=object(),
    )

    assert resultado["existe"] is True
    assert resultado["id_procedimiento"] == 15
    assert (
        resultado["numero_procedimiento"]
        == "PROCEDIMIENTO 2026"
    )


def test_validar_claves_contra_catalogo_repository(
    monkeypatch,
):
    def mock_get_by_clave(
        self,
        clave,
        conn=None,
    ):
        if clave == "CLAVE-1":
            return {
                "id_clave": 100,
                "clave": "CLAVE-1",
                "descripcion": "DESCRIPCION",
            }

        return None

    monkeypatch.setattr(
        (
            "repositories.claves_repository."
            "ClavesRepository.get_by_clave"
        ),
        mock_get_by_clave,
    )

    df = pd.DataFrame(
        {
            "CLAVE": [
                "CLAVE-1",
                "CLAVE-2",
            ],
            "DESCRIPCION": [
                "DESCRIPCION 1",
                "DESCRIPCION 2",
            ],
        }
    )

    resultado = validar_claves_contra_catalogo(
        df=df,
        conn=object(),
    )

    assert resultado["success"] is True
    assert resultado["resumen"]["claves_existentes"] == 1
    assert resultado["resumen"]["claves_nuevas"] == 1

    assert resultado["df"].iloc[0]["ID_CLAVE"] == 100
    assert resultado["df"].iloc[0]["ES_NUEVA"] == False
    assert resultado["df"].iloc[1]["ES_NUEVA"] == True


def test_generar_resumen_validacion():
    df = pd.DataFrame(
        {
            "CLAVE": [
                "A",
                "A",
                "B",
            ]
        }
    )

    mensajes = [
        {
            "nivel": NIVEL_ERROR,
            "fila": 2,
            "campo": "CLAVE",
            "valor": "A",
            "mensaje": "Error.",
        }
    ]

    resumen = generar_resumen_validacion(
        df=df,
        mensajes=mensajes,
        campo_clave="CLAVE",
    )

    assert resumen["total_registros"] == 3
    assert resumen["errores"] == 1
    assert resumen["valido"] is False
    assert resumen["claves_unicas"] == 2
    assert resumen["duplicados_clave"] == 1