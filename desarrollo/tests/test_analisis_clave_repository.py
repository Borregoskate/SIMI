"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_analisis_clave_repository.py

Pruebas unitarias corregidas para AnalisisClaveRepository.

Autor: Jorge Saavedra
Versión: 1.0.1
==============================================================
"""

import re

from repositories.analisis_clave_repository import AnalisisClaveRepository


CONEXION_PRUEBA = object()


def normalizar_sql(query):
    """Reduce espacios y saltos de línea para validar SQL sin depender del formato."""
    return re.sub(r"\s+", " ", query).strip()


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

def test_analisis_clave_repository_configuracion():
    repo = AnalisisClaveRepository()

    assert repo.table_name == "claves"
    assert repo.primary_key == "id_clave"
    assert repo.TIPO_INICIAL == "INICIAL"
    assert repo.TIPO_SUBASTA == "SUBASTA"
    assert repo.RESULTADO_POSITIVA == "POSITIVA"
    assert repo.RESULTADO_NEGATIVA == "NEGATIVA"


# ==========================================================
# FILTROS
# ==========================================================

def test_construir_filtros_con_clave_obligatoria():
    where_sql, params = AnalisisClaveRepository._construir_filtros(
        id_clave=3,
        alias_clave="pc",
        alias_procedimiento="pr",
    )

    assert where_sql.startswith("WHERE ")
    assert "pc.id_clave = %s" in where_sql
    assert "pr.id_procedimiento = %s" not in where_sql
    assert "pr.ejercicio = %s" not in where_sql
    assert params == (3,)


def test_construir_filtros_completos():
    where_sql, params = AnalisisClaveRepository._construir_filtros(
        id_clave=3,
        id_procedimiento=10,
        ejercicio=2026,
        alias_clave="pc",
        alias_procedimiento="pr",
    )

    assert "pc.id_clave = %s" in where_sql
    assert "pr.id_procedimiento = %s" in where_sql
    assert "pr.ejercicio = %s" in where_sql
    assert params == (3, 10, 2026)


# ==========================================================
# CATÁLOGOS PARA FILTROS
# ==========================================================

def test_obtener_claves_filtro(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion": "CLAVE DE PRUEBA",
            "categoria": "MEDICAMENTOS",
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.claves AS c" in sql
        assert "LEFT JOIN simi.cat_categorias_clave AS cc" in sql
        assert "cc.nombre_categoria AS categoria" in sql
        assert "ORDER BY c.clave, c.id_clave" in sql

        assert params is None
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_claves_filtro(
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_informacion_clave(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = {
        "id_clave": 3,
        "clave": "010.000.001",
        "descripcion": "CLAVE DE PRUEBA",
        "id_categoria": 2,
        "categoria": "MEDICAMENTOS",
    }

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.claves AS c" in sql
        assert "LEFT JOIN simi.cat_categorias_clave AS cc" in sql
        assert "cc.nombre_categoria AS categoria" in sql
        assert "WHERE c.id_clave = %s" in sql
        assert "LIMIT 1" in sql

        assert params == (3,)
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        assert fetchall is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_informacion_clave(
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_procedimientos_filtro(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "descripcion": "PROCEDIMIENTO DE PRUEBA",
            "ejercicio": 2026,
            "activo": True,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.procedimientos AS pr" in sql
        assert "INNER JOIN simi.procedimiento_claves AS pc" in sql
        assert "pc.id_clave = %s" in sql
        assert (
            "ORDER BY pr.ejercicio DESC, "
            "pr.numero_procedimiento, "
            "pr.id_procedimiento DESC"
        ) in sql

        assert params == (3,)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_procedimientos_filtro(
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_obtener_ejercicios_filtro(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {"ejercicio": 2026},
        {"ejercicio": 2025},
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "SELECT DISTINCT pr.ejercicio" in sql
        assert "FROM simi.procedimientos AS pr" in sql
        assert "INNER JOIN simi.procedimiento_claves AS pc" in sql
        assert "pc.id_clave = %s" in sql
        assert "pr.ejercicio IS NOT NULL" in sql

        assert params == (3,)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_ejercicios_filtro(
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# INDICADORES
# ==========================================================

def test_obtener_indicadores_clave(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = {
        "total_procedimientos": 2,
        "total_proveedores_participantes": 5,
        "total_propuestas_iniciales": 8,
        "total_evaluaciones_positivas": 5,
        "total_evaluaciones_negativas": 3,
        "total_propuestas_subasta": 3,
        "total_proveedores_adjudicados": 2,
        "total_procedimientos_adjudicados": 1,
        "cantidad_total_adjudicada": 1000,
    }

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "WITH universo_filtrado AS" in sql
        assert "propuestas_iniciales AS" in sql
        assert "propuestas_subasta AS" in sql
        assert "evaluaciones_filtradas AS" in sql
        assert "adjudicaciones_filtradas AS" in sql
        assert "proveedores_participantes AS" in sql
        assert "UNION" in sql

        assert "FROM simi.procedimientos AS pr" in sql
        assert "INNER JOIN simi.procedimiento_claves AS pc" in sql
        assert "FROM simi.propuestas AS p" in sql
        assert "FROM simi.evaluaciones_tecnicas AS et" in sql
        assert "FROM simi.adjudicaciones AS a" in sql

        assert params == (
            3,
            10,
            2026,
            "INICIAL",
            "SUBASTA",
            "POSITIVA",
            "NEGATIVA",
        )
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        assert fetchall is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_indicadores_clave(
        id_clave=3,
        id_procedimiento=10,
        ejercicio=2026,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# RESUMEN POR PROCEDIMIENTO
# ==========================================================

def test_obtener_resumen_procedimientos(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_procedimiento_clave": 50,
            "id_clave": 3,
            "cantidad_requerida": None,
            "proveedores_oferta_inicial": 4,
            "total_propuestas_iniciales": 4,
            "evaluaciones_positivas": 3,
            "evaluaciones_negativas": 1,
            "total_subastas": 2,
            "proveedores_adjudicados": 2,
            "mejor_precio_inicial": 100,
            "mejor_precio_viable": 105,
            "mejor_precio_subasta": 95,
            "mejor_precio_adjudicado": 96,
            "cantidad_total_adjudicada": 1000,
            "porcentaje_total_adjudicado": 100,
            "valor_total_adjudicado": 96500,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "WITH universo_filtrado AS" in sql
        assert "propuestas_agregadas AS" in sql
        assert "evaluaciones_agregadas AS" in sql
        assert "adjudicaciones_agregadas AS" in sql

        assert "mejor_precio_inicial" in sql
        assert "mejor_precio_viable" in sql
        assert "mejor_precio_subasta" in sql
        assert "mejor_precio_adjudicado" in sql
        assert "valor_total_adjudicado" in sql

        assert params == (
            3,
            10,
            "INICIAL",
            "INICIAL",
            "INICIAL",
            "INICIAL",
            "POSITIVA",
            "SUBASTA",
            "SUBASTA",
            "POSITIVA",
            "POSITIVA",
            "NEGATIVA",
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_resumen_procedimientos(
        id_clave=3,
        id_procedimiento=10,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# DETALLE POR PROVEEDOR
# ==========================================================

def test_obtener_detalle_proveedores(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_proveedor": 15,
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR, S.A. DE C.V.",
            "id_propuesta_inicial": 100,
            "cantidad_inicial": 1000,
            "precio_inicial": 110,
            "id_evaluacion": 50,
            "resultado_tecnico": "POSITIVA",
            "id_propuesta_subasta": 150,
            "cantidad_subasta": 1000,
            "precio_subasta": 95,
            "id_adjudicacion": 80,
            "cantidad_adjudicada": 600,
            "porcentaje_adjudicado": 60,
            "precio_adjudicado": 96,
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "WITH universo_filtrado AS" in sql
        assert "participantes AS" in sql
        assert "propuestas_iniciales AS" in sql
        assert "propuestas_subasta AS" in sql
        assert "evaluaciones AS" in sql
        assert "adjudicaciones AS" in sql
        assert "UNION" in sql

        assert "INNER JOIN simi.proveedores AS pv" in sql
        assert "pi.precio_inicial" in sql
        assert "ps.precio_subasta" in sql
        assert "ev.resultado_tecnico" in sql
        assert "ad.precio_adjudicado" in sql

        assert params == (
            3,
            2026,
            "INICIAL",
            "SUBASTA",
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_detalle_proveedores(
        id_clave=3,
        ejercicio=2026,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# HISTORIAL
# ==========================================================

def test_obtener_historial_precios(monkeypatch):
    repo = AnalisisClaveRepository()

    esperado = [
        {
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_clave": 3,
            "origen_dato": "OPERATIVO",
            "mejor_precio_inicial": 100,
            "mejor_precio_viable": 105,
            "mejor_precio_subasta": 95,
            "mejor_precio_adjudicado": 96,
            "proveedores_adjudicados": 1,
            "cantidad_total_adjudicada": 1000,
            "porcentaje_total_adjudicado": 100,
            "valor_total_adjudicado": 96500,
        },
        {
            "id_procedimiento": None,
            "numero_procedimiento": "HIST-2025-001",
            "ejercicio": 2025,
            "id_clave": 3,
            "origen_dato": "HISTORICO",
            "mejor_precio_inicial": None,
            "mejor_precio_viable": None,
            "mejor_precio_subasta": None,
            "mejor_precio_adjudicado": 98,
            "proveedores_adjudicados": 1,
            "cantidad_total_adjudicada": 500,
            "porcentaje_total_adjudicado": 100,
            "valor_total_adjudicado": 49000,
        },
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        # Universo y precios operativos.
        assert "WITH universo_filtrado AS" in sql
        assert "precios AS" in sql
        assert "adjudicaciones_actuales AS" in sql
        assert "historial_operativo AS" in sql

        # Adjudicaciones históricas.
        assert "historial_adjudicaciones AS" in sql
        assert "simi.adjudicaciones_historicas" in sql
        assert "'OPERATIVO'::TEXT AS origen_dato" in sql
        assert "'HISTORICO'::TEXT AS origen_dato" in sql

        # Campos analíticos esperados.
        assert "mejor_precio_inicial" in sql
        assert "mejor_precio_viable" in sql
        assert "mejor_precio_subasta" in sql
        assert "mejor_precio_adjudicado" in sql
        assert "proveedores_adjudicados" in sql
        assert "cantidad_total_adjudicada" in sql
        assert "porcentaje_total_adjudicado" in sql
        assert "valor_total_adjudicado" in sql

        # Consolidación de operativos e históricos.
        assert "UNION ALL" in sql
        assert "SELECT * FROM historial_operativo" in sql
        assert "SELECT * FROM historial_adjudicaciones" in sql

        # Orden cronológico de la consulta consolidada.
        assert (
            "ORDER BY h.ejercicio NULLS LAST, "
            "h.numero_procedimiento, "
            "h.origen_dato, "
            "h.id_procedimiento NULLS LAST"
        ) in sql

        # La clave se utiliza una vez en el universo operativo
        # y otra en adjudicaciones históricas.
        assert params == (
            3,
            "INICIAL",
            "INICIAL",
            "POSITIVA",
            "SUBASTA",
            "POSITIVA",
            3,
        )

        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(repo, "custom_query", mock_custom_query)

    resultado = repo.obtener_historial_precios(
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado