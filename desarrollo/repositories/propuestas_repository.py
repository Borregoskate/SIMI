"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

propuestas_repository.py

Repositorio para la tabla simi.propuestas.

Responsabilidades:

- Consultar propuestas económicas.
- Detectar propuestas iniciales existentes.
- Crear propuestas iniciales.
- Consultar propuestas por procedimiento, proveedor o clave.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza normalización, validación ni cálculos económicos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class PropuestasRepository(BaseRepository):
    """
    Repositorio especializado para propuestas económicas.
    """

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"

    def __init__(self):
        super().__init__(
            table_name="propuestas",
            primary_key="id_propuesta",
        )

    # ==========================================================
    # CONSULTAS DE EXISTENCIA
    # ==========================================================

    def existe_propuesta_inicial(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        conn=None,
    ):
        """
        Busca una propuesta inicial para una combinación de
        procedimiento-clave y proveedor.

        Devuelve el registro encontrado o None.
        """

        query = """
            SELECT
                id_propuesta,
                id_procedimiento_clave,
                id_proveedor,
                tipo_propuesta
            FROM simi.propuestas
            WHERE id_procedimiento_clave = %s
              AND id_proveedor = %s
              AND tipo_propuesta = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento_clave,
                id_proveedor,
                self.TIPO_INICIAL,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_procedimiento_clave(
        self,
        id_procedimiento_clave: int,
        conn=None,
    ):
        """
        Devuelve todas las propuestas registradas para una clave
        perteneciente a un procedimiento.
        """

        query = """
            SELECT *
            FROM simi.propuestas
            WHERE id_procedimiento_clave = %s
            ORDER BY
                tipo_propuesta,
                precio_unitario,
                id_propuesta;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento_clave,),
            conn=conn,
            fetchall=True,
        )

    def get_by_proveedor(
        self,
        id_proveedor: int,
        conn=None,
    ):
        """
        Devuelve todas las propuestas registradas por un proveedor.
        """

        query = """
            SELECT *
            FROM simi.propuestas
            WHERE id_proveedor = %s
            ORDER BY
                fecha_registro DESC,
                id_propuesta DESC;
        """

        return self.custom_query(
            query=query,
            params=(id_proveedor,),
            conn=conn,
            fetchall=True,
        )

    def get_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve las propuestas asociadas a un procedimiento,
        junto con los datos de la clave y del proveedor.
        """

        query = """
            SELECT
                p.id_propuesta,
                p.id_procedimiento_clave,
                p.id_proveedor,
                p.tipo_propuesta,
                p.cantidad_ofertada,
                p.pais_origen,
                p.precio_unitario,
                p.fecha_registro,
                pc.id_procedimiento,
                pc.id_clave,
                c.clave,
                c.descripcion,
                pr.rfc,
                pr.razon_social
            FROM simi.propuestas AS p
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento_clave =
                   p.id_procedimiento_clave
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            INNER JOIN simi.proveedores AS pr
                ON pr.id_proveedor = p.id_proveedor
            WHERE pc.id_procedimiento = %s
            ORDER BY
                c.clave,
                pr.razon_social,
                p.tipo_propuesta,
                p.id_propuesta;
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

    def crear_propuesta_inicial(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        cantidad_ofertada,
        pais_origen: str,
        precio_unitario,
        conn=None,
    ):
        """
        Crea una propuesta de tipo INICIAL.

        Todos los datos deben llegar normalizados, validados y
        verificados desde la capa Service.
        """

        data = {
            "id_procedimiento_clave": id_procedimiento_clave,
            "id_proveedor": id_proveedor,
            "tipo_propuesta": self.TIPO_INICIAL,
            "cantidad_ofertada": cantidad_ofertada,
            "pais_origen": pais_origen,
            "precio_unitario": precio_unitario,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    def crear_propuesta_subasta(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        cantidad_ofertada,
        pais_origen: str,
        precio_unitario,
        conn=None,
    ):
        """
        Crea una propuesta de tipo SUBASTA.

        Este método únicamente persiste la información.
        La validación de evaluación técnica previa y las reglas
        de participación pertenecen al Service de subasta.
        """

        data = {
            "id_procedimiento_clave": id_procedimiento_clave,
            "id_proveedor": id_proveedor,
            "tipo_propuesta": self.TIPO_SUBASTA,
            "cantidad_ofertada": cantidad_ofertada,
            "pais_origen": pais_origen,
            "precio_unitario": precio_unitario,
        }

        return self.insert(
            data=data,
            conn=conn,
        )