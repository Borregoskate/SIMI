"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimientos_repository.py

Repositorio para la tabla procedimientos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from psycopg2.extras import RealDictCursor


class ProcedimientosRepository:
    """
    Repositorio específico para procedimientos.
    """

    def get_activos(self, conn):
        query = """
            SELECT *
            FROM procedimientos
            WHERE activo = TRUE
            ORDER BY fecha_creacion DESC, id_procedimiento DESC;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_by_numero_procedimiento(self, conn, numero_procedimiento: str):
        query = """
            SELECT *
            FROM procedimientos
            WHERE numero_procedimiento = %s
            LIMIT 1;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (numero_procedimiento,))
            return cursor.fetchone()

    def crear_procedimiento(
        self,
        conn,
        numero_procedimiento: str,
        descripcion: str | None,
        ejercicio: int,
        activo: bool = True
    ):
        query = """
            INSERT INTO procedimientos (
                numero_procedimiento,
                descripcion,
                ejercicio,
                activo
            )
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    numero_procedimiento,
                    descripcion,
                    ejercicio,
                    activo
                )
            )
            return cursor.fetchone()

    def desactivar(self, conn, id_procedimiento: int):
        query = """
            UPDATE procedimientos
            SET activo = FALSE
            WHERE id_procedimiento = %s
            RETURNING *;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (id_procedimiento,))
            return cursor.fetchone()