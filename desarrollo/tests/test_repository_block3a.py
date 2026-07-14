"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_repository_block3a.py

Pruebas unitarias del Bloque 3A:
- EvaluacionesTecnicasRepository
- PropuestasRepository para SUBASTA
- AdjudicacionesRepository

Estas pruebas no requieren conexión a PostgreSQL.
Validan que los repositories deleguen correctamente las
operaciones a BaseRepository y transmitan la conexión externa.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

from repositories.adjudicaciones_repository import (
    AdjudicacionesRepository,
)
from repositories.evaluaciones_tecnicas_repository import (
    EvaluacionesTecnicasRepository,
)
from repositories.propuestas_repository import (
    PropuestasRepository,
)


CONEXION_PRUEBA = object()


# ==========================================================
# EVALUACIONES TÉCNICAS
# ==========================================================

def test_evaluaciones_repository_configuracion():
    repo = EvaluacionesTecnicasRepository()

    assert repo.table_name == "evaluaciones_tecnicas"
    assert repo.primary_key == "id_evaluacion"


def test_evaluaciones_get_by_combinacion(monkeypatch):
    repo = EvaluacionesTecnicasRepository()
    esperado = {
        "id_evaluacion": 10,
        "id_procedimiento": 1,
        "id_proveedor": 2,
        "id_clave": 3,
        "resultado": "POSITIVA",
    }

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "FROM simi.evaluaciones_tecnicas" in query
        assert params == (1, 2, 3)
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        assert fetchall is False
        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.get_by_combinacion(
        id_procedimiento=1,
        id_proveedor=2,
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_evaluaciones_crear_evaluacion(monkeypatch):
    repo = EvaluacionesTecnicasRepository()
    esperado = {
        "id_evaluacion": 20,
        "id_procedimiento": 1,
        "id_proveedor": 2,
        "id_clave": 3,
        "resultado": "NEGATIVA",
    }

    def mock_insert(data, conn=None):
        assert data == {
            "id_procedimiento": 1,
            "id_proveedor": 2,
            "id_clave": 3,
            "resultado": "NEGATIVA",
        }
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(repo, "insert", mock_insert)

    resultado = repo.crear_evaluacion(
        id_procedimiento=1,
        id_proveedor=2,
        id_clave=3,
        resultado="NEGATIVA",
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_evaluaciones_actualizar_resultado(monkeypatch):
    repo = EvaluacionesTecnicasRepository()
    esperado = {
        "id_evaluacion": 20,
        "resultado": "POSITIVA",
    }

    def mock_update(record_id, data, conn=None):
        assert record_id == 20
        assert data == {"resultado": "POSITIVA"}
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(repo, "update", mock_update)

    resultado = repo.actualizar_resultado(
        id_evaluacion=20,
        resultado="POSITIVA",
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_evaluaciones_proveedor_aprobado(monkeypatch):
    repo = EvaluacionesTecnicasRepository()

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "FROM simi.evaluaciones_tecnicas" in query
        assert "resultado = %s" in query
        assert params == (1, 2, 3, "POSITIVA")
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        return {"id_evaluacion": 30, "resultado": "POSITIVA"}

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.proveedor_aprobado_para_clave(
        id_procedimiento=1,
        id_proveedor=2,
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert resultado["resultado"] == "POSITIVA"


# ==========================================================
# PROPUESTAS DE SUBASTA
# ==========================================================

def test_propuestas_repository_tipos():
    repo = PropuestasRepository()

    assert repo.table_name == "propuestas"
    assert repo.primary_key == "id_propuesta"
    assert repo.TIPO_INICIAL == "INICIAL"
    assert repo.TIPO_SUBASTA == "SUBASTA"


def test_propuestas_existe_subasta(monkeypatch):
    repo = PropuestasRepository()
    esperado = {
        "id_propuesta": 40,
        "tipo_propuesta": "SUBASTA",
    }

    def mock_get_by_combinacion(
        id_procedimiento_clave,
        id_proveedor,
        tipo_propuesta,
        conn=None,
    ):
        assert id_procedimiento_clave == 11
        assert id_proveedor == 22
        assert tipo_propuesta == "SUBASTA"
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(
        repo,
        "get_by_combinacion",
        mock_get_by_combinacion,
    )

    resultado = repo.existe_propuesta_subasta(
        id_procedimiento_clave=11,
        id_proveedor=22,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_propuestas_crear_subasta(monkeypatch):
    repo = PropuestasRepository()
    esperado = {
        "id_propuesta": 50,
        "tipo_propuesta": "SUBASTA",
    }

    def mock_crear_propuesta(
        id_procedimiento_clave,
        id_proveedor,
        tipo_propuesta,
        cantidad_ofertada,
        pais_origen,
        precio_unitario,
        conn=None,
    ):
        assert id_procedimiento_clave == 11
        assert id_proveedor == 22
        assert tipo_propuesta == "SUBASTA"
        assert cantidad_ofertada == Decimal("100")
        assert pais_origen == "MEXICO"
        assert precio_unitario == Decimal("25.50")
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(
        repo,
        "crear_propuesta",
        mock_crear_propuesta,
    )

    resultado = repo.crear_propuesta_subasta(
        id_procedimiento_clave=11,
        id_proveedor=22,
        cantidad_ofertada=Decimal("100"),
        pais_origen="MEXICO",
        precio_unitario=Decimal("25.50"),
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_propuestas_actualizar_subasta(monkeypatch):
    repo = PropuestasRepository()
    esperado = {
        "id_propuesta": 50,
        "precio_unitario": Decimal("24.00"),
    }

    def mock_update(record_id, data, conn=None):
        assert record_id == 50
        assert data == {
            "cantidad_ofertada": Decimal("120"),
            "pais_origen": "MEXICO",
            "precio_unitario": Decimal("24.00"),
        }
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(repo, "update", mock_update)

    resultado = repo.actualizar_propuesta_subasta(
        id_propuesta=50,
        cantidad_ofertada=Decimal("120"),
        pais_origen="MEXICO",
        precio_unitario=Decimal("24.00"),
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado



# ==========================================================
# ADJUDICACIONES
# ==========================================================

def test_adjudicaciones_repository_configuracion():
    repo = AdjudicacionesRepository()

    assert repo.table_name == "adjudicaciones"
    assert repo.primary_key == "id_adjudicacion"


def test_adjudicaciones_get_by_combinacion(monkeypatch):
    repo = AdjudicacionesRepository()
    esperado = {
        "id_adjudicacion": 60,
        "id_procedimiento": 1,
        "id_clave": 3,
        "id_proveedor": 2,
    }

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "FROM simi.adjudicaciones" in query
        assert params == (1, 3, 2)
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        assert fetchall is False
        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.get_by_combinacion(
        id_procedimiento=1,
        id_clave=3,
        id_proveedor=2,
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_adjudicaciones_crear(monkeypatch):
    repo = AdjudicacionesRepository()
    esperado = {
        "id_adjudicacion": 70,
        "porcentaje_adjudicado": Decimal("60"),
    }

    def mock_insert(data, conn=None):
        assert data == {
            "id_procedimiento": 1,
            "id_clave": 3,
            "id_proveedor": 2,
            "cantidad_adjudicada": Decimal("600"),
            "porcentaje_adjudicado": Decimal("60"),
            "precio_unitario_adjudicado": Decimal("24.00"),
        }
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(repo, "insert", mock_insert)

    resultado = repo.crear_adjudicacion(
        id_procedimiento=1,
        id_clave=3,
        id_proveedor=2,
        cantidad_adjudicada=Decimal("600"),
        porcentaje_adjudicado=Decimal("60"),
        precio_unitario_adjudicado=Decimal("24.00"),
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_adjudicaciones_actualizar(monkeypatch):
    repo = AdjudicacionesRepository()
    esperado = {
        "id_adjudicacion": 70,
        "porcentaje_adjudicado": Decimal("70"),
    }

    def mock_update(record_id, data, conn=None):
        assert record_id == 70
        assert data == {
            "cantidad_adjudicada": Decimal("700"),
            "porcentaje_adjudicado": Decimal("70"),
            "precio_unitario_adjudicado": Decimal("23.50"),
        }
        assert conn is CONEXION_PRUEBA
        return esperado

    monkeypatch.setattr(repo, "update", mock_update)

    resultado = repo.actualizar_adjudicacion(
        id_adjudicacion=70,
        cantidad_adjudicada=Decimal("700"),
        porcentaje_adjudicado=Decimal("70"),
        precio_unitario_adjudicado=Decimal("23.50"),
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


def test_adjudicaciones_consultas_agregadas(monkeypatch):
    repo = AdjudicacionesRepository()
    respuestas = iter(
        [
            {"total": 2},
            {"porcentaje_total": Decimal("100")},
        ]
    )

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetchone=False,
        fetchall=False,
    ):
        assert "FROM simi.adjudicaciones" in query
        assert params == (1, 3)
        assert conn is CONEXION_PRUEBA
        assert fetchone is True
        return next(respuestas)

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    cantidad = repo.contar_proveedores_adjudicados(
        id_procedimiento=1,
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )
    porcentaje = repo.sumar_porcentaje_adjudicado(
        id_procedimiento=1,
        id_clave=3,
        conn=CONEXION_PRUEBA,
    )

    assert cantidad["total"] == 2
    assert porcentaje["porcentaje_total"] == Decimal("100")
