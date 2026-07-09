"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

claves_repository.py

Repositorio para la tabla claves.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ClavesRepository(BaseRepository):

    def __init__(self):
        super().__init__(
            table_name="claves",
            primary_key="id_clave"
        )

    def get_by_clave(self, clave: str, conn=None):
        query = """
            SELECT *
            FROM simi.claves
            WHERE clave = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(clave,),
            conn=conn,
            fetch=True
        )

        return result[0] if result else None

    def buscar(self, texto: str, conn=None):
        query = """
            SELECT *
            FROM simi.claves
            WHERE
                clave ILIKE %s
                OR descripcion ILIKE %s
            ORDER BY clave;
        """

        parametro = f"%{texto}%"

        return self.custom_query(
            query,
            params=(parametro, parametro),
            conn=conn,
            fetch=True
        )

    def crear_clave(
        self,
        clave: str,
        descripcion: str,
        id_categoria: int = None,
        conn=None
    ):
        data = {
            "clave": clave,
            "descripcion": descripcion,
            "id_categoria": id_categoria
        }

        return self.insert(data, conn=conn)

    def actualizar_descripcion(
        self,
        id_clave: int,
        descripcion: str,
        conn=None
    ):
        return self.update(
            record_id=id_clave,
            data={"descripcion": descripcion},
            conn=conn
        )

    def obtener_por_categoria(self, id_categoria: int, conn=None):
        query = """
            SELECT *
            FROM simi.claves
            WHERE id_categoria = %s
            ORDER BY clave;
        """

        return self.custom_query(
            query,
            params=(id_categoria,),
            conn=conn,
            fetch=True
        )

    def existe_clave(self, clave: str, conn=None):
        return self.exists_by_field(
            "clave",
            clave,
            conn=conn
        )