"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

database.py

Configuración de conexión a PostgreSQL / Supabase.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


load_dotenv()


def get_connection():
    """
    Crea y devuelve una conexión activa a PostgreSQL.
    """

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        options="-c search_path=simi,public",
        cursor_factory=RealDictCursor
    )