"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

propuestas_repository.py

Repositorio para la tabla propuestas.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class PropuestasRepository(BaseRepository):
    """
    Repositorio para propuestas iniciales y propuestas de subasta.
    """

    def __init__(self):
        super().__init__(
            table_name="propuestas",
            primary_key="id_propuesta"
        )

    def get_by_procedimiento_clave(self, id_procedimiento_clave: int):
        """
        Obtiene propuestas por clave dentro de un procedimiento.
        """
        query = """
            SELECT *
            FROM propuestas
            WHERE id_procedimiento_clave = %s
            ORDER BY precio_unitario ASC;
        """

        return self.custom_query(
            query,
            params=(id_procedimiento_clave,),
            fetch=True
        )

    def get_by_proveedor(self, id_proveedor: int):
        """
        Obtiene propuestas por proveedor.
        """
        query = """
            SELECT *
            FROM propuestas
            WHERE id_proveedor = %s
            ORDER BY fecha_registro DESC;
        """

        return self.custom_query(
            query,
            params=(id_proveedor,),
            fetch=True
        )

    def get_by_tipo(self, tipo_propuesta: str):
        """
        Obtiene propuestas por tipo:
        INICIAL o SUBASTA.
        """
        query = """
            SELECT *
            FROM propuestas
            WHERE tipo_propuesta = %s
            ORDER BY fecha_registro DESC;
        """

        return self.custom_query(
            query,
            params=(tipo_propuesta,),
            fetch=True
        )

    def crear_propuesta(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        tipo_propuesta: str,
        cantidad_ofertada,
        id_pais_origen: int,
        precio_unitario
    ):
        """
        Crea una propuesta.
        """
        data = {
            "id_procedimiento_clave": id_procedimiento_clave,
            "id_proveedor": id_proveedor,
            "tipo_propuesta": tipo_propuesta,
            "cantidad_ofertada": cantidad_ofertada,
            "id_pais_origen": id_pais_origen,
            "precio_unitario": precio_unitario
        }

        return self.insert(data)

    def existe_propuesta(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        tipo_propuesta: str
    ):
        """
        Verifica si ya existe una propuesta para:
        procedimiento_clave + proveedor + tipo_propuesta.
        """
        query = """
            SELECT EXISTS(
                SELECT 1
                FROM propuestas
                WHERE id_procedimiento_clave = %s
                  AND id_proveedor = %s
                  AND tipo_propuesta = %s
            ) AS existe;
        """

        result = self.custom_query(
            query,
            params=(
                id_procedimiento_clave,
                id_proveedor,
                tipo_propuesta
            ),
            fetch=True
        )

        return result[0]["existe"] if result else False