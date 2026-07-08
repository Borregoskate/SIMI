"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_database_connection.py

Prueba de conexión real a PostgreSQL / Supabase.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from services.database_service import execute_query


def test_database_connection():
    """
    Prueba la conexión ejecutando una consulta simple.
    """

    query = "SELECT version() AS version;"

    result = execute_query(
        query=query,
        fetchone=True
    )

    print("Conexión exitosa a PostgreSQL / Supabase.")
    print(result["version"])


if __name__ == "__main__":
    test_database_connection()