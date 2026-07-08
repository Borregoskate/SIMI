"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

adjudicaciones_repository.py

Repositorio para la tabla adjudicaciones.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class AdjudicacionesRepository(BaseRepository):
    """
    Repositorio para adjudicaciones actuales del sistema.
    """

    def __init__(self):
        super().__init__(
            table_name="adjudicaciones",
            primary_key="id_adjudicacion"
        )

    def get_by_procedimiento(self, id_procedimiento: int):
        query = """
            SELECT *
            FROM adjudicaciones
            WHERE id_procedimiento = %s
            ORDER BY id_clave, porcentaje_adjudicado DESC;
        """

        return self.custom_query(
            query,
            params=(id_procedimiento,),
            fetch=True
        )

    def get_by_clave(self, id_clave: int):
        query = """
            SELECT *
            FROM adjudicaciones
            WHERE id_clave = %s
            ORDER BY precio_unitario_adjudicado ASC;
        """

        return self.custom_query(
            query,
            params=(id_clave,),
            fetch=True
        )

    def get_by_proveedor(self, id_proveedor: int):
        query = """
            SELECT *
            FROM adjudicaciones
            WHERE id_proveedor = %s
            ORDER BY id_procedimiento DESC, id_clave;
        """

        return self.custom_query(
            query,
            params=(id_proveedor,),
            fetch=True
        )

    def crear_adjudicacion(
        self,
        id_procedimiento: int,
        id_clave: int,
        id_proveedor: int,
        cantidad_adjudicada,
        porcentaje_adjudicado,
        precio_unitario_adjudicado
    ):
        data = {
            "id_procedimiento": id_procedimiento,
            "id_clave": id_clave,
            "id_proveedor": id_proveedor,
            "cantidad_adjudicada": cantidad_adjudicada,
            "porcentaje_adjudicado": porcentaje_adjudicado,
            "precio_unitario_adjudicado": precio_unitario_adjudicado
        }

        return self.insert(data)