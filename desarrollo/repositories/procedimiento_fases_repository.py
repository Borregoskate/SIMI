"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimiento_fases_repository.py

Repositorio para la tabla procedimiento_fases.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from psycopg2.extras import RealDictCursor


class ProcedimientoFasesRepository:
    """
    Repositorio para registrar fases del procedimiento.
    """

    def registrar_fase(
        self,
        conn,
        id_procedimiento: int,
        fase: str
    ):
        query = """
            INSERT INTO procedimiento_fases (
                id_procedimiento,
                fase,
                fecha
            )
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            RETURNING *;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    id_procedimiento,
                    fase
                )
            )
            return cursor.fetchone()