"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimiento_claves_repository.py

Repositorio para la tabla procedimiento_claves.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from psycopg2.extras import RealDictCursor


class ProcedimientoClavesRepository:
    """
    Repositorio para relacionar procedimientos con claves.
    """

    def get_by_procedimiento_clave(
        self,
        conn,
        id_procedimiento: int,
        id_clave: int
    ):
        query = """
            SELECT *
            FROM procedimiento_claves
            WHERE id_procedimiento = %s
              AND id_clave = %s
            LIMIT 1;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    id_procedimiento,
                    id_clave
                )
            )
            return cursor.fetchone()

    def crear(
        self,
        conn,
        id_procedimiento: int,
        id_clave: int,
        cantidad_requerida=None
    ):
        query = """
            INSERT INTO procedimiento_claves (
                id_procedimiento,
                id_clave,
                cantidad_requerida
            )
            VALUES (%s, %s, %s)
            RETURNING *;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    id_procedimiento,
                    id_clave,
                    cantidad_requerida
                )
            )
            return cursor.fetchone()

    def actualizar_cantidad(
        self,
        conn,
        id_procedimiento_clave: int,
        cantidad_requerida=None
    ):
        query = """
            UPDATE procedimiento_claves
            SET cantidad_requerida = %s
            WHERE id_procedimiento_clave = %s
            RETURNING *;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    cantidad_requerida,
                    id_procedimiento_clave
                )
            )
            return cursor.fetchone()