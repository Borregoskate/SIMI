"""Pruebas unitarias para AnalisisProveedorRepository."""

import pytest

from repositories.analisis_proveedor_repository import AnalisisProveedorRepository


@pytest.fixture
def repository():
    return AnalisisProveedorRepository()


@pytest.fixture
def capturador(monkeypatch, repository):
    llamadas = []

    def custom_query(**kwargs):
        llamadas.append(kwargs)
        if kwargs.get("fetchone"):
            return {"id_proveedor": 1}
        return [{"resultado": True}]

    monkeypatch.setattr(repository, "custom_query", custom_query)
    return llamadas


def test_configuracion_repository(repository):
    assert repository.table_name == "proveedores"
    assert repository.primary_key == "id_proveedor"
    assert repository.TIPO_INICIAL == "INICIAL"
    assert repository.TIPO_SUBASTA == "SUBASTA"


def test_construir_filtros_operativos_completos():
    where, params = AnalisisProveedorRepository._construir_filtros_operativos(
        id_proveedor=7,
        id_procedimiento=20,
        ejercicio=2026,
        id_clave=30,
    )
    assert "pa.id_proveedor = %s" in where
    assert "pr.id_procedimiento = %s" in where
    assert "pr.ejercicio = %s" in where
    assert "c.id_clave = %s" in where
    assert params == (7, 20, 2026, 30)


def test_construir_filtros_operativos_minimos():
    where, params = AnalisisProveedorRepository._construir_filtros_operativos(7)
    assert where == "WHERE pa.id_proveedor = %s"
    assert params == (7,)


def test_filtros_historicos_excluyen_procedimiento_operativo():
    where, params = AnalisisProveedorRepository._construir_filtros_historicos(
        id_proveedor=7,
        id_procedimiento=20,
        ejercicio=2025,
        id_clave=30,
    )
    assert "FALSE" in where
    assert "numero_procedimiento" in where
    assert "ah.id_clave = %s" in where
    assert params == (7, 2025, 30)


def test_obtener_proveedores_filtro(repository, capturador):
    resultado = repository.obtener_proveedores_filtro(conn="CONN")
    llamada = capturador[-1]
    assert resultado == [{"resultado": True}]
    assert "simi.proveedores" in llamada["query"]
    assert "simi.adjudicaciones_historicas" in llamada["query"]
    assert llamada["conn"] == "CONN"
    assert llamada["fetchall"] is True


def test_obtener_informacion_proveedor(repository, capturador):
    resultado = repository.obtener_informacion_proveedor(15, conn="CONN")
    llamada = capturador[-1]
    assert resultado == {"id_proveedor": 1}
    assert "pv.id_proveedor = %s" in llamada["query"]
    assert llamada["params"] == (15,)
    assert llamada["fetchone"] is True


def test_obtener_procedimientos_filtro_repite_proveedor(repository, capturador):
    repository.obtener_procedimientos_filtro(9, conn="CONN")
    llamada = capturador[-1]
    assert "WITH participaciones" in llamada["query"]
    assert "simi.propuestas" in llamada["query"]
    assert "simi.evaluaciones_tecnicas" in llamada["query"]
    assert "simi.adjudicaciones" in llamada["query"]
    assert llamada["params"] == (9, 9, 9)


def test_obtener_ejercicios_incluye_historicos(repository, capturador):
    repository.obtener_ejercicios_filtro(9)
    llamada = capturador[-1]
    assert "simi.adjudicaciones_historicas" in llamada["query"]
    assert "SUBSTRING" in llamada["query"]
    assert all(valor == 9 for valor in llamada["params"])


def test_obtener_claves_incluye_fuentes_operativas_e_historicas(repository, capturador):
    repository.obtener_claves_filtro(9)
    llamada = capturador[-1]
    assert "simi.claves" in llamada["query"]
    assert "simi.adjudicaciones_historicas" in llamada["query"]
    assert all(valor == 9 for valor in llamada["params"])


def test_indicadores_usa_filtros_y_union_historico(repository, capturador):
    repository.obtener_indicadores_proveedor(
        id_proveedor=3,
        id_procedimiento=10,
        ejercicio=2026,
        id_clave=8,
        conn="CONN",
    )
    llamada = capturador[-1]
    query = llamada["query"]
    assert "WITH participaciones" in query
    assert "adjudicaciones_historicas" in query
    assert "simi.adjudicaciones_historicas" in query
    assert "FALSE" in query
    assert llamada["conn"] == "CONN"
    assert llamada["fetchone"] is True


def test_participacion_operativa_une_todas_las_etapas(repository, capturador):
    repository.obtener_participacion_operativa(3, ejercicio=2026)
    llamada = capturador[-1]
    query = llamada["query"]
    assert "propuesta_inicial" in query
    assert "evaluacion" in query
    assert "propuesta_subasta" in query
    assert "adjudicacion" in query
    assert "simi.procedimiento_claves" in query
    assert llamada["fetchall"] is True


def test_historial_adjudicaciones_conserva_dos_origenes(repository, capturador):
    repository.obtener_historial_adjudicaciones(3, ejercicio=2026)
    llamada = capturador[-1]
    query = llamada["query"]
    assert "'OPERATIVO'" in query
    assert "'HISTORICO'" in query
    assert "UNION ALL" in query
    assert "simi.adjudicaciones_historicas" in query


def test_competidores_solo_usa_informacion_operativa(repository, capturador):
    repository.obtener_competidores(3, id_clave=8)
    llamada = capturador[-1]
    query = llamada["query"]
    assert "WITH participantes" in query
    assert "victorias_proveedor" in query
    assert "victorias_competidor" in query
    assert "adjudicaciones_historicas" not in query
