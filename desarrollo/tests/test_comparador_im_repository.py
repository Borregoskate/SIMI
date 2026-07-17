"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_comparador_im_repository.py

Pruebas unitarias para ComparadorIMRepository.

Estas pruebas validan:
- Configuración del Repository.
- Preparación de listas.
- Consultas por lotes.
- Uso del esquema simi.
- Parámetros SQL.
- Propagación de conexiones.
- Recuperación de propuestas y adjudicaciones.
- Construcción del contexto consolidado.
- Comportamiento ante listas vacías.

No requieren conexión real a la base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import re

from repositories.comparador_im_repository import (
    ComparadorIMRepository,
)


CONEXION_PRUEBA = object()


def normalizar_sql(query):
    """
    Reduce espacios y saltos de línea para validar SQL
    sin depender del formato visual.
    """
    return re.sub(r"\s+", " ", query).strip()


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

def test_comparador_im_repository_configuracion():
    repo = ComparadorIMRepository()

    assert repo.table_name == "claves"
    assert repo.primary_key == "id_clave"
    assert repo.full_table_name == "simi.claves"

    assert repo.TIPO_INICIAL == "INICIAL"
    assert repo.TIPO_SUBASTA == "SUBASTA"

    assert repo.ORIGEN_OPERATIVO == "OPERATIVO"
    assert repo.ORIGEN_HISTORICO == "HISTORICO"


# ==========================================================
# UTILIDADES INTERNAS
# ==========================================================

def test_preparar_lista_elimina_none_y_duplicados():
    resultado = ComparadorIMRepository._preparar_lista(
        [3, None, 5, 3, 7, None, 5]
    )

    assert resultado == [3, 5, 7]


def test_preparar_lista_con_none_devuelve_lista_vacia():
    resultado = ComparadorIMRepository._preparar_lista(None)

    assert resultado == []


def test_preparar_lista_con_tupla_conserva_orden():
    resultado = ComparadorIMRepository._preparar_lista(
        ("010.001", "010.002", "010.001")
    )

    assert resultado == ["010.001", "010.002"]


# ==========================================================
# RESOLUCIÓN DE CLAVES POR CÓDIGO
# ==========================================================

def test_obtener_claves_por_codigos_lista_vacia_no_consulta(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def mock_custom_query(*args, **kwargs):
        raise AssertionError(
            "No debe ejecutarse SQL con una lista vacía."
        )

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    assert repo.obtener_claves_por_codigos([]) == []
    assert repo.obtener_claves_por_codigos(None) == []


def test_obtener_claves_por_codigos(monkeypatch):
    repo = ComparadorIMRepository()

    esperado = [
        {
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion": "CLAVE DE PRUEBA",
            "id_categoria": 2,
            "categoria": "MEDICAMENTOS",
        },
        {
            "id_clave": 7,
            "clave": "010.000.002",
            "descripcion": "SEGUNDA CLAVE",
            "id_categoria": 2,
            "categoria": "MEDICAMENTOS",
        },
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.claves AS c" in sql
        assert (
            "LEFT JOIN simi.cat_categorias_clave AS cc"
            in sql
        )
        assert "cc.nombre_categoria AS categoria" in sql
        assert "WHERE c.clave = ANY(%s)" in sql
        assert "ORDER BY c.clave, c.id_clave" in sql

        assert params == (
            ["010.000.001", "010.000.002"],
        )
        assert conn is CONEXION_PRUEBA
        assert fetch is False
        assert fetchone is False
        assert fetchall is True

        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.obtener_claves_por_codigos(
        claves=[
            "010.000.001",
            "010.000.002",
            "010.000.001",
        ],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# RESOLUCIÓN INTERNA DE CLAVES POR ID
# ==========================================================

def test_obtener_claves_por_ids_lista_vacia_no_consulta(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def mock_custom_query(*args, **kwargs):
        raise AssertionError(
            "No debe ejecutarse SQL con una lista vacía."
        )

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    assert repo._obtener_claves_por_ids([]) == []


def test_obtener_claves_por_ids(monkeypatch):
    repo = ComparadorIMRepository()

    esperado = [
        {
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion": "CLAVE DE PRUEBA",
            "id_categoria": 2,
            "categoria": "MEDICAMENTOS",
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.claves AS c" in sql
        assert "WHERE c.id_clave = ANY(%s)" in sql
        assert "ORDER BY c.clave, c.id_clave" in sql

        assert params == ([3],)
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo._obtener_claves_por_ids(
        ids_clave=[3, 3, None],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# PROPUESTAS ACUMULADAS
# ==========================================================

def test_obtener_propuestas_acumuladas_lista_vacia_no_consulta(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def mock_custom_query(*args, **kwargs):
        raise AssertionError(
            "No debe ejecutarse SQL con una lista vacía."
        )

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    assert repo.obtener_propuestas_acumuladas([]) == []


def test_obtener_propuestas_acumuladas(monkeypatch):
    repo = ComparadorIMRepository()

    esperado = [
        {
            "id_propuesta": 100,
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion_clave": "CLAVE DE PRUEBA",
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_proveedor": 15,
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR, S.A. DE C.V.",
            "tipo_propuesta": "INICIAL",
            "resultado_tecnico": "POSITIVA",
            "cantidad_ofertada": 1000,
            "pais_origen": "MEXICO",
            "precio_unitario": 110,
            "fecha_registro": None,
        },
        {
            "id_propuesta": 101,
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion_clave": "CLAVE DE PRUEBA",
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_proveedor": 15,
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR, S.A. DE C.V.",
            "tipo_propuesta": "SUBASTA",
            "resultado_tecnico": "POSITIVA",
            "cantidad_ofertada": 1000,
            "pais_origen": "MEXICO",
            "precio_unitario": 95,
            "fecha_registro": None,
        },
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.propuestas AS p" in sql
        assert (
            "INNER JOIN simi.procedimiento_claves AS pc"
            in sql
        )
        assert "INNER JOIN simi.claves AS c" in sql
        assert "INNER JOIN simi.procedimientos AS pr" in sql
        assert "INNER JOIN simi.proveedores AS pv" in sql
        assert (
            "LEFT JOIN simi.evaluaciones_tecnicas AS et"
            in sql
        )

        assert (
            "et.id_procedimiento = pr.id_procedimiento"
            in sql
        )
        assert "et.id_clave = pc.id_clave" in sql
        assert "et.id_proveedor = p.id_proveedor" in sql

        assert "WHERE pc.id_clave = ANY(%s)" in sql
        assert "p.tipo_propuesta = ANY(%s)" in sql
        assert "et.resultado AS resultado_tecnico" in sql
        assert "p.fecha_registro" in sql

        assert params == (
            [3, 7],
            ["INICIAL", "SUBASTA"],
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.obtener_propuestas_acumuladas(
        ids_clave=[3, 7, 3],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# ADJUDICACIONES OPERATIVAS
# ==========================================================

def test_obtener_adjudicaciones_operativas_lista_vacia(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def mock_custom_query(*args, **kwargs):
        raise AssertionError(
            "No debe ejecutarse SQL con una lista vacía."
        )

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    assert repo.obtener_adjudicaciones_operativas([]) == []


def test_obtener_adjudicaciones_operativas(monkeypatch):
    repo = ComparadorIMRepository()

    esperado = [
        {
            "id_adjudicacion": 80,
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion_clave": "CLAVE DE PRUEBA",
            "id_procedimiento": 10,
            "numero_procedimiento": "PROC-001",
            "ejercicio": 2026,
            "id_proveedor": 15,
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR, S.A. DE C.V.",
            "cantidad_adjudicada": 600,
            "porcentaje_adjudicado": 60,
            "precio_unitario_adjudicado": 96,
            "origen_dato": "OPERATIVO",
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert "FROM simi.adjudicaciones AS a" in sql
        assert "INNER JOIN simi.claves AS c" in sql
        assert "INNER JOIN simi.procedimientos AS pr" in sql
        assert "INNER JOIN simi.proveedores AS pv" in sql
        assert "WHERE a.id_clave = ANY(%s)" in sql
        assert "%s::TEXT AS origen_dato" in sql

        assert "GROUP BY" not in sql
        assert "MIN(" not in sql
        assert "MAX(" not in sql
        assert "AVG(" not in sql

        assert params == (
            "OPERATIVO",
            [3],
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.obtener_adjudicaciones_operativas(
        ids_clave=[3],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# ADJUDICACIONES HISTÓRICAS
# ==========================================================

def test_obtener_adjudicaciones_historicas_lista_vacia(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def mock_custom_query(*args, **kwargs):
        raise AssertionError(
            "No debe ejecutarse SQL con una lista vacía."
        )

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    assert repo.obtener_adjudicaciones_historicas([]) == []


def test_obtener_adjudicaciones_historicas(monkeypatch):
    repo = ComparadorIMRepository()

    esperado = [
        {
            "id_adjudicacion_historica": 90,
            "id_clave": 3,
            "clave": "010.000.001",
            "descripcion_clave": "CLAVE DE PRUEBA",
            "id_procedimiento": None,
            "numero_procedimiento": "LA-001-2023",
            "ejercicio": 2023,
            "id_proveedor": 20,
            "rfc": "XYZ010101AA1",
            "razon_social": "PROVEEDOR HISTORICO",
            "cantidad_adjudicada": 800,
            "porcentaje_adjudicado": 100,
            "precio_unitario_adjudicado": 108.75,
            "origen_dato": "HISTORICO",
        }
    ]

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        sql = normalizar_sql(query)

        assert (
            "FROM simi.adjudicaciones_historicas AS ah"
            in sql
        )
        assert "INNER JOIN simi.claves AS c" in sql
        assert "INNER JOIN simi.proveedores AS pv" in sql
        assert "WHERE ah.id_clave = ANY(%s)" in sql
        assert "NULL::BIGINT AS id_procedimiento" in sql
        assert "%s::TEXT AS origen_dato" in sql

        assert (
            "SUBSTRING( ah.numero_procedimiento "
            "FROM '(20[0-9]{2})' )"
            in sql
        )
        assert "END AS ejercicio" in sql

        assert "GROUP BY" not in sql
        assert "MIN(" not in sql
        assert "MAX(" not in sql
        assert "AVG(" not in sql

        assert params == (
            "HISTORICO",
            [3, 7],
        )
        assert conn is CONEXION_PRUEBA
        assert fetchall is True
        assert fetchone is False

        return esperado

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    resultado = repo.obtener_adjudicaciones_historicas(
        ids_clave=[3, 7],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == esperado


# ==========================================================
# CONTEXTO CONSOLIDADO
# ==========================================================

def test_obtener_contexto_comparacion_lista_vacia(
    monkeypatch,
):
    repo = ComparadorIMRepository()

    def metodo_no_permitido(*args, **kwargs):
        raise AssertionError(
            "No debe llamarse ningún método de consulta."
        )

    monkeypatch.setattr(
        repo,
        "_obtener_claves_por_ids",
        metodo_no_permitido,
    )
    monkeypatch.setattr(
        repo,
        "obtener_propuestas_acumuladas",
        metodo_no_permitido,
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_operativas",
        metodo_no_permitido,
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_historicas",
        metodo_no_permitido,
    )

    resultado = repo.obtener_contexto_comparacion([])

    assert resultado == {
        "claves": [],
        "propuestas": [],
        "adjudicaciones_operativas": [],
        "adjudicaciones_historicas": [],
    }


def test_obtener_contexto_comparacion(monkeypatch):
    repo = ComparadorIMRepository()

    claves = [{"id_clave": 3}]
    propuestas = [{"id_propuesta": 100}]
    operativas = [{"id_adjudicacion": 80}]
    historicas = [{"id_adjudicacion_historica": 90}]

    llamadas = []

    def mock_claves(ids_clave, conn=None):
        llamadas.append(("claves", ids_clave, conn))
        return claves

    def mock_propuestas(ids_clave, conn=None):
        llamadas.append(("propuestas", ids_clave, conn))
        return propuestas

    def mock_operativas(ids_clave, conn=None):
        llamadas.append(("operativas", ids_clave, conn))
        return operativas

    def mock_historicas(ids_clave, conn=None):
        llamadas.append(("historicas", ids_clave, conn))
        return historicas

    monkeypatch.setattr(
        repo,
        "_obtener_claves_por_ids",
        mock_claves,
    )
    monkeypatch.setattr(
        repo,
        "obtener_propuestas_acumuladas",
        mock_propuestas,
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_operativas",
        mock_operativas,
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_historicas",
        mock_historicas,
    )

    resultado = repo.obtener_contexto_comparacion(
        ids_clave=[3, 7, 3, None],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == {
        "claves": claves,
        "propuestas": propuestas,
        "adjudicaciones_operativas": operativas,
        "adjudicaciones_historicas": historicas,
    }

    assert llamadas == [
        ("claves", [3, 7], CONEXION_PRUEBA),
        ("propuestas", [3, 7], CONEXION_PRUEBA),
        ("operativas", [3, 7], CONEXION_PRUEBA),
        ("historicas", [3, 7], CONEXION_PRUEBA),
    ]


def test_contexto_conserva_resultados_vacios(monkeypatch):
    repo = ComparadorIMRepository()

    monkeypatch.setattr(
        repo,
        "_obtener_claves_por_ids",
        lambda ids_clave, conn=None: [],
    )
    monkeypatch.setattr(
        repo,
        "obtener_propuestas_acumuladas",
        lambda ids_clave, conn=None: [],
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_operativas",
        lambda ids_clave, conn=None: [],
    )
    monkeypatch.setattr(
        repo,
        "obtener_adjudicaciones_historicas",
        lambda ids_clave, conn=None: [],
    )

    resultado = repo.obtener_contexto_comparacion(
        ids_clave=[999],
        conn=CONEXION_PRUEBA,
    )

    assert resultado == {
        "claves": [],
        "propuestas": [],
        "adjudicaciones_operativas": [],
        "adjudicaciones_historicas": [],
    }


# ==========================================================
# SEGURIDAD ARQUITECTÓNICA
# ==========================================================

def test_repository_solo_contiene_consultas_select(monkeypatch):
    repo = ComparadorIMRepository()

    consultas = []

    def mock_custom_query(
        query,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        consultas.append(normalizar_sql(query).upper())
        return []

    monkeypatch.setattr(
        repo,
        "custom_query",
        mock_custom_query,
    )

    repo.obtener_claves_por_codigos(["010.000.001"])
    repo._obtener_claves_por_ids([3])
    repo.obtener_propuestas_acumuladas([3])
    repo.obtener_adjudicaciones_operativas([3])
    repo.obtener_adjudicaciones_historicas([3])

    assert len(consultas) == 5

    for sql in consultas:
        assert sql.startswith("SELECT")
        assert " INSERT " not in f" {sql} "
        assert " UPDATE " not in f" {sql} "
        assert " DELETE " not in f" {sql} "
        assert " TRUNCATE " not in f" {sql} "
        assert " DROP " not in f" {sql} "