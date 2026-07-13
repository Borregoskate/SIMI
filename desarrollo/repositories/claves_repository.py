"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

claves_repository.py

Repositorio para la tabla simi.claves.

Responsabilidades:

- Consultar claves del catálogo.
- Crear claves.
- Actualizar la descripción de una clave.
- Consultar la relación entre una clave y un procedimiento.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza normalización ni aplica reglas de negocio.

Autor: Jorge Saavedra
Versión: 1.3.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ClavesRepository(BaseRepository):
    """
    Repositorio especializado para el catálogo de claves.
    """

    def __init__(self):
        super().__init__(
            table_name="claves",
            primary_key="id_clave",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_clave(
        self,
        clave: str,
        conn=None,
    ):
        """
        Busca una clave mediante su valor textual.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.claves
            WHERE clave = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(clave,),
            conn=conn,
            fetchone=True,
        )

    def buscar(
        self,
        texto: str,
        conn=None,
    ):
        """
        Busca coincidencias en la clave o en su descripción.

        El texto debe llegar preparado desde la capa Service.
        Esta búsqueda no modifica ni normaliza el valor recibido.
        """

        parametro = f"%{texto}%"

        query = """
            SELECT *
            FROM simi.claves
            WHERE clave ILIKE %s
               OR descripcion ILIKE %s
            ORDER BY
                clave,
                id_clave;
        """

        return self.custom_query(
            query=query,
            params=(
                parametro,
                parametro,
            ),
            conn=conn,
            fetchall=True,
        )

    def obtener_por_categoria(
        self,
        id_categoria: int,
        conn=None,
    ):
        """
        Devuelve todas las claves asociadas a una categoría.
        """

        query = """
            SELECT *
            FROM simi.claves
            WHERE id_categoria = %s
            ORDER BY
                clave,
                id_clave;
        """

        return self.custom_query(
            query=query,
            params=(id_categoria,),
            conn=conn,
            fetchall=True,
        )

    def get_procedimiento_clave(
        self,
        id_procedimiento: int,
        clave: str,
        conn=None,
    ):
        """
        Obtiene la relación procedimiento_claves a partir del
        procedimiento y del valor textual de la clave.

        Se utiliza en la Carga 2 para comprobar que una clave
        ofertada pertenece al universo del procedimiento.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT
                pc.id_procedimiento_clave,
                pc.id_procedimiento,
                pc.id_clave,
                pc.cantidad_requerida,
                c.clave,
                c.descripcion
            FROM simi.procedimiento_claves AS pc
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            WHERE pc.id_procedimiento = %s
              AND c.clave = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                clave,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # EXISTENCIA
    # ==========================================================

    def existe_clave(
        self,
        clave: str,
        conn=None,
    ) -> bool:
        """
        Indica si una clave ya existe en el catálogo.
        """

        return self.exists_by_field(
            field_name="clave",
            value=clave,
            conn=conn,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_clave(
        self,
        clave: str,
        descripcion: str,
        id_categoria: int | None = None,
        conn=None,
    ):
        """
        Crea una clave en el catálogo.

        Los valores deben llegar normalizados, validados y
        verificados desde la capa Service.
        """

        data = {
            "clave": clave,
            "descripcion": descripcion,
            "id_categoria": id_categoria,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_descripcion(
        self,
        id_clave: int,
        descripcion: str,
        conn=None,
    ):
        """
        Actualiza la descripción de una clave.
        """

        return self.update(
            record_id=id_clave,
            data={
                "descripcion": descripcion,
            },
            conn=conn,
        )