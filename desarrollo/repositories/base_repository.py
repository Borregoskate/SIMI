"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

base_repository.py

Repositorio base para acceso a datos.
Centraliza operaciones comunes hacia PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from services.database_service import execute_query


class BaseRepository:
    """
    Clase base para todos los repositorios de SIMI.
    No contiene lógica de negocio.
    """

    def __init__(self, table_name: str, primary_key: str):
        self.schema = "simi"
        self.table_name = table_name
        self.primary_key = primary_key

    def _full_table_name(self):
        return f"{self.schema}.{self.table_name}"

    # ==========================================================
    # CONSULTAS BÁSICAS
    # ==========================================================

    def get_all(self, conn=None):
        query = f"""
            SELECT *
            FROM {self._full_table_name()}
            ORDER BY {self.primary_key};
        """
        return execute_query(query, conn=conn, fetch=True)

    def get_by_id(self, record_id, conn=None):
        query = f"""
            SELECT *
            FROM {self._full_table_name()}
            WHERE {self.primary_key} = %s
            LIMIT 1;
        """
        result = execute_query(
            query,
            params=(record_id,),
            conn=conn,
            fetch=True
        )
        return result[0] if result else None

    def get_by_field(self, field_name: str, value, conn=None):
        query = f"""
            SELECT *
            FROM {self._full_table_name()}
            WHERE {field_name} = %s
            ORDER BY {self.primary_key};
        """
        return execute_query(
            query,
            params=(value,),
            conn=conn,
            fetch=True
        )

    def exists_by_field(self, field_name: str, value, conn=None):
        query = f"""
            SELECT EXISTS (
                SELECT 1
                FROM {self._full_table_name()}
                WHERE {field_name} = %s
            ) AS exists;
        """
        result = execute_query(
            query,
            params=(value,),
            conn=conn,
            fetch=True
        )
        if not result:
            return False

        first_row = result[0]

        if isinstance(first_row, dict):
            return first_row.get("exists", False)

        return first_row[0]

    # ==========================================================
    # INSERT / UPDATE / DELETE
    # ==========================================================

    def insert(self, data: dict, conn=None):
        if not data:
            raise ValueError("No se recibieron datos para insertar.")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())

        query = f"""
            INSERT INTO {self._full_table_name()} ({columns})
            VALUES ({placeholders})
            RETURNING *;
        """

        result = execute_query(
            query,
            params=values,
            conn=conn,
            fetch=True
        )
        return result[0] if result else None

    def update(self, record_id, data: dict, conn=None):
        if not data:
            raise ValueError("No se recibieron datos para actualizar.")

        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)

        query = f"""
            UPDATE {self._full_table_name()}
            SET {set_clause}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        result = execute_query(
            query,
            params=values,
            conn=conn,
            fetch=True
        )
        return result[0] if result else None

    def delete(self, record_id, conn=None):
        query = f"""
            DELETE FROM {self._full_table_name()}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        result = execute_query(
            query,
            params=(record_id,),
            conn=conn,
            fetch=True
        )
        return result[0] if result else None

    # ==========================================================
    # CONSULTAS PERSONALIZADAS
    # ==========================================================

    def custom_query(self, query: str, params=None, conn=None, fetch=True):
        return execute_query(
            query,
            params=params,
            conn=conn,
            fetch=fetch
        )