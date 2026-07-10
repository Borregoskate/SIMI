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
    Repositorio para propuestas económicas.
    """

    def __init__(self):
        super().__init__(
            table_name="propuestas",
            primary_key="id_propuesta"
        )

    def existe_propuesta_inicial(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        conn=None
    ):
        query = """
            SELECT id_propuesta
            FROM simi.propuestas
            WHERE id_procedimiento_clave = %s
              AND id_proveedor = %s
              AND tipo_propuesta = 'INICIAL'
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(id_procedimiento_clave, id_proveedor),
            conn=conn,
            fetch=True
        )

        return result[0] if result else None

    def crear_propuesta_inicial(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        cantidad_ofertada,
        pais_origen: str,
        precio_unitario,
        conn=None
    ):
        data = {
            "id_procedimiento_clave": id_procedimiento_clave,
            "id_proveedor": id_proveedor,
            "tipo_propuesta": "INICIAL",
            "cantidad_ofertada": cantidad_ofertada,
            "pais_origen": pais_origen,
            "precio_unitario": precio_unitario
        }

        return self.insert(data, conn=conn)