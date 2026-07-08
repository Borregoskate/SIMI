"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

proveedores_repository.py

Repositorio para la tabla proveedores.

Autor: Jorge Saavedra
Versión: 1.0.0
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

    def get_by_rfc(self, rfc: str):
        """
        Obtiene un proveedor por RFC.
        """
        query = """
            SELECT *
            FROM proveedores
            WHERE rfc = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(rfc,),
            fetch=True
        )

        if result:
            return result[0]

        return None

    def get_by_razon_social(self, razon_social: str):
        """
        Obtiene un proveedor por razón social.
        """
        query = """
            SELECT *
            FROM proveedores
            WHERE UPPER(razon_social) = UPPER(%s)
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(razon_social,),
            fetch=True
        )

        if result:
            return result[0]

        return None

    def buscar(self, texto: str):
        """
        Busca proveedores por RFC o razón social.
        """
        query = """
            SELECT *
            FROM proveedores
            WHERE
                rfc ILIKE %s
                OR razon_social ILIKE %s
            ORDER BY razon_social;
        """

        parametro = f"%{texto}%"

        return self.custom_query(
            query,
            params=(parametro, parametro),
            fetch=True
        )

    def crear_proveedor(
        self,
        rfc: str,
        razon_social: str
    ):
        """
        Inserta un nuevo proveedor.
        """
        data = {
            "rfc": rfc,
            "razon_social": razon_social
        }

        return self.insert(data)

    def actualizar_razon_social(
        self,
        id_proveedor: int,
        razon_social: str
    ):
        """
        Actualiza la razón social del proveedor.
        """
        return self.update(
            record_id=id_proveedor,
            data={
                "razon_social": razon_social
            }
        )

    def existe_rfc(self, rfc: str):
        """
        Verifica si un RFC ya existe.
        """
        return self.exists_by_field(
            "rfc",
            rfc
        )

    def existe_razon_social(self, razon_social: str):
        """
        Verifica si una razón social ya existe.
        """
        query = """
            SELECT EXISTS(
                SELECT 1
                FROM proveedores
                WHERE UPPER(razon_social) = UPPER(%s)
            ) AS existe;
        """

        result = self.custom_query(
            query,
            params=(razon_social,),
            fetch=True
        )

        if result:
            return result[0]["existe"]

        return False