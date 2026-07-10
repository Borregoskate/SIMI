"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

proveedores_repository.py

Repositorio para la tabla proveedores.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProveedoresRepository(BaseRepository):
    """
    Repositorio para el catálogo de proveedores.
    """

    def __init__(self):
        super().__init__(
            table_name="proveedores",
            primary_key="id_proveedor"
        )

    def get_by_rfc(self, rfc: str, conn=None):
        query = """
            SELECT *
            FROM simi.proveedores
            WHERE rfc = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(rfc,),
            conn=conn,
            fetch=True
        )

        return result[0] if result else None

    def get_by_razon_social(self, razon_social: str, conn=None):
        query = """
            SELECT *
            FROM simi.proveedores
            WHERE UPPER(razon_social) = UPPER(%s)
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(razon_social,),
            conn=conn,
            fetch=True
        )

        return result[0] if result else None

    def buscar(self, texto: str, conn=None):
        query = """
            SELECT *
            FROM simi.proveedores
            WHERE
                rfc ILIKE %s
                OR razon_social ILIKE %s
            ORDER BY razon_social;
        """

        parametro = f"%{texto}%"

        return self.custom_query(
            query,
            params=(parametro, parametro),
            conn=conn,
            fetch=True
        )

    def crear_proveedor(self, rfc: str, razon_social: str, conn=None):
        data = {
            "rfc": rfc,
            "razon_social": razon_social
        }

        return self.insert(data, conn=conn)

    def actualizar_razon_social(self, id_proveedor: int, razon_social: str, conn=None):
        return self.update(
            record_id=id_proveedor,
            data={"razon_social": razon_social},
            conn=conn
        )

    def existe_rfc(self, rfc: str, conn=None):
        return self.exists_by_field(
            "rfc",
            rfc,
            conn=conn
        )

    def existe_razon_social(self, razon_social: str, conn=None):
        query = """
            SELECT EXISTS(
                SELECT 1
                FROM simi.proveedores
                WHERE UPPER(razon_social) = UPPER(%s)
            ) AS existe;
        """

        result = self.custom_query(
            query,
            params=(razon_social,),
            conn=conn,
            fetch=True
        )

        return result[0]["existe"] if result else False