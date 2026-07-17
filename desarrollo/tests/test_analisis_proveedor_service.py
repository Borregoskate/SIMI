"""Pruebas unitarias para AnalisisProveedorService."""

from copy import deepcopy
from decimal import Decimal

import pytest

from services.analisis_proveedor_service import AnalisisProveedorService


class FakeAnalisisProveedorRepository:
    def __init__(self):
        self.llamadas = []
        self.proveedores = [
            {"id_proveedor": 1, "rfc": "AAA010101AAA", "razon_social": "PROVEEDOR UNO, S.A. DE C.V."}
        ]
        self.procedimientos = [
            {"id_procedimiento": 100, "numero_procedimiento": "PROC-2026-001", "ejercicio": 2026}
        ]
        self.ejercicios = [{"ejercicio": 2026}, {"ejercicio": 2024}]
        self.claves = [
            {"id_clave": 10, "clave": "010.000.001", "descripcion": "CLAVE A"},
            {"id_clave": 20, "clave": "010.000.002", "descripcion": "CLAVE B"},
        ]
        self.informacion = deepcopy(self.proveedores[0])
        self.indicadores = {
            "total_procedimientos_participados": "2",
            "total_claves_ofertadas": "2",
            "total_participaciones_procedimiento_clave": "3",
            "total_propuestas_iniciales": "3",
            "total_propuestas_subasta": "2",
            "total_evaluaciones_positivas": "2",
            "total_evaluaciones_negativas": "1",
            "total_claves_adjudicadas_operativas": "1",
            "total_procedimientos_adjudicados": "1",
            "total_adjudicaciones_operativas": "1",
            "total_adjudicaciones_historicas": "1",
            "total_claves_adjudicadas_historicas": "1",
            "cantidad_adjudicada_operativa": "60",
            "cantidad_adjudicada_historica": "40",
            "valor_adjudicado_operativo": "4800",
            "valor_adjudicado_historico": "3600",
        }
        self.participaciones = [
            {
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-2026-001",
                "ejercicio": 2026,
                "id_clave": 10,
                "clave": "010.000.001",
                "descripcion_clave": "CLAVE A",
                "cantidad_requerida": None,
                "id_propuesta_inicial": 1,
                "cantidad_inicial": "100",
                "precio_inicial": "100",
                "id_evaluacion": 10,
                "resultado_tecnico": "POSITIVA",
                "id_propuesta_subasta": 20,
                "cantidad_subasta": "90",
                "precio_subasta": "80",
                "id_adjudicacion": 30,
                "cantidad_adjudicada": "60",
                "porcentaje_adjudicado": "60",
                "precio_adjudicado": "80",
                "valor_adjudicado": "4800",
            },
            {
                "id_procedimiento": 101,
                "numero_procedimiento": "PROC-2025-002",
                "ejercicio": 2025,
                "id_clave": 20,
                "clave": "010.000.002",
                "descripcion_clave": "CLAVE B",
                "id_propuesta_inicial": 2,
                "cantidad_inicial": "10",
                "precio_inicial": "1000",
                "id_evaluacion": 11,
                "resultado_tecnico": "NEGATIVA",
                "id_propuesta_subasta": None,
                "cantidad_subasta": None,
                "precio_subasta": None,
                "id_adjudicacion": None,
                "cantidad_adjudicada": None,
                "porcentaje_adjudicado": None,
                "precio_adjudicado": None,
                "valor_adjudicado": None,
            },
            {
                "id_procedimiento": 102,
                "numero_procedimiento": "PROC-2024-003",
                "ejercicio": 2024,
                "id_clave": 10,
                "clave": "010.000.001",
                "descripcion_clave": "CLAVE A",
                "id_propuesta_inicial": 3,
                "cantidad_inicial": "20",
                "precio_inicial": "70",
                "id_evaluacion": 12,
                "resultado_tecnico": "POSITIVA",
                "id_propuesta_subasta": 21,
                "cantidad_subasta": "20",
                "precio_subasta": "77",
                "id_adjudicacion": None,
                "cantidad_adjudicada": None,
                "porcentaje_adjudicado": None,
                "precio_adjudicado": None,
                "valor_adjudicado": None,
            },
        ]
        self.historial = [
            {
                "origen_dato": "OPERATIVO",
                "id_procedimiento": 100,
                "numero_procedimiento": "PROC-2026-001",
                "ejercicio": 2026,
                "id_clave": 10,
                "clave": "010.000.001",
                "descripcion_clave": "CLAVE A",
                "cantidad_adjudicada": "60",
                "porcentaje_adjudicado": "60",
                "precio_adjudicado": "80",
                "valor_adjudicado": "4800",
            },
            {
                "origen_dato": "HISTORICO",
                "id_procedimiento": None,
                "numero_procedimiento": "HIST-2023-001",
                "ejercicio": 2023,
                "id_clave": 10,
                "clave": "010.000.001",
                "descripcion_clave": "CLAVE A",
                "cantidad_adjudicada": "40",
                "porcentaje_adjudicado": "100",
                "precio_adjudicado": "90",
                "valor_adjudicado": "3600",
            },
        ]
        self.competidores = [
            {
                "id_competidor": 2,
                "rfc_competidor": "BBB010101BBB",
                "razon_social_competidor": "COMPETIDOR DOS",
                "coincidencias": "4",
                "procedimientos_compartidos": "3",
                "claves_compartidas": "2",
                "victorias_proveedor": "2",
                "victorias_competidor": "1",
                "adjudicaciones_compartidas": "1",
                "sin_adjudicacion": "0",
            }
        ]

    def _guardar(self, nombre, *args, **kwargs):
        self.llamadas.append((nombre, args, kwargs))

    def obtener_proveedores_filtro(self, conn=None):
        self._guardar("obtener_proveedores_filtro", conn=conn)
        return deepcopy(self.proveedores)

    def obtener_procedimientos_filtro(self, id_proveedor, conn=None):
        self._guardar("obtener_procedimientos_filtro", id_proveedor, conn=conn)
        return deepcopy(self.procedimientos)

    def obtener_ejercicios_filtro(self, id_proveedor, conn=None):
        self._guardar("obtener_ejercicios_filtro", id_proveedor, conn=conn)
        return deepcopy(self.ejercicios)

    def obtener_claves_filtro(self, id_proveedor, conn=None):
        self._guardar("obtener_claves_filtro", id_proveedor, conn=conn)
        return deepcopy(self.claves)

    def obtener_informacion_proveedor(self, id_proveedor, conn=None):
        self._guardar("obtener_informacion_proveedor", id_proveedor, conn=conn)
        return deepcopy(self.informacion)

    def obtener_indicadores_proveedor(self, **kwargs):
        self._guardar("obtener_indicadores_proveedor", **kwargs)
        return deepcopy(self.indicadores)

    def obtener_participacion_operativa(self, **kwargs):
        self._guardar("obtener_participacion_operativa", **kwargs)
        return deepcopy(self.participaciones)

    def obtener_historial_adjudicaciones(self, **kwargs):
        self._guardar("obtener_historial_adjudicaciones", **kwargs)
        return deepcopy(self.historial)

    def obtener_competidores(self, **kwargs):
        self._guardar("obtener_competidores", **kwargs)
        return deepcopy(self.competidores)


@pytest.fixture
def repository():
    return FakeAnalisisProveedorRepository()


@pytest.fixture
def service(repository):
    return AnalisisProveedorService(repository=repository)


def test_service_acepta_repository_inyectado(repository):
    assert AnalisisProveedorService(repository=repository).repository is repository


def test_seleccionar_cantidad_referencia_respeta_prioridad():
    assert AnalisisProveedorService._seleccionar_cantidad_referencia({
        "cantidad_adjudicada": "5", "cantidad_subasta": "8", "cantidad_inicial": "10"
    }) == ("ADJUDICADA", Decimal("5"))
    assert AnalisisProveedorService._seleccionar_cantidad_referencia({
        "cantidad_adjudicada": None, "cantidad_subasta": "8", "cantidad_inicial": "10"
    }) == ("SUBASTA", Decimal("8"))
    assert AnalisisProveedorService._seleccionar_cantidad_referencia({
        "cantidad_adjudicada": None, "cantidad_subasta": None, "cantidad_inicial": "10"
    }) == ("INICIAL", Decimal("10"))


def test_procesar_participacion_calcula_variaciones_y_ahorro(repository):
    originales = deepcopy(repository.participaciones)
    resultado = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    primero, segundo, tercero = resultado
    assert primero["precio_inicial"] == Decimal("100.00")
    assert primero["variacion_inicial_subasta"] == Decimal("-20.00")
    assert primero["clasificacion_inicial_subasta"] == AnalisisProveedorService.CLASIFICACION_AHORRO
    assert primero["ahorro_unitario_subasta"] == Decimal("20.00")
    assert primero["ahorro_estimado_subasta"] == Decimal("1200.00")
    assert primero["estado_participacion"] == AnalisisProveedorService.ESTADO_ADJUDICADO
    assert segundo["descartado_tecnicamente"] is True
    assert segundo["estado_participacion"] == AnalisisProveedorService.ESTADO_DESCARTADO
    assert tercero["clasificacion_inicial_subasta"] == AnalisisProveedorService.CLASIFICACION_INCREMENTO
    assert repository.participaciones == originales


def test_resumen_economico_no_promedia_claves(repository):
    participaciones = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    resultado = AnalisisProveedorService.construir_resumen_economico(participaciones)
    assert "precio_promedio" not in resultado
    assert resultado["combinaciones_comparables"] == 2
    assert resultado["claves_con_reduccion"] == 1
    assert resultado["claves_con_incremento"] == 1
    assert resultado["ahorro_estimado_total"] == Decimal("1200.00")
    assert resultado["incremento_estimado_total"] == Decimal("140.00")


def test_completar_indicadores(repository):
    participaciones = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    resultado = AnalisisProveedorService.completar_indicadores(repository.indicadores, participaciones)
    assert resultado["total_evaluaciones"] == 3
    assert resultado["porcentaje_aprobacion_tecnica"] == Decimal("66.67")
    assert resultado["porcentaje_procedimientos_adjudicados"] == Decimal("50.00")
    assert resultado["total_adjudicaciones"] == 2
    assert resultado["valor_adjudicado_total"] == Decimal("8400.00")
    assert resultado["claves_descartadas_tecnicamente"] == 1


def test_desempeno_tecnico(repository):
    participaciones = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    resultado = AnalisisProveedorService.construir_desempeno_tecnico(participaciones)
    assert resultado["evaluaciones_positivas"] == 2
    assert resultado["evaluaciones_negativas"] == 1
    assert resultado["porcentaje_aprobacion"] == Decimal("66.67")
    assert resultado["claves_descartadas"] == 1
    assert len(resultado["detalle_descartadas"]) == 1


def test_historial_normaliza_origen_y_valores(repository):
    resultado = AnalisisProveedorService.procesar_historial_adjudicaciones(repository.historial)
    assert resultado[0]["es_historico"] is False
    assert resultado[1]["es_historico"] is True
    assert resultado[1]["precio_adjudicado"] == Decimal("90.00")
    assert resultado[1]["valor_adjudicado"] == Decimal("3600.00")
    assert resultado[1]["orden_fuente"] == 1


def test_evolucion_se_agrupa_por_clave_sin_mezclar_productos(repository):
    participaciones = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    historial = AnalisisProveedorService.procesar_historial_adjudicaciones(repository.historial)
    resultado = AnalisisProveedorService.construir_evolucion_por_clave(participaciones, historial)
    assert len(resultado) == 2
    clave_a = next(item for item in resultado if item["id_clave"] == 10)
    clave_b = next(item for item in resultado if item["id_clave"] == 20)
    assert clave_a["total_operativos"] == 2
    assert clave_a["total_historicos"] == 1
    assert clave_b["total_puntos"] == 1
    assert all(punto["precio_inicial"] != Decimal("1000.00") for punto in clave_a["puntos"])


def test_participacion_por_ejercicio_integra_historicos(repository):
    participaciones = AnalisisProveedorService.procesar_participacion_operativa(repository.participaciones)
    historial = AnalisisProveedorService.procesar_historial_adjudicaciones(repository.historial)
    resultado = AnalisisProveedorService.construir_participacion_por_ejercicio(participaciones, historial)
    por_ejercicio = {item["ejercicio"]: item for item in resultado}
    assert por_ejercicio[2026]["procedimientos_participados"] == 1
    assert por_ejercicio[2026]["valor_adjudicado_operativo"] == Decimal("4800.00")
    assert por_ejercicio[2023]["adjudicaciones_historicas"] == 1
    assert por_ejercicio[2023]["valor_adjudicado_historico"] == Decimal("3600.00")


def test_procesar_competidores(repository):
    resultado = AnalisisProveedorService.procesar_competidores(repository.competidores)
    item = resultado[0]
    assert item["derrotas_proveedor"] == 1
    assert item["porcentaje_victorias"] == Decimal("50.00")
    assert item["porcentaje_derrotas"] == Decimal("25.00")


def test_catalogos_sin_proveedor_solo_consulta_proveedores(service, repository):
    resultado = service.obtener_catalogos_filtros()
    assert resultado["proveedores"] == repository.proveedores
    assert resultado["procedimientos"] == []
    assert resultado["ejercicios"] == []
    assert resultado["claves"] == []
    assert [item[0] for item in repository.llamadas] == ["obtener_proveedores_filtro"]


def test_catalogos_con_proveedor_consulta_dependencias(service, repository):
    resultado = service.obtener_catalogos_filtros(id_proveedor=1, conn="CONN")
    assert resultado["procedimientos"] == repository.procedimientos
    assert resultado["ejercicios"] == repository.ejercicios
    assert resultado["claves"] == repository.claves
    nombres = [item[0] for item in repository.llamadas]
    assert nombres == [
        "obtener_proveedores_filtro",
        "obtener_procedimientos_filtro",
        "obtener_ejercicios_filtro",
        "obtener_claves_filtro",
    ]


def test_obtener_analisis_requiere_proveedor(service):
    with pytest.raises(ValueError, match="id_proveedor es obligatorio"):
        service.obtener_analisis_proveedor(None)


def test_obtener_analisis_rechaza_proveedor_inexistente(service, repository):
    repository.informacion = {}
    with pytest.raises(ValueError, match="no existe"):
        service.obtener_analisis_proveedor(999)


def test_obtener_analisis_construye_respuesta_completa(service, repository):
    resultado = service.obtener_analisis_proveedor(
        id_proveedor=1,
        id_procedimiento=100,
        ejercicio=2026,
        id_clave=10,
        conn="CONN",
    )
    assert set(resultado) == {
        "filtros", "proveedor", "indicadores", "resumen_economico",
        "desempeno_tecnico", "tablas", "graficas", "limitaciones"
    }
    assert resultado["filtros"]["id_proveedor"] == 1
    assert resultado["proveedor"]["rfc"] == "AAA010101AAA"
    assert len(resultado["tablas"]["participacion_operativa"]) == 3
    assert len(resultado["tablas"]["evolucion_por_clave"]) == 2
    assert resultado["limitaciones"]["precios_promedio_globales"] is False
    assert resultado["limitaciones"]["competencia_incluye_historicos"] is False


def test_obtener_analisis_no_modifica_datos_repository(service, repository):
    originales = (
        deepcopy(repository.indicadores),
        deepcopy(repository.participaciones),
        deepcopy(repository.historial),
        deepcopy(repository.competidores),
    )
    service.obtener_analisis_proveedor(1)
    assert repository.indicadores == originales[0]
    assert repository.participaciones == originales[1]
    assert repository.historial == originales[2]
    assert repository.competidores == originales[3]
