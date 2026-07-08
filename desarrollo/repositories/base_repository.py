"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

base_repository.py

Repositorio base para acceso a datos.
Centraliza operaciones comunes hacia PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.0.0
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

    # ==========================================================
    # CONSULTAS BÁSICAS
    # ==========================================================

    def get_all(self):
        query = f"""
            SELECT *
            FROM {self.table_name}
            ORDER BY {self.primary_key};
        """
        return execute_query(query, fetch=True)

    def get_by_id(self, record_id):
        query = f"""
            SELECT *
            FROM {self.table_name}
            WHERE {self.primary_key} = %s;
        """
        result = execute_query(query, params=(record_id,), fetch=True)
        return result[0] if result else None

    def get_by_field(self, field_name: str, value):
        query = f"""
            SELECT *
            FROM {self.table_name}
            WHERE {field_name} = %s
            ORDER BY {self.primary_key};
        """
        return execute_query(query, params=(value,), fetch=True)

    def exists_by_field(self, field_name: str, value):
        query = f"""
            SELECT EXISTS (
                SELECT 1
                FROM {self.table_name}
                WHERE {field_name} = %s
            ) AS exists;
        """
        result = execute_query(query, params=(value,), fetch=True)
        return result[0]["exists"] if result else False

    # ==========================================================
    # INSERT / UPDATE / DELETE
    # ==========================================================

    def insert(self, data: dict):
        if not data:
            raise ValueError("No se recibieron datos para insertar.")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())

        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
            RETURNING *;
        """

        result = execute_query(query, params=values, fetch=True)
        return result[0] if result else None

    def update(self, record_id, data: dict):
        if not data:
            raise ValueError("No se recibieron datos para actualizar.")

        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)

        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        result = execute_query(query, params=values, fetch=True)
        return result[0] if result else None

    def delete(self, record_id):
        query = f"""
            DELETE FROM {self.table_name}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        result = execute_query(query, params=(record_id,), fetch=True)
        return result[0] if result else None

    # ==========================================================
    # OPERACIONES MASIVAS
    # ==========================================================

    def bulk_insert(self, records: list[dict]):
        """
        Inserta múltiples registros.

        records debe tener esta forma:
        [
            {"campo1": valor1, "campo2": valor2},
            {"campo1": valor3, "campo2": valor4}
        ]
        """

        if not records:
            raise ValueError("No se recibieron registros para insertar.")

        columns = list(records[0].keys())
        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
            INSERT INTO {self.table_name} ({column_names})
            VALUES ({placeholders})
            RETURNING *;
        """

        inserted_records = []

        for record in records:
            values = tuple(record[column] for column in columns)
            result = execute_query(query, params=values, fetch=True)

            if result:
                inserted_records.append(result[0])

        return inserted_records

    # ==========================================================
    # PAGINACIÓN Y FILTROS
    # ==========================================================

    def get_paginated(self, limit: int = 50, offset: int = 0):
        query = f"""
            SELECT *
            FROM {self.table_name}
            ORDER BY {self.primary_key}
            LIMIT %s OFFSET %s;
        """

        return execute_query(
            query,
            params=(limit, offset),
            fetch=True
        )

    def get_filtered(self, filters: dict):
        """
        Consulta registros usando filtros dinámicos con AND.

        Ejemplo:
        {
            "activo": True,
            "ejercicio": 2026
        }
        """

        if not filters:
            return self.get_all()

        where_clause = " AND ".join(
            [f"{column} = %s" for column in filters.keys()]
        )

        values = tuple(filters.values())

        query = f"""
            SELECT *
            FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY {self.primary_key};
        """

        return execute_query(query, params=values, fetch=True)

    # ==========================================================
    # CONSULTAS PERSONALIZADAS
    # ==========================================================

    def custom_query(self, query: str, params=None, fetch=True):
        """
        Ejecuta consultas personalizadas.
        Solo debe usarse dentro de repositories específicos.
        """

        return execute_query(
            query,
            params=params,
            fetch=fetch
        )