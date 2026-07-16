"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_analisis_clave_service.py

Pruebas unitarias para AnalisisClaveService.

Estas pruebas:
- No se conectan a la base de datos.
- No ejecutan SQL.
- Utilizan un Repository falso controlado.
- Validan cálculos, estados, clasificaciones y estructuras
  preparadas para Streamlit.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from copy import deepcopy
from decimal import Decimal

import pytest

from services.analisis_clave_service import AnalisisClaveService


class FakeAnalisisClaveRepository:
    """Repository falso para aislar las pruebas del Service."""

    RESULTADO_POSITIVA = "POSITIVA"

    def __init__(self):
        self.llamadas = []

        self.claves = [
            {
                "id_clave": 10,
                "clave": "010.000.001",
                "descripcion": "PRODUCTO DE PRUEBA",
                "categoria": "MEDICAMENTOS",
            }
        ]

        self.procedimientos_filtro = [
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-001",
                "ejercicio": 2026,
            },
            {
                "id_procedimiento": 101,
                "numero_procedimiento": "PROC-002",
                "ejercicio": 2025,
            },
        ]

        self.ejercicios = [
            {"ejercicio": 2026},
            {"ejercicio": 2025},
        ]

        self.informacion_clave = {
            "id_clave": 10,
            "clave": "010.000.001",
            "descripcion": "PRODUCTO DE PRUEBA",
            "id_categoria": 1,
            "categoria": "MEDICAMENTOS",
        }

        self.indicadores = {
            "total_procedimientos": 2,
            "total_proveedores_participantes": 4,
            "total_propuestas_iniciales": 5,
            "total_evaluaciones_positivas": 3,
            "total_evaluaciones_negativas": 2,
            "total_propuestas_subasta": 2,
            "total_proveedores_adjudicados": 2,
            "total_procedimientos_adjudicados": 1,
            "cantidad_total_adjudicada": "150",
        }

        self.resumen = [
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-001",
                "ejercicio": 2026,
                "cantidad_requerida": "100",
                "total_propuestas_iniciales": 3,
                "evaluaciones_positivas": 2,
                "evaluaciones_negativas": 1,
                "total_subastas": 1,
                "proveedores_adjudicados": 2,
                "cantidad_total_adjudicada": "100",
                "porcentaje_total_adjudicado": "100",
                "valor_total_adjudicado": "8000",
                "mejor_precio_inicial": "100",
                "mejor_precio_viable": "90",
                "mejor_precio_subasta": "80",
                "mejor_precio_adjudicado": "75",
            },
            {
                "id_procedimiento": 101,
                "numero_procedimiento": "PROC-002",
                "ejercicio": 2025,
                "cantidad_requerida": None,
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 1,
                "evaluaciones_negativas": 1,
                "total_subastas": 0,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": None,
                "porcentaje_total_adjudicado": None,
                "valor_total_adjudicado": None,
                "mejor_precio_inicial": "120",
                "mejor_precio_viable": "110",
                "mejor_precio_subasta": None,
                "mejor_precio_adjudicado": None,
            },
        ]

        self.detalle = [
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-001",
                "id_proveedor": 1,
                "rfc": "AAA010101AAA",
                "razon_social": "PROVEEDOR UNO, S.A. DE C.V.",
                "id_propuesta_inicial": 1,
                "cantidad_inicial": "100",
                "precio_inicial": "100",
                "id_evaluacion": 10,
                "resultado_tecnico": "POSITIVA",
                "id_propuesta_subasta": 20,
                "cantidad_subasta": "100",
                "precio_subasta": "80",
                "id_adjudicacion": 30,
                "cantidad_adjudicada": "60",
                "porcentaje_adjudicado": "60",
                "precio_adjudicado": "75",
            },
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-001",
                "id_proveedor": 2,
                "rfc": "BBB010101BBB",
                "razon_social": "PROVEEDOR DOS, S.A. DE C.V.",
                "id_propuesta_inicial": 2,
                "cantidad_inicial": "100",
                "precio_inicial": "105",
                "id_evaluacion": 11,
                "resultado_tecnico": "NEGATIVA",
                "id_propuesta_subasta": None,
                "cantidad_subasta": None,
                "precio_subasta": None,
                "id_adjudicacion": None,
                "cantidad_adjudicada": None,
                "porcentaje_adjudicado": None,
                "precio_adjudicado": None,
            },
        ]

        self.historial = [
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-001",
                "ejercicio": 2026,
                "mejor_precio_inicial": "100",
                "mejor_precio_viable": "90",
                "mejor_precio_subasta": "80",
                "mejor_precio_adjudicado": "75",
                "cantidad_total_adjudicada": "100",
                "valor_total_adjudicado": "8000",
            }
        ]

    def obtener_claves_filtro(self, conn=None):
        self.llamadas.append(("obtener_claves_filtro", conn))
        return deepcopy(self.claves)

    def obtener_procedimientos_filtro(
        self,
        id_clave,
        conn=None,
    ):
        self.llamadas.append(
            ("obtener_procedimientos_filtro", id_clave, conn)
        )
        return deepcopy(self.procedimientos_filtro)

    def obtener_ejercicios_filtro(
        self,
        id_clave,
        conn=None,
    ):
        self.llamadas.append(
            ("obtener_ejercicios_filtro", id_clave, conn)
        )
        return deepcopy(self.ejercicios)

    def obtener_informacion_clave(
        self,
        id_clave,
        conn=None,
    ):
        self.llamadas.append(
            ("obtener_informacion_clave", id_clave, conn)
        )
        return deepcopy(self.informacion_clave)

    def obtener_indicadores_clave(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_indicadores_clave",
                id_clave,
                id_procedimiento,
                ejercicio,
                conn,
            )
        )
        return deepcopy(self.indicadores)

    def obtener_resumen_procedimientos(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_resumen_procedimientos",
                id_clave,
                id_procedimiento,
                ejercicio,
                conn,
            )
        )
        return deepcopy(self.resumen)

    def obtener_detalle_proveedores(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_detalle_proveedores",
                id_clave,
                id_procedimiento,
                ejercicio,
                conn,
            )
        )
        return deepcopy(self.detalle)

    def obtener_historial_precios(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_historial_precios",
                id_clave,
                id_procedimiento,
                ejercicio,
                conn,
            )
        )
        return deepcopy(self.historial)


@pytest.fixture
def repository():
    return FakeAnalisisClaveRepository()


@pytest.fixture
def service(repository):
    return AnalisisClaveService(repository=repository)


# ==========================================================
# INICIALIZACIÓN
# ==========================================================


def test_service_acepta_repository_inyectado(repository):
    service = AnalisisClaveService(repository=repository)

    assert service.repository is repository


# ==========================================================
# CONVERSIÓN Y REDONDEO
# ==========================================================


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (10, Decimal("10")),
        (10.5, Decimal("10.5")),
        ("10.50", Decimal("10.50")),
        (Decimal("12.30"), Decimal("12.30")),
        (" 15.25 ", Decimal("15.25")),
        (None, None),
        ("", None),
        ("NO NUMERICO", None),
    ],
)
def test_decimal_convierte_valores_controladamente(valor, esperado):
    assert AnalisisClaveService._decimal(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("10", 10),
        (Decimal("10.99"), 10),
        (None, 0),
        ("INVALIDO", 0),
    ],
)
def test_entero_convierte_sin_propagar_errores(valor, esperado):
    assert AnalisisClaveService._entero(valor) == esperado


def test_redondear_precio_utiliza_round_half_up():
    resultado = AnalisisClaveService.redondear_precio("10.125")

    assert resultado == Decimal("10.13")


def test_redondear_porcentaje_utiliza_dos_decimales():
    resultado = AnalisisClaveService.redondear_porcentaje("33.335")

    assert resultado == Decimal("33.34")


def test_redondeo_devuelve_none_para_valor_invalido():
    assert AnalisisClaveService.redondear_precio(None) is None
    assert AnalisisClaveService.redondear_porcentaje("ERROR") is None


# ==========================================================
# PORCENTAJES Y VARIACIONES
# ==========================================================


def test_calcular_porcentaje():
    resultado = AnalisisClaveService.calcular_porcentaje(3, 4)

    assert resultado == Decimal("75.00")


@pytest.mark.parametrize("denominador", [None, 0, -1, "INVALIDO"])
def test_calcular_porcentaje_sin_denominador_valido_devuelve_none(
    denominador,
):
    resultado = AnalisisClaveService.calcular_porcentaje(
        10,
        denominador,
    )

    assert resultado is None


def test_calcular_variacion_ahorro():
    resultado = AnalisisClaveService.calcular_variacion(
        Decimal("100"),
        Decimal("80"),
    )

    assert resultado == Decimal("-20.00")


def test_calcular_variacion_incremento():
    resultado = AnalisisClaveService.calcular_variacion(100, 125)

    assert resultado == Decimal("25.00")


def test_calcular_variacion_sin_cambio():
    resultado = AnalisisClaveService.calcular_variacion("100", "100")

    assert resultado == Decimal("0.00")


@pytest.mark.parametrize(
    ("origen", "destino"),
    [
        (None, 100),
        (100, None),
        (0, 100),
        (-10, 100),
        ("INVALIDO", 100),
    ],
)
def test_calcular_variacion_con_informacion_insuficiente(
    origen,
    destino,
):
    resultado = AnalisisClaveService.calcular_variacion(
        origen,
        destino,
    )

    assert resultado is None


@pytest.mark.parametrize(
    ("variacion", "clasificacion"),
    [
        (
            Decimal("-0.01"),
            AnalisisClaveService.CLASIFICACION_AHORRO,
        ),
        (
            Decimal("0.00"),
            AnalisisClaveService.CLASIFICACION_SIN_CAMBIO,
        ),
        (
            Decimal("0.01"),
            AnalisisClaveService.CLASIFICACION_INCREMENTO,
        ),
        (
            None,
            AnalisisClaveService.CLASIFICACION_INSUFICIENTE,
        ),
    ],
)
def test_clasificar_variacion(variacion, clasificacion):
    assert (
        AnalisisClaveService.clasificar_variacion(variacion)
        == clasificacion
    )


# ==========================================================
# PRECIO ADJUDICADO PONDERADO
# ==========================================================


def test_calcular_precio_adjudicado_ponderado():
    resultado = (
        AnalisisClaveService.calcular_precio_adjudicado_ponderado(
            cantidad_total_adjudicada=150,
            valor_total_adjudicado=12000,
        )
    )

    assert resultado == Decimal("80.00")


@pytest.mark.parametrize(
    ("cantidad", "valor"),
    [
        (None, 1000),
        (0, 1000),
        (-1, 1000),
        (100, None),
    ],
)
def test_precio_adjudicado_ponderado_invalido_devuelve_none(
    cantidad,
    valor,
):
    resultado = (
        AnalisisClaveService.calcular_precio_adjudicado_ponderado(
            cantidad,
            valor,
        )
    )

    assert resultado is None


# ==========================================================
# ESTADOS ANALÍTICOS
# ==========================================================


@pytest.mark.parametrize(
    ("registro", "esperado"),
    [
        (
            {
                "total_propuestas_iniciales": 0,
                "evaluaciones_positivas": 0,
                "evaluaciones_negativas": 0,
                "total_subastas": 0,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": 0,
            },
            AnalisisClaveService.ESTADO_SIN_PROPUESTAS,
        ),
        (
            {
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 0,
                "evaluaciones_negativas": 0,
                "total_subastas": 0,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": 0,
            },
            AnalisisClaveService.ESTADO_SOLO_OFERTA_INICIAL,
        ),
        (
            {
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 0,
                "evaluaciones_negativas": 2,
                "total_subastas": 0,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": 0,
            },
            AnalisisClaveService.ESTADO_SIN_APROBACION,
        ),
        (
            {
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 1,
                "evaluaciones_negativas": 1,
                "total_subastas": 0,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": 0,
            },
            AnalisisClaveService.ESTADO_CON_OFERTA_VIABLE,
        ),
        (
            {
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 1,
                "evaluaciones_negativas": 1,
                "total_subastas": 1,
                "proveedores_adjudicados": 0,
                "cantidad_total_adjudicada": 0,
            },
            AnalisisClaveService.ESTADO_CON_SUBASTA,
        ),
        (
            {
                "total_propuestas_iniciales": 2,
                "evaluaciones_positivas": 1,
                "evaluaciones_negativas": 1,
                "total_subastas": 1,
                "proveedores_adjudicados": 1,
                "cantidad_total_adjudicada": 100,
            },
            AnalisisClaveService.ESTADO_ADJUDICADO,
        ),
    ],
)
def test_clasificar_estado_procedimiento(registro, esperado):
    resultado = (
        AnalisisClaveService.clasificar_estado_procedimiento(
            registro
        )
    )

    assert resultado == esperado


def test_clasificar_estado_consolidado_usa_etapa_mas_avanzada():
    procedimientos = [
        {
            "estado_analitico": (
                AnalisisClaveService.ESTADO_CON_OFERTA_VIABLE
            )
        },
        {
            "estado_analitico": (
                AnalisisClaveService.ESTADO_ADJUDICADO
            )
        },
    ]

    resultado = AnalisisClaveService.clasificar_estado_consolidado(
        procedimientos
    )

    assert resultado == AnalisisClaveService.ESTADO_ADJUDICADO


def test_estado_consolidado_sin_registros():
    resultado = AnalisisClaveService.clasificar_estado_consolidado(
        []
    )

    assert resultado == AnalisisClaveService.ESTADO_SIN_INFORMACION


# ==========================================================
# PROCESAMIENTO POR PROCEDIMIENTO
# ==========================================================


def test_procesar_resumen_calcula_todos_los_resultados(repository):
    originales = deepcopy(repository.resumen)

    resultado = AnalisisClaveService.procesar_resumen_procedimientos(
        repository.resumen
    )

    primero = resultado[0]

    assert primero["mejor_precio_inicial"] == Decimal("100.00")
    assert primero["mejor_precio_viable"] == Decimal("90.00")
    assert primero["mejor_precio_subasta"] == Decimal("80.00")
    assert (
        primero["precio_adjudicado_ponderado"]
        == Decimal("80.00")
    )
    assert (
        primero["variacion_inicial_viable"]
        == Decimal("-10.00")
    )
    assert (
        primero["variacion_viable_subasta"]
        == Decimal("-11.11")
    )
    assert (
        primero["variacion_subasta_adjudicacion"]
        == Decimal("0.00")
    )
    assert (
        primero["variacion_viable_adjudicacion"]
        == Decimal("-11.11")
    )
    assert (
        primero["clasificacion_viable_adjudicacion"]
        == AnalisisClaveService.CLASIFICACION_AHORRO
    )
    assert (
        primero["estado_analitico"]
        == AnalisisClaveService.ESTADO_ADJUDICADO
    )

    assert repository.resumen == originales


def test_procesar_resumen_mantiene_none_en_etapas_ausentes(
    repository,
):
    resultado = AnalisisClaveService.procesar_resumen_procedimientos(
        repository.resumen
    )

    segundo = resultado[1]

    assert segundo["mejor_precio_subasta"] is None
    assert segundo["precio_adjudicado_ponderado"] is None
    assert segundo["variacion_viable_subasta"] is None
    assert (
        segundo["clasificacion_viable_subasta"]
        == AnalisisClaveService.CLASIFICACION_INSUFICIENTE
    )
    assert (
        segundo["estado_analitico"]
        == AnalisisClaveService.ESTADO_CON_OFERTA_VIABLE
    )


# ==========================================================
# CONSOLIDADO
# ==========================================================


def test_calcular_precios_consolidados(repository):
    procedimientos = (
        AnalisisClaveService.procesar_resumen_procedimientos(
            repository.resumen
        )
    )

    resultado = AnalisisClaveService.calcular_precios_consolidados(
        procedimientos
    )

    assert resultado["mejor_precio_inicial"] == Decimal("110.00")
    assert resultado["mejor_precio_viable"] == Decimal("100.00")
    assert resultado["mejor_precio_subasta"] == Decimal("80.00")
    assert (
        resultado["precio_adjudicado_ponderado"]
        == Decimal("80.00")
    )


def test_calcular_variaciones_consolidadas():
    precios = {
        "mejor_precio_inicial": Decimal("100"),
        "mejor_precio_viable": Decimal("90"),
        "mejor_precio_subasta": Decimal("80"),
        "precio_adjudicado_ponderado": Decimal("85"),
    }

    resultado = (
        AnalisisClaveService.calcular_variaciones_consolidadas(
            precios
        )
    )

    assert resultado["variacion_inicial_viable"] == Decimal("-10.00")
    assert resultado["variacion_viable_subasta"] == Decimal("-11.11")
    assert (
        resultado["variacion_subasta_adjudicacion"]
        == Decimal("6.25")
    )
    assert (
        resultado["variacion_viable_adjudicacion"]
        == Decimal("-5.56")
    )
    assert (
        resultado["clasificacion_subasta_adjudicacion"]
        == AnalisisClaveService.CLASIFICACION_INCREMENTO
    )


def test_contar_estados(repository):
    procedimientos = (
        AnalisisClaveService.procesar_resumen_procedimientos(
            repository.resumen
        )
    )

    resultado = AnalisisClaveService.contar_estados(
        procedimientos
    )

    assert resultado[AnalisisClaveService.ESTADO_ADJUDICADO] == 1
    assert (
        resultado[
            AnalisisClaveService.ESTADO_CON_OFERTA_VIABLE
        ]
        == 1
    )


def test_construir_consolidado(repository):
    procedimientos = (
        AnalisisClaveService.procesar_resumen_procedimientos(
            repository.resumen
        )
    )

    resultado = AnalisisClaveService.construir_consolidado(
        procedimientos
    )

    assert (
        resultado["estado_analitico"]
        == AnalisisClaveService.ESTADO_ADJUDICADO
    )
    assert "precios" in resultado
    assert "variaciones" in resultado
    assert "procedimientos_por_estado" in resultado


# ==========================================================
# INDICADORES
# ==========================================================


def test_completar_indicadores(repository):
    procedimientos = (
        AnalisisClaveService.procesar_resumen_procedimientos(
            repository.resumen
        )
    )

    resultado = AnalisisClaveService.completar_indicadores(
        repository.indicadores,
        procedimientos,
    )

    assert resultado["total_evaluaciones"] == 5
    assert (
        resultado["porcentaje_aprobacion_tecnica"]
        == Decimal("60.00")
    )
    assert (
        resultado["porcentaje_procedimientos_adjudicados"]
        == Decimal("50.00")
    )
    assert (
        resultado[
            "promedio_propuestas_iniciales_por_procedimiento"
        ]
        == Decimal("2.50")
    )
    assert (
        resultado["estado_analitico_consolidado"]
        == AnalisisClaveService.ESTADO_ADJUDICADO
    )


def test_completar_indicadores_sin_evaluaciones():
    indicadores = {
        "total_procedimientos": 0,
        "total_evaluaciones_positivas": 0,
        "total_evaluaciones_negativas": 0,
    }

    resultado = AnalisisClaveService.completar_indicadores(
        indicadores,
        [],
    )

    assert resultado["total_evaluaciones"] == 0
    assert resultado["porcentaje_aprobacion_tecnica"] is None
    assert (
        resultado["porcentaje_procedimientos_adjudicados"]
        is None
    )


# ==========================================================
# DETALLE DE PROVEEDORES
# ==========================================================


def test_procesar_detalle_proveedores(repository):
    originales = deepcopy(repository.detalle)

    resultado = AnalisisClaveService.procesar_detalle_proveedores(
        repository.detalle
    )

    primero = resultado[0]
    segundo = resultado[1]

    assert primero["precio_inicial"] == Decimal("100.00")
    assert primero["cantidad_adjudicada"] == Decimal("60")
    assert primero["tiene_oferta_inicial"] is True
    assert primero["evaluado"] is True
    assert primero["aprobado_tecnicamente"] is True
    assert primero["tiene_subasta"] is True
    assert primero["adjudicado"] is True

    assert segundo["aprobado_tecnicamente"] is False
    assert segundo["tiene_subasta"] is False
    assert segundo["adjudicado"] is False

    assert repository.detalle == originales


# ==========================================================
# HISTORIAL
# ==========================================================


def test_procesar_historial_precios(repository):
    resultado = AnalisisClaveService.procesar_historial_precios(
        repository.historial
    )

    registro = resultado[0]

    assert registro["mejor_precio_inicial"] == Decimal("100.00")
    assert (
        registro["precio_adjudicado_ponderado"]
        == Decimal("80.00")
    )
    assert (
        registro["variacion_viable_adjudicacion"]
        == Decimal("-11.11")
    )
    assert (
        registro["clasificacion_viable_adjudicacion"]
        == AnalisisClaveService.CLASIFICACION_AHORRO
    )


# ==========================================================
# FILTROS
# ==========================================================


def test_obtener_catalogos_sin_clave_solo_consulta_claves(
    service,
    repository,
):
    resultado = service.obtener_catalogos_filtros()

    assert resultado["claves"] == repository.claves
    assert resultado["procedimientos"] == []
    assert resultado["ejercicios"] == []
    assert repository.llamadas == [
        ("obtener_claves_filtro", None)
    ]


def test_obtener_catalogos_con_clave_consulta_todos_los_filtros(
    service,
    repository,
):
    conn = object()

    resultado = service.obtener_catalogos_filtros(
        id_clave=10,
        conn=conn,
    )

    assert resultado["claves"] == repository.claves
    assert (
        resultado["procedimientos"]
        == repository.procedimientos_filtro
    )
    assert resultado["ejercicios"] == repository.ejercicios
    assert (
        "obtener_procedimientos_filtro",
        10,
        conn,
    ) in repository.llamadas
    assert (
        "obtener_ejercicios_filtro",
        10,
        conn,
    ) in repository.llamadas


# ==========================================================
# RESPUESTA COMPLETA PARA STREAMLIT
# ==========================================================


def test_obtener_analisis_clave_requiere_id_clave(service):
    with pytest.raises(
        ValueError,
        match="id_clave es obligatorio",
    ):
        service.obtener_analisis_clave(id_clave=None)


def test_obtener_analisis_clave_construye_respuesta_completa(
    service,
    repository,
):
    conn = object()

    resultado = service.obtener_analisis_clave(
        id_clave=10,
        id_procedimiento=100,
        ejercicio=2026,
        conn=conn,
    )

    assert resultado["filtros"] == {
        "id_clave": 10,
        "id_procedimiento": 100,
        "ejercicio": 2026,
    }
    assert resultado["clave"] == repository.informacion_clave

    assert (
        resultado["indicadores"]["total_procedimientos"]
        == 2
    )
    assert (
        resultado["consolidado"]["estado_analitico"]
        == AnalisisClaveService.ESTADO_ADJUDICADO
    )

    assert len(
        resultado["tablas"]["resumen_procedimientos"]
    ) == 2
    assert len(
        resultado["tablas"]["detalle_proveedores"]
    ) == 2
    assert len(
        resultado["graficas"]["historial_precios"]
    ) == 1

    assert (
        "obtener_indicadores_clave",
        10,
        100,
        2026,
        conn,
    ) in repository.llamadas
    assert (
        "obtener_resumen_procedimientos",
        10,
        100,
        2026,
        conn,
    ) in repository.llamadas
    assert (
        "obtener_detalle_proveedores",
        10,
        100,
        2026,
        conn,
    ) in repository.llamadas
    assert (
        "obtener_historial_precios",
        10,
        100,
        2026,
        conn,
    ) in repository.llamadas


def test_obtener_analisis_no_modifica_respuestas_del_repository(
    service,
    repository,
):
    resumen_original = deepcopy(repository.resumen)
    detalle_original = deepcopy(repository.detalle)
    historial_original = deepcopy(repository.historial)
    indicadores_originales = deepcopy(repository.indicadores)

    service.obtener_analisis_clave(id_clave=10)

    assert repository.resumen == resumen_original
    assert repository.detalle == detalle_original
    assert repository.historial == historial_original
    assert repository.indicadores == indicadores_originales


def test_respuesta_incluye_estructuras_para_streamlit(service):
    resultado = service.obtener_analisis_clave(id_clave=10)

    assert set(resultado) == {
        "filtros",
        "clave",
        "indicadores",
        "consolidado",
        "graficas",
        "tablas",
    }
    assert set(resultado["graficas"]) == {
        "historial_precios",
        "variaciones_por_procedimiento",
        "procedimientos_por_estado",
    }
    assert set(resultado["tablas"]) == {
        "resumen_procedimientos",
        "detalle_proveedores",
        "historial_precios",
    }