"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimiento_fases_repository.py

Repositorio para la tabla simi.procedimiento_fases.

Registra la bitácora de fases de cada procedimiento.

Las fechas son generadas automáticamente por PostgreSQL
mediante CURRENT_TIMESTAMP.

Este Repository:

- No normaliza fases.
- No valida transiciones.
- No abre conexiones.
- No administra cursores.
- No confirma ni revierte transacciones.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProcedimientoFasesRepository(BaseRepository):
    """
    Repositorio especializado para la bitácora de fases
    de los procedimientos.
    """

    def __init__(self):
        super().__init__(
            table_name="procedimiento_fases",
            primary_key="id_procedimiento_fase",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve el historial de fases de un procedimiento.

        El registro más reciente aparece primero.
        """

        query = """
            SELECT *
            FROM simi.procedimiento_fases
            WHERE id_procedimiento = %s
            ORDER BY
                fecha DESC,
                id_procedimiento_fase DESC;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    def get_ultima_fase(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve la fase más reciente de un procedimiento.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.procedimiento_fases
            WHERE id_procedimiento = %s
            ORDER BY
                fecha DESC,
                id_procedimiento_fase DESC
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # REGISTRO DE FASE
    # ==========================================================

    def registrar_fase(
        self,
        id_procedimiento: int,
        fase: str,
        conn=None,
    ):
        """
        Registra una fase para un procedimiento.

        La fase debe llegar normalizada y validada por el Service.
        La fecha se genera automáticamente en PostgreSQL.
        """

        query = """
            INSERT INTO simi.procedimiento_fases (
                id_procedimiento,
                fase,
                fecha
            )
            VALUES (
                %s,
                %s,
                CURRENT_TIMESTAMP
            )
            RETURNING *;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                fase,
            ),
            conn=conn,
            fetchone=True,
        )