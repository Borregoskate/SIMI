"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

claves_repository.py

Repositorio para la tabla claves.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ClavesRepository(BaseRepository):
    """
    Repositorio para el catálogo de claves.
    """

    def __init__(self):
        super().__init__(
            table_name="claves",
            primary_key="id_clave"
        )

    def get_by_clave(self, clave: str):
        """
        Obtiene una clave por su código.
        """
        query = """
            SELECT *
            FROM claves
            WHERE clave = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(clave,),
            fetch=True
        )

        if result:
            return result[0]

        return None

    def buscar(self, texto: str):
        """
        Busca claves por código o descripción.
        """
        query = """
            SELECT *
            FROM claves
            WHERE
                clave ILIKE %s
                OR descripcion ILIKE %s
            ORDER BY clave;
        """

        parametro = f"%{texto}%"

        return self.custom_query(
            query,
            params=(parametro, parametro),
            fetch=True
        )

    def crear_clave(
        self,
        clave: str,
        descripcion: str,
        id_categoria: int = None
    ):
        """
        Agrega una nueva clave al catálogo.
        """
        data = {
            "clave": clave,
            "descripcion": descripcion,
            "id_categoria": id_categoria
        }

        return self.insert(data)

    def actualizar_descripcion(
        self,
        id_clave: int,
        descripcion: str
    ):
        """
        Actualiza únicamente la descripción.
        """
        return self.update(
            record_id=id_clave,
            data={
                "descripcion": descripcion
            }
        )

    def obtener_por_categoria(
        self,
        id_categoria: int
    ):
        """
        Obtiene todas las claves de una categoría.
        """
        query = """
            SELECT *
            FROM claves
            WHERE id_categoria = %s
            ORDER BY clave;
        """

        return self.custom_query(
            query,
            params=(id_categoria,),
            fetch=True
        )

    def existe_clave(self, clave: str):
        """
        Verifica si una clave ya existe.
        """
        return self.exists_by_field(
            "clave",
            clave
        )