"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

database_service.py

Servicio centralizado para ejecutar consultas SQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from config.database import get_connection


def execute_query(query, params=None, fetch=False):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        if fetch:
            columns = [desc[0] for desc in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            connection.commit()
            return results

        connection.commit()
        return None

    except Exception as error:
        if connection:
            connection.rollback()

        print("Error ejecutando consulta:")
        print(error)
        raise error

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()