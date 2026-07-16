"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_dashboard_service.py

Pruebas unitarias para DashboardService.

No requieren conexión real a PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

from services.dashboard_service import DashboardService


class DashboardRepositoryFake:
    def obtener_indicadores_principales(self, **kwargs):
        return {
            "total_procedimientos": 1,
            "total_claves": 3,
            "total_proveedores_participantes": 4,
            "total_propuestas_iniciales": 5,
            "total_claves_adjudicadas": 1,
            "total_claves_desiertas": 1,
        }

    def obtener_competencia_por_clave(self, **kwargs):
        return [
            {"id_clave": 1, "total_proveedores": 3},
            {"id_clave": 2, "total_proveedores": 2},
            {"id_clave": 3, "total_proveedores": 0},
        ]

    def obtener_estado_claves(self, **kwargs):
        return [
            {
                "id_clave": 1,
                "proveedores_oferta_inicial": 3,
                "evaluaciones_positivas": 2,
                "tiene_adjudicacion": True,
            },
            {
                "id_clave": 2,
                "proveedores_oferta_inicial": 2,
                "evaluaciones_positivas": 0,
                "tiene_adjudicacion": False,
            },
            {
                "id_clave": 3,
                "proveedores_oferta_inicial": 0,
                "evaluaciones_positivas": 0,
                "tiene_adjudicacion": False,
            },
        ]

    def obtener_aprobacion_por_proveedor(self, **kwargs):
        return [
            {
                "id_proveedor": 1,
                "total_evaluaciones": 4,
                "evaluaciones_positivas": 3,
                "evaluaciones_negativas": 1,
            }
        ]

    def obtener_participacion_proveedores(self, **kwargs):
        return [
            {
                "id_proveedor": 1,
                "presento_oferta_inicial": True,
                "participo_subasta": True,
                "claves_adjudicadas": 1,
            }
        ]

    def obtener_precios_por_clave(self, **kwargs):
        return [
            {
                "id_clave": 1,
                "mejor_precio_inicial": Decimal("120"),
                "mejor_precio_viable": Decimal("100"),
                "mejor_precio_subasta": Decimal("90"),
            }
        ]

    def obtener_resumen_competencia_procedimientos(
        self,
        **kwargs,
    ):
        return [{"id_procedimiento": 1}]

    def obtener_procedimientos_filtro(self, **kwargs):
        return [{"id_procedimiento": 1}]

    def obtener_ejercicios_filtro(self, **kwargs):
        return [{"ejercicio": 2026}]


def test_calcular_porcentaje():
    resultado = DashboardService.calcular_porcentaje(3, 4)

    assert resultado == Decimal("75.00")


def test_calcular_porcentaje_division_cero():
    resultado = DashboardService.calcular_porcentaje(5, 0)

    assert resultado == Decimal("0")


def test_clasificar_competencia_clave():
    assert (
        DashboardService.clasificar_competencia_clave(0)
        == "SIN PARTICIPACIÓN"
    )
    assert (
        DashboardService.clasificar_competencia_clave(1)
        == "COMPETENCIA NULA"
    )
    assert (
        DashboardService.clasificar_competencia_clave(2)
        == "COMPETENCIA BAJA"
    )
    assert (
        DashboardService.clasificar_competencia_clave(4)
        == "COMPETENCIA MEDIA"
    )
    assert (
        DashboardService.clasificar_competencia_clave(5)
        == "COMPETENCIA ALTA"
    )


def test_calcular_resumen_competencia_incluye_claves_sin_oferta():
    registros = [
        {"total_proveedores": 3},
        {"total_proveedores": 2},
        {"total_proveedores": 0},
    ]

    resultado = DashboardService.calcular_resumen_competencia(
        registros
    )

    assert resultado["total_claves"] == 3
    assert (
        resultado["promedio_proveedores_por_clave"]
        == Decimal("1.67")
    )
    assert (
        resultado["puntuacion_promedio_competencia"]
        == Decimal("1.67")
    )
    assert resultado["nivel_competencia"] == "COMPETENCIA BAJA"


def test_clasificar_estado_clave():
    assert DashboardService.clasificar_estado_clave(
        {
            "proveedores_oferta_inicial": 0,
            "evaluaciones_positivas": 0,
            "tiene_adjudicacion": False,
        }
    ) == "DESIERTA"

    assert DashboardService.clasificar_estado_clave(
        {
            "proveedores_oferta_inicial": 2,
            "evaluaciones_positivas": 0,
            "tiene_adjudicacion": False,
        }
    ) == "SIN APROBACIÓN TÉCNICA"

    assert DashboardService.clasificar_estado_clave(
        {
            "proveedores_oferta_inicial": 2,
            "evaluaciones_positivas": 1,
            "tiene_adjudicacion": False,
        }
    ) == "CON APROBADOS SIN ADJUDICACIÓN"

    assert DashboardService.clasificar_estado_clave(
        {
            "proveedores_oferta_inicial": 2,
            "evaluaciones_positivas": 1,
            "tiene_adjudicacion": True,
        }
    ) == "ADJUDICADA"


def test_procesar_aprobacion_proveedores():
    registros = [
        {
            "id_proveedor": 1,
            "total_evaluaciones": 4,
            "evaluaciones_positivas": 3,
            "evaluaciones_negativas": 1,
        },
        {
            "id_proveedor": 2,
            "total_evaluaciones": 0,
            "evaluaciones_positivas": 0,
            "evaluaciones_negativas": 0,
        },
    ]

    resultado = (
        DashboardService.procesar_aprobacion_proveedores(
            registros
        )
    )

    assert resultado[0]["porcentaje_aprobacion"] == Decimal(
        "75.00"
    )
    assert resultado[0]["estado_aprobacion"] == "EVALUADO"
    assert resultado[1]["porcentaje_aprobacion"] is None
    assert (
        resultado[1]["estado_aprobacion"]
        == "SIN EVALUACIONES"
    )


def test_procesar_precios_con_ahorro():
    registros = [
        {
            "mejor_precio_inicial": "120",
            "mejor_precio_viable": "100",
            "mejor_precio_subasta": "90",
        }
    ]

    resultado = DashboardService.procesar_precios_por_clave(
        registros
    )[0]

    assert resultado["ahorro_unitario_subasta"] == Decimal(
        "10.00"
    )
    assert resultado["ahorro_porcentual_subasta"] == Decimal(
        "10.00"
    )
    assert resultado["estado_ahorro_subasta"] == "AHORRO"


def test_procesar_precios_con_incremento():
    registros = [
        {
            "mejor_precio_viable": "100",
            "mejor_precio_subasta": "110",
        }
    ]

    resultado = DashboardService.procesar_precios_por_clave(
        registros
    )[0]

    assert resultado["ahorro_unitario_subasta"] == Decimal(
        "-10.00"
    )
    assert resultado["ahorro_porcentual_subasta"] == Decimal(
        "-10.00"
    )
    assert (
        resultado["estado_ahorro_subasta"]
        == "INCREMENTO DE PRECIO"
    )


def test_procesar_precios_sin_informacion_suficiente():
    registros = [
        {
            "mejor_precio_viable": "100",
            "mejor_precio_subasta": None,
        }
    ]

    resultado = DashboardService.procesar_precios_por_clave(
        registros
    )[0]

    assert resultado["ahorro_unitario_subasta"] is None
    assert resultado["ahorro_porcentual_subasta"] is None
    assert (
        resultado["estado_ahorro_subasta"]
        == "INFORMACIÓN INSUFICIENTE"
    )


def test_completar_indicadores():
    indicadores = {
        "total_claves": 4,
        "total_claves_adjudicadas": 3,
    }
    resumen = {
        "promedio_proveedores_por_clave": Decimal("2.25"),
        "puntuacion_promedio_competencia": Decimal("2.50"),
        "nivel_competencia": "COMPETENCIA MEDIA",
    }

    resultado = DashboardService.completar_indicadores(
        indicadores,
        resumen,
    )

    assert (
        resultado["porcentaje_claves_adjudicadas"]
        == Decimal("75.00")
    )
    assert (
        resultado["promedio_proveedores_por_clave"]
        == Decimal("2.25")
    )
    assert resultado["nivel_competencia"] == (
        "COMPETENCIA MEDIA"
    )


def test_obtener_dashboard_construye_respuesta_completa():
    service = DashboardService(
        repository=DashboardRepositoryFake()
    )

    resultado = service.obtener_dashboard(
        id_procedimiento=1,
        ejercicio=2026,
        id_clave=1,
    )

    assert resultado["filtros"] == {
        "id_procedimiento": 1,
        "ejercicio": 2026,
        "id_clave": 1,
    }
    assert (
        resultado["indicadores"][
            "porcentaje_claves_adjudicadas"
        ]
        == Decimal("33.33")
    )
    assert (
        resultado["indicadores"][
            "promedio_proveedores_por_clave"
        ]
        == Decimal("1.67")
    )
    assert (
        resultado["tablas"]["estado_claves"][0][
            "estado_analitico"
        ]
        == "ADJUDICADA"
    )
    assert (
        resultado["tablas"]["precios_claves"][0][
            "ahorro_unitario_subasta"
        ]
        == Decimal("10.00")
    )


def test_obtener_catalogos_filtros():
    service = DashboardService(
        repository=DashboardRepositoryFake()
    )

    resultado = service.obtener_catalogos_filtros()

    assert resultado["procedimientos"] == [
        {"id_procedimiento": 1}
    ]
    assert resultado["ejercicios"] == [
        {"ejercicio": 2026}
    ]