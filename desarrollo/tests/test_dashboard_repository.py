"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_dashboard_repository.py

Pruebas unitarias para DashboardRepository.

Estas pruebas:
- No requieren conexión real a PostgreSQL.
- Verifican delegación a BaseRepository.
- Verifican consultas parametrizadas.
- Verifican transmisión de conexión externa.
- Verifican filtros opcionales.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.dashboard_repository import DashboardRepository


CONEXION_PRUEBA = object()


def test_dashboard_repository_configuracion():
    repo = DashboardRepository()

    assert repo.table_name == "procedimientos"
    assert repo.primary_key == "id_procedimiento"
    assert repo.TIPO_INICIAL == "INICIAL"
    assert repo.TIPO_SUBASTA == "SUBASTA"
    assert repo.RESULTADO_POSITIVA == "POSITIVA"
    assert repo.RESULTADO_NEGATIVA == "NEGATIVA"


def test_construir_filtros_sin_parametros():
    where_sql, params = DashboardRepository._construir_filtros()

    assert where_sql == ""
    assert params == ()


def test_construir_filtros_completos():
    where_sql, params = DashboardRepository._construir_filtros(
        id_procedimiento=10,
        ejercicio=2026,
        alias_procedimiento="pr",
    )

    assert "pr.id_procedimiento = %s" in where_sql
    assert "pr.ejercicio = %s" in where_sql
    assert params == (10, 2026)


def test_obtener_procedimientos_filtro(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_procedimiento": 1,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "FROM simi.procedimientos" in query
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_procedimientos_filtro(
        conn=CONEXION_PRUEBA
    )

    assert resultado == esperado


def test_obtener_indicadores_principales(monkeypatch):
    repo = DashboardRepository()
    esperado = {
        "total_procedimientos": 1,
        "total_claves": 10,
        "total_proveedores_participantes": 4,
        "total_propuestas_iniciales": 25,
        "total_claves_adjudicadas": 8,
        "total_claves_desiertas": 2,
    }

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "WITH procedimientos_filtrados" in query
        assert "claves_desiertas" in query
        assert "p.tipo_propuesta = %s" in query
        assert params == (1, 2026, "INICIAL", "SUBASTA")
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        assert fetchall is False
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_indicadores_principales(
        id_procedimiento=1,
        ejercicio=2026,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_competencia_por_clave(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_clave": 3,
            "clave": "010.000.001",
            "total_proveedores": 4,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "COUNT(" in query
        assert "DISTINCT CASE" in query
        assert "p.tipo_propuesta = %s" in query
        assert params == ("INICIAL", 1)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_competencia_por_clave(
        id_procedimiento=1,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_resumen_competencia_procedimientos(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_procedimiento": 1,
            "promedio_proveedores_por_clave": 2.5,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "WITH competencia_clave" in query
        assert "AVG(total_proveedores)" in query
        assert params == ("INICIAL", 2026)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_resumen_competencia_procedimientos(
        ejercicio=2026,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_estado_claves(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "clave": "010.000.001",
            "proveedores_oferta_inicial": 0,
            "tiene_adjudicacion": False,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "evaluaciones_positivas" in query
        assert "tiene_subasta" in query
        assert "tiene_adjudicacion" in query
        assert params == (
            "INICIAL",
            "POSITIVA",
            "NEGATIVA",
            "SUBASTA",
            1,
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_estado_claves(
        id_procedimiento=1,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_participacion_proveedores(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_proveedor": 2,
            "razon_social": "PROVEEDOR A, S.A. DE C.V.",
            "presento_oferta_inicial": True,
            "participo_subasta": True,
            "claves_adjudicadas": 1,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "WITH procedimientos_filtrados" in query
        assert "participantes AS" in query
        assert "presento_oferta_inicial" in query
        assert "participo_subasta" in query
        assert params == (
            1,
            "POSITIVA",
            "NEGATIVA",
            "INICIAL",
            "SUBASTA",
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_participacion_proveedores(
        id_procedimiento=1,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_aprobacion_por_proveedor(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_proveedor": 2,
            "total_evaluaciones": 10,
            "evaluaciones_positivas": 8,
            "evaluaciones_negativas": 2,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "COUNT(et.id_evaluacion)" in query
        assert "evaluaciones_positivas" in query
        assert "evaluaciones_negativas" in query
        assert params == ("POSITIVA", "NEGATIVA", 2026)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_aprobacion_por_proveedor(
        ejercicio=2026,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_precios_por_clave(monkeypatch):
    repo = DashboardRepository()
    esperado = [
        {
            "id_clave": 3,
            "mejor_precio_inicial": 25,
            "mejor_precio_viable": 24,
            "mejor_precio_subasta": 22,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "mejor_precio_inicial" in query
        assert "mejor_precio_viable" in query
        assert "mejor_precio_subasta" in query
        assert "et.id_proveedor = p.id_proveedor" in query
        assert params == (
            "INICIAL",
            "INICIAL",
            "POSITIVA",
            "SUBASTA",
            "POSITIVA",
            1,
            3,
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_precios_por_clave(
        id_procedimiento=1,
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado