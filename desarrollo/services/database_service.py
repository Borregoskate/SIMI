"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

database_service.py

Servicio centralizado para ejecutar consultas SQL.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_config_value(key, default=None):
    """
    Obtiene configuración desde Streamlit Secrets o variables de entorno.
    """
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def get_connection():
    """
    Crea una conexión nueva a PostgreSQL / Supabase.
    """
    return psycopg2.connect(
        host=get_config_value("DB_HOST"),
        port=get_config_value("DB_PORT"),
        database=get_config_value("DB_NAME"),
        user=get_config_value("DB_USER"),
        password=get_config_value("DB_PASSWORD"),
        sslmode=get_config_value("DB_SSLMODE", "require"),
        cursor_factory=RealDictCursor
    )


def execute_query(
    query,
    params=None,
    conn=None,
    fetch=False,
    fetchone=False,
    fetchall=False,
    commit=True
):
    """
    Ejecuta una consulta SQL.

    Soporta:
    - Conexión automática.
    - Conexión externa para transacciones.
    - fetch=True para compatibilidad con repositories existentes.
    - fetchone=True.
    - fetchall=True.
    """

    owns_connection = conn is None

    if owns_connection:
        conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)

            result = None

            if fetchone:
                result = cursor.fetchone()
            elif fetchall or fetch:
                result = cursor.fetchall()

            if owns_connection and commit:
                conn.commit()

            return result

    except Exception as e:
        if owns_connection:
            conn.rollback()
        raise e

    finally:
        if owns_connection and conn:
            conn.close()