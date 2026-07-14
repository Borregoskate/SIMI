"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

adjudicaciones_repository.py

Repositorio para la tabla simi.adjudicaciones.

Responsabilidades:
- Consultar adjudicaciones.
- Detectar adjudicaciones existentes.
- Crear adjudicaciones.
- Actualizar adjudicaciones existentes.
- Consultar adjudicaciones por procedimiento, clave o proveedor.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza:
- Normalización.
- Validaciones de negocio.
- Cálculos de porcentajes.
- Verificación de propuestas o evaluaciones técnicas.
- Apertura o cierre de conexiones.
- Commit o rollback.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class AdjudicacionesRepository(BaseRepository):
    """
    Repositorio especializado para adjudicaciones actuales.
    """

    def __init__(self):
        super().__init__(
            table_name="adjudicaciones",
            primary_key="id_adjudicacion",
        )

    # ==========================================================
    # CONSULTAS DE EXISTENCIA
    # ==========================================================

    def get_by_combinacion(
        self,
        id_procedimiento: int,
        id_clave: int,
        id_proveedor: int,
        conn=None,
    ):
        """
        Busca una adjudicación mediante la combinación:

        procedimiento + clave + proveedor.

        Devuelve el registro encontrado o None.

        Una clave puede adjudicarse parcialmente a varios proveedores,
        pero cada proveedor debe tener una sola adjudicación para la
        misma clave dentro del mismo procedimiento.
        """

        query = """
            SELECT
                id_adjudicacion,
                id_procedimiento,
                id_clave,
                id_proveedor,
                cantidad_adjudicada,
                porcentaje_adjudicado,
                precio_unitario_adjudicado
            FROM simi.adjudicaciones
            WHERE id_procedimiento = %s
              AND id_clave = %s
              AND id_proveedor = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_clave,
                id_proveedor,
            ),
            conn=conn,
            fetchone=True,
        )

    def existe_adjudicacion(
        self,
        id_procedimiento: int,
        id_clave: int,
        id_proveedor: int,
        conn=None,
    ):
        """
        Alias descriptivo para consultar si ya existe
        una adjudicación.

        Devuelve el registro encontrado o None.
        """

        return self.get_by_combinacion(
            id_procedimiento=id_procedimiento,
            id_clave=id_clave,
            id_proveedor=id_proveedor,
            conn=conn,
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve las adjudicaciones de un procedimiento,
        incluyendo información de claves y proveedores.
        """

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                a.id_clave,
                a.id_proveedor,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,

                c.clave,
                c.descripcion,

                p.rfc,
                p.razon_social

            FROM simi.adjudicaciones AS a

            INNER JOIN simi.claves AS c
                ON c.id_clave = a.id_clave

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = a.id_proveedor

            WHERE a.id_procedimiento = %s

            ORDER BY
                c.clave,
                a.porcentaje_adjudicado DESC,
                a.precio_unitario_adjudicado,
                p.razon_social,
                a.id_adjudicacion;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    def get_by_clave(
        self,
        id_clave: int,
        conn=None,
    ):
        """
        Devuelve todas las adjudicaciones registradas para una clave.
        """

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                a.id_clave,
                a.id_proveedor,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,

                p.rfc,
                p.razon_social

            FROM simi.adjudicaciones AS a

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = a.id_proveedor

            WHERE a.id_clave = %s

            ORDER BY
                a.id_procedimiento DESC,
                a.precio_unitario_adjudicado,
                a.porcentaje_adjudicado DESC,
                p.razon_social;
        """

        return self.custom_query(
            query=query,
            params=(id_clave,),
            conn=conn,
            fetchall=True,
        )

    def get_by_proveedor(
        self,
        id_proveedor: int,
        conn=None,
    ):
        """
        Devuelve todas las adjudicaciones de un proveedor.
        """

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                a.id_clave,
                a.id_proveedor,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,

                c.clave,
                c.descripcion

            FROM simi.adjudicaciones AS a

            INNER JOIN simi.claves AS c
                ON c.id_clave = a.id_clave

            WHERE a.id_proveedor = %s

            ORDER BY
                a.id_procedimiento DESC,
                c.clave,
                a.id_adjudicacion;
        """

        return self.custom_query(
            query=query,
            params=(id_proveedor,),
            conn=conn,
            fetchall=True,
        )

    def get_by_procedimiento_y_clave(
        self,
        id_procedimiento: int,
        id_clave: int,
        conn=None,
    ):
        """
        Devuelve todos los proveedores adjudicados para una clave
        dentro de un procedimiento.

        Esta consulta contempla adjudicaciones parciales.
        """

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                a.id_clave,
                a.id_proveedor,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,

                p.rfc,
                p.razon_social

            FROM simi.adjudicaciones AS a

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = a.id_proveedor

            WHERE a.id_procedimiento = %s
              AND a.id_clave = %s

            ORDER BY
                a.porcentaje_adjudicado DESC,
                a.precio_unitario_adjudicado,
                p.razon_social,
                a.id_adjudicacion;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_clave,
            ),
            conn=conn,
            fetchall=True,
        )

    def contar_proveedores_adjudicados(
        self,
        id_procedimiento: int,
        id_clave: int,
        conn=None,
    ):
        """
        Cuenta los proveedores adjudicados para una clave
        dentro de un procedimiento.

        La regla que limita la adjudicación a un máximo autorizado
        de proveedores pertenece a la capa Service.
        """

        query = """
            SELECT COUNT(*) AS total
            FROM simi.adjudicaciones
            WHERE id_procedimiento = %s
              AND id_clave = %s;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_clave,
            ),
            conn=conn,
            fetchone=True,
        )

    def sumar_porcentaje_adjudicado(
        self,
        id_procedimiento: int,
        id_clave: int,
        conn=None,
    ):
        """
        Devuelve la suma del porcentaje adjudicado para una clave.

        El Repository únicamente consulta el valor.
        La validación de que el porcentaje no exceda el límite
        permitido pertenece a la capa Service.
        """

        query = """
            SELECT
                COALESCE(
                    SUM(porcentaje_adjudicado),
                    0
                ) AS porcentaje_total
            FROM simi.adjudicaciones
            WHERE id_procedimiento = %s
              AND id_clave = %s;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_clave,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_adjudicacion(
        self,
        id_procedimiento: int,
        id_clave: int,
        id_proveedor: int,
        cantidad_adjudicada,
        porcentaje_adjudicado,
        precio_unitario_adjudicado,
        conn=None,
    ):
        """
        Crea una adjudicación.

        Los datos deben llegar previamente normalizados,
        validados y verificados desde la capa Service.
        """

        data = {
            "id_procedimiento": id_procedimiento,
            "id_clave": id_clave,
            "id_proveedor": id_proveedor,
            "cantidad_adjudicada": cantidad_adjudicada,
            "porcentaje_adjudicado": porcentaje_adjudicado,
            "precio_unitario_adjudicado": (
                precio_unitario_adjudicado
            ),
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_adjudicacion(
        self,
        id_adjudicacion: int,
        cantidad_adjudicada,
        porcentaje_adjudicado,
        precio_unitario_adjudicado,
        conn=None,
    ):
        """
        Actualiza una adjudicación existente.

        La decisión de permitir una actualización pertenece
        exclusivamente a la capa Service.
        """

        data = {
            "cantidad_adjudicada": cantidad_adjudicada,
            "porcentaje_adjudicado": porcentaje_adjudicado,
            "precio_unitario_adjudicado": (
                precio_unitario_adjudicado
            ),
        }

        return self.update(
            record_id=id_adjudicacion,
            data=data,
            conn=conn,
        )