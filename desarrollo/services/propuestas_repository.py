"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

propuestas_repository.py

Repositorio para la tabla simi.propuestas.

Responsabilidades:
- Consultar propuestas económicas.
- Detectar propuestas iniciales y de subasta existentes.
- Crear propuestas iniciales.
- Crear propuestas de subasta.
- Consultar propuestas por procedimiento, proveedor o clave.
- Delegar toda ejecución SQL a BaseRepository.

Las propuestas iniciales y las propuestas de subasta se almacenan
en la misma tabla. Se distinguen mediante el campo tipo_propuesta:

- INICIAL
- SUBASTA

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza:
- Normalización.
- Validaciones de negocio.
- Verificación de evaluación técnica.
- Cálculos económicos.
- Apertura o cierre de conexiones.
- Commit o rollback.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class PropuestasRepository(BaseRepository):
    """
    Repositorio especializado para propuestas económicas.
    """

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"

    TIPOS_VALIDOS = {
        TIPO_INICIAL,
        TIPO_SUBASTA,
    }

    def __init__(self):
        super().__init__(
            table_name="propuestas",
            primary_key="id_propuesta",
        )

    # ==========================================================
    # CONSULTAS DE EXISTENCIA
    # ==========================================================

    def get_by_combinacion(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        tipo_propuesta: str,
        conn=None,
    ):
        """
        Busca una propuesta mediante la combinación lógica:

        procedimiento-clave + proveedor + tipo de propuesta.

        Devuelve el registro encontrado o None.
        """

        query = """
            SELECT
                id_propuesta,
                id_procedimiento_clave,
                id_proveedor,
                tipo_propuesta,
                cantidad_ofertada,
                pais_origen,
                precio_unitario,
                fecha_registro
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
                tipo_propuesta,
            ),
            conn=conn,
            fetchone=True,
        )

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

        return self.get_by_combinacion(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            tipo_propuesta=self.TIPO_INICIAL,
            conn=conn,
        )

    def existe_propuesta_subasta(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        conn=None,
    ):
        """
        Busca una propuesta de subasta para una combinación de
        procedimiento-clave y proveedor.

        Devuelve el registro encontrado o None.
        """

        return self.get_by_combinacion(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            tipo_propuesta=self.TIPO_SUBASTA,
            conn=conn,
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
            SELECT
                id_propuesta,
                id_procedimiento_clave,
                id_proveedor,
                tipo_propuesta,
                cantidad_ofertada,
                pais_origen,
                precio_unitario,
                fecha_registro
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
            SELECT
                id_propuesta,
                id_procedimiento_clave,
                id_proveedor,
                tipo_propuesta,
                cantidad_ofertada,
                pais_origen,
                precio_unitario,
                fecha_registro
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
        incluyendo los datos de la clave y del proveedor.
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
                p.precio_unitario,
                p.id_propuesta;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    def get_by_procedimiento_y_tipo(
        self,
        id_procedimiento: int,
        tipo_propuesta: str,
        conn=None,
    ):
        """
        Devuelve las propuestas de un procedimiento filtradas
        por tipo INICIAL o SUBASTA.
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
              AND p.tipo_propuesta = %s

            ORDER BY
                c.clave,
                p.precio_unitario,
                pr.razon_social,
                p.id_propuesta;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                tipo_propuesta,
            ),
            conn=conn,
            fetchall=True,
        )

    def get_iniciales_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve únicamente las propuestas iniciales
        de un procedimiento.
        """

        return self.get_by_procedimiento_y_tipo(
            id_procedimiento=id_procedimiento,
            tipo_propuesta=self.TIPO_INICIAL,
            conn=conn,
        )

    def get_subastas_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve únicamente las propuestas de subasta
        de un procedimiento.
        """

        return self.get_by_procedimiento_y_tipo(
            id_procedimiento=id_procedimiento,
            tipo_propuesta=self.TIPO_SUBASTA,
            conn=conn,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_propuesta(
        self,
        id_procedimiento_clave: int,
        id_proveedor: int,
        tipo_propuesta: str,
        cantidad_ofertada,
        pais_origen: str,
        precio_unitario,
        conn=None,
    ):
        """
        Crea una propuesta económica.

        Todos los datos deben llegar normalizados, validados
        y verificados desde la capa Service.
        """

        data = {
            "id_procedimiento_clave": id_procedimiento_clave,
            "id_proveedor": id_proveedor,
            "tipo_propuesta": tipo_propuesta,
            "cantidad_ofertada": cantidad_ofertada,
            "pais_origen": pais_origen,
            "precio_unitario": precio_unitario,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

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
        """

        return self.crear_propuesta(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            tipo_propuesta=self.TIPO_INICIAL,
            cantidad_ofertada=cantidad_ofertada,
            pais_origen=pais_origen,
            precio_unitario=precio_unitario,
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

        La validación de evaluación técnica previa y las reglas
        de participación pertenecen al Service de subasta.
        """

        return self.crear_propuesta(
            id_procedimiento_clave=id_procedimiento_clave,
            id_proveedor=id_proveedor,
            tipo_propuesta=self.TIPO_SUBASTA,
            cantidad_ofertada=cantidad_ofertada,
            pais_origen=pais_origen,
            precio_unitario=precio_unitario,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_propuesta_subasta(
        self,
        id_propuesta: int,
        cantidad_ofertada,
        pais_origen: str,
        precio_unitario,
        conn=None,
    ):
        """
        Actualiza una propuesta de subasta existente.

        La decisión de actualizar o crear una nueva propuesta
        pertenece exclusivamente a la capa Service.
        """

        data = {
            "cantidad_ofertada": cantidad_ofertada,
            "pais_origen": pais_origen,
            "precio_unitario": precio_unitario,
        }

        return self.update(
            record_id=id_propuesta,
            data=data,
            conn=conn,
        )