"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimiento_claves_repository.py

Repositorio para la tabla simi.procedimiento_claves.

Relaciona las claves que forman parte del universo de cada
procedimiento.

La cantidad requerida es opcional por decisión funcional
autorizada para SIMI.

Este Repository:

- No normaliza datos.
- No valida reglas de negocio.
- No abre conexiones.
- No administra cursores.
- No confirma ni revierte transacciones.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProcedimientoClavesRepository(BaseRepository):
    """
    Repositorio especializado para la relación entre
    procedimientos y claves.
    """

    def __init__(self):
        super().__init__(
            table_name="procedimiento_claves",
            primary_key="id_procedimiento_clave",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_procedimiento_clave(
        self,
        id_procedimiento: int,
        id_clave: int,
        conn=None,
    ):
        """
        Busca la relación entre un procedimiento y una clave.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.procedimiento_claves
            WHERE id_procedimiento = %s
              AND id_clave = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_clave,
            ),
            conn=conn,
            fetchone=True,
        )

    def get_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve todas las claves asociadas a un procedimiento.
        """

        query = """
            SELECT *
            FROM simi.procedimiento_claves
            WHERE id_procedimiento = %s
            ORDER BY id_procedimiento_clave;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    def get_detalle_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve las claves de un procedimiento junto con
        los datos básicos del catálogo de claves.
        """

        query = """
            SELECT
                pc.id_procedimiento_clave,
                pc.id_procedimiento,
                pc.id_clave,
                pc.cantidad_requerida,
                c.clave,
                c.descripcion,
                c.id_categoria
            FROM simi.procedimiento_claves AS pc
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            WHERE pc.id_procedimiento = %s
            ORDER BY
                c.clave,
                pc.id_procedimiento_clave;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear(
        self,
        id_procedimiento: int,
        id_clave: int,
        cantidad_requerida=None,
        conn=None,
    ):
        """
        Relaciona una clave con un procedimiento.

        cantidad_requerida puede ser None.
        """

        data = {
            "id_procedimiento": id_procedimiento,
            "id_clave": id_clave,
            "cantidad_requerida": cantidad_requerida,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_cantidad(
        self,
        id_procedimiento_clave: int,
        cantidad_requerida=None,
        conn=None,
    ):
        """
        Actualiza la cantidad requerida.

        El valor puede permanecer en None cuando la información
        no esté disponible o no sea confiable.
        """

        return self.update(
            record_id=id_procedimiento_clave,
            data={
                "cantidad_requerida": cantidad_requerida,
            },
            conn=conn,
        )