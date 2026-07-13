"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

database_service.py

Servicio centralizado para:

- Obtener conexiones PostgreSQL.
- Ejecutar consultas SQL.
- Administrar transacciones.
- Confirmar o revertir operaciones.
- Cerrar conexiones propias.

Ningún Repository ni Service debe abrir, confirmar,
revertir o cerrar conexiones directamente.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

import os
from contextlib import contextmanager

import psycopg2
import streamlit as st
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


load_dotenv()


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

def get_config_value(key, default=None):
    """
    Obtiene un valor de configuración.

    Prioridad:
    1. Streamlit Secrets.
    2. Variables de entorno.
    3. Valor predeterminado.
    """

    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, default)


def _get_required_config_value(key):
    """
    Obtiene un valor obligatorio de configuración.

    Lanza una excepción clara cuando no existe.
    """

    value = get_config_value(key)

    if value in (None, ""):
        raise RuntimeError(
            f"No se encontró la configuración obligatoria: {key}"
        )

    return value


# ==========================================================
# CONEXIÓN
# ==========================================================

def get_connection():
    """
    Crea y devuelve una conexión nueva a PostgreSQL.

    La conexión utiliza RealDictCursor para devolver registros
    accesibles mediante el nombre de sus columnas.
    """

    return psycopg2.connect(
        host=_get_required_config_value("DB_HOST"),
        port=get_config_value("DB_PORT", "5432"),
        database=_get_required_config_value("DB_NAME"),
        user=_get_required_config_value("DB_USER"),
        password=_get_required_config_value("DB_PASSWORD"),
        sslmode=get_config_value("DB_SSLMODE", "require"),
        cursor_factory=RealDictCursor,
    )


# ==========================================================
# EJECUCIÓN DE CONSULTAS
# ==========================================================

def execute_query(
    query,
    params=None,
    conn=None,
    fetch=False,
    fetchone=False,
    fetchall=False,
    commit=True,
):
    """
    Ejecuta una consulta SQL.

    Comportamiento:

    - Si no recibe conexión, crea y administra una conexión propia.
    - Si recibe conexión, participa en la transacción existente.
    - Solo confirma o revierte cuando la conexión fue creada aquí.
    - Nunca confirma, revierte ni cierra una conexión externa.

    Parámetros de lectura:

    - fetchone=True:
        Devuelve un solo registro o None.

    - fetchall=True:
        Devuelve una lista de registros.

    - fetch=True:
        Alias temporal de fetchall=True para conservar
        compatibilidad durante la migración de los Repository.

    El parámetro commit se conserva temporalmente por compatibilidad.
    """

    if not query or not str(query).strip():
        raise ValueError("La consulta SQL no puede estar vacía.")

    if fetchone and (fetchall or fetch):
        raise ValueError(
            "No se puede utilizar fetchone junto con fetchall o fetch."
        )

    owns_connection = conn is None
    active_connection = conn

    try:
        if owns_connection:
            active_connection = get_connection()

        with active_connection.cursor() as cursor:
            cursor.execute(query, params)

            if fetchone:
                result = cursor.fetchone()
            elif fetchall or fetch:
                result = cursor.fetchall()
            else:
                result = None

        if owns_connection and commit:
            active_connection.commit()

        return result

    except Exception:
        if owns_connection and active_connection is not None:
            active_connection.rollback()

        raise

    finally:
        if owns_connection and active_connection is not None:
            active_connection.close()


# ==========================================================
# TRANSACCIONES
# ==========================================================

@contextmanager
def database_transaction():
    """
    Proporciona una transacción administrada.

    Uso:

        with database_transaction() as conn:
            repository.insert(data, conn=conn)
            otro_repository.update(id_registro, data, conn=conn)

    Reglas:

    - Abre una sola conexión.
    - Confirma todas las operaciones si terminan correctamente.
    - Revierte todas las operaciones si ocurre una excepción.
    - Siempre cierra la conexión.
    """

    conn = None

    try:
        conn = get_connection()

        yield conn

        conn.commit()

    except Exception:
        if conn is not None:
            conn.rollback()

        raise

    finally:
        if conn is not None:
            conn.close()