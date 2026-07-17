"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

comparador_im_repository.py

Repositorio de solo lectura para comparar un procedimiento
existente contra el mercado operativo e histórico acumulado.

Regla principal:
- El procedimiento seleccionado se analiza con sus propias etapas.
- La referencia de mercado excluye ese mismo procedimiento.
- El histórico se incorpora por id_clave.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ComparadorIMRepository(BaseRepository):
    """Repository del Comparador Inteligente por Procedimiento."""

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"
    RESULTADO_POSITIVA = "POSITIVA"

    ORIGEN_PROCEDIMIENTO = "PROCEDIMIENTO"
    ORIGEN_OPERATIVO = "OPERATIVO"
    ORIGEN_HISTORICO = "HISTORICO"

    def __init__(self):
        super().__init__(
            table_name="procedimientos",
            primary_key="id_procedimiento",
        )

    @staticmethod
    def _preparar_lista(valores):
        if valores is None:
            return []

        resultado = []
        vistos = set()

        for valor in valores:
            if valor is None or valor in vistos:
                continue

            vistos.add(valor)
            resultado.append(valor)

        return resultado

    # ==========================================================
    # PROCEDIMIENTOS DISPONIBLES
    # ==========================================================

    def obtener_procedimientos_disponibles(self, conn=None):
        """
        Devuelve procedimientos que tienen al menos una clave
        registrada en su universo.
        """
        query = """
            SELECT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.descripcion,
                pr.ejercicio,
                pr.activo,
                COUNT(DISTINCT pc.id_clave) AS total_claves
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            GROUP BY
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.descripcion,
                pr.ejercicio,
                pr.activo
            ORDER BY
                pr.ejercicio DESC NULLS LAST,
                pr.numero_procedimiento,
                pr.id_procedimiento DESC;
        """

        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    def obtener_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        query = """
            SELECT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.descripcion,
                pr.ejercicio,
                pr.fecha_creacion,
                pr.activo
            FROM simi.procedimientos AS pr
            WHERE pr.id_procedimiento = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # UNIVERSO DEL PROCEDIMIENTO
    # ==========================================================

    def obtener_universo_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        query = """
            SELECT
                pc.id_procedimiento_clave,
                pc.id_procedimiento,
                pc.id_clave,
                c.clave,
                c.descripcion,
                c.id_categoria,
                cc.nombre_categoria AS categoria,
                pc.cantidad_requerida
            FROM simi.procedimiento_claves AS pc
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            LEFT JOIN simi.cat_categorias_clave AS cc
                ON cc.id_categoria = c.id_categoria
            WHERE pc.id_procedimiento = %s
            ORDER BY
                c.clave,
                c.id_clave;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # ETAPAS DEL PROCEDIMIENTO SELECCIONADO
    # ==========================================================

    def obtener_propuestas_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        query = """
            SELECT
                p.id_propuesta,
                pc.id_procedimiento_clave,
                pc.id_procedimiento,
                pc.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                p.id_proveedor,
                pv.rfc,
                pv.razon_social,
                p.tipo_propuesta,
                et.resultado AS resultado_tecnico,
                p.cantidad_ofertada,
                p.pais_origen,
                p.precio_unitario,
                p.fecha_registro,
                %s::TEXT AS origen_dato
            FROM simi.propuestas AS p
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento_clave =
                   p.id_procedimiento_clave
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = p.id_proveedor
            LEFT JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pc.id_procedimiento
                AND et.id_clave = pc.id_clave
                AND et.id_proveedor = p.id_proveedor
            WHERE pc.id_procedimiento = %s
              AND p.tipo_propuesta = ANY(%s)
            ORDER BY
                pc.id_clave,
                p.tipo_propuesta,
                pv.razon_social,
                pv.rfc,
                p.id_propuesta;
        """

        return self.custom_query(
            query=query,
            params=(
                self.ORIGEN_PROCEDIMIENTO,
                id_procedimiento,
                [self.TIPO_INICIAL, self.TIPO_SUBASTA],
            ),
            conn=conn,
            fetchall=True,
        )

    def obtener_adjudicaciones_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                a.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                a.id_proveedor,
                pv.rfc,
                pv.razon_social,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,
                %s::TEXT AS origen_dato
            FROM simi.adjudicaciones AS a
            INNER JOIN simi.procedimientos AS pr
                ON pr.id_procedimiento = a.id_procedimiento
            INNER JOIN simi.claves AS c
                ON c.id_clave = a.id_clave
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = a.id_proveedor
            WHERE a.id_procedimiento = %s
            ORDER BY
                a.id_clave,
                pv.razon_social,
                pv.rfc,
                a.id_adjudicacion;
        """

        return self.custom_query(
            query=query,
            params=(
                self.ORIGEN_PROCEDIMIENTO,
                id_procedimiento,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # MERCADO OPERATIVO EXTERNO
    # ==========================================================

    def obtener_mercado_operativo(
        self,
        ids_clave,
        excluir_id_procedimiento,
        conn=None,
    ):
        """
        Recupera adjudicaciones de otros procedimientos para las
        claves del universo seleccionado.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                a.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                a.id_proveedor,
                pv.rfc,
                pv.razon_social,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,
                %s::TEXT AS origen_dato
            FROM simi.adjudicaciones AS a
            INNER JOIN simi.procedimientos AS pr
                ON pr.id_procedimiento = a.id_procedimiento
            INNER JOIN simi.claves AS c
                ON c.id_clave = a.id_clave
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = a.id_proveedor
            WHERE a.id_clave = ANY(%s)
              AND a.id_procedimiento <> %s
            ORDER BY
                a.id_clave,
                pr.ejercicio NULLS LAST,
                pr.numero_procedimiento,
                a.id_procedimiento,
                pv.razon_social,
                pv.rfc,
                a.id_adjudicacion;
        """

        return self.custom_query(
            query=query,
            params=(
                self.ORIGEN_OPERATIVO,
                ids_clave,
                excluir_id_procedimiento,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # MERCADO HISTÓRICO
    # ==========================================================

    def obtener_mercado_historico(
        self,
        ids_clave,
        conn=None,
    ):
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

        query = """
            SELECT
                ah.id_adjudicacion_historica,
                NULL::BIGINT AS id_procedimiento,
                ah.numero_procedimiento,
                CASE
                    WHEN SUBSTRING(
                        ah.numero_procedimiento
                        FROM '(20[0-9]{2})'
                    ) IS NOT NULL
                    THEN SUBSTRING(
                        ah.numero_procedimiento
                        FROM '(20[0-9]{2})'
                    )::INTEGER
                    ELSE NULL
                END AS ejercicio,
                ah.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                ah.id_proveedor,
                pv.rfc,
                pv.razon_social,
                ah.cantidad_adjudicada,
                ah.porcentaje_adjudicado,
                ah.precio_unitario_adjudicado,
                %s::TEXT AS origen_dato
            FROM simi.adjudicaciones_historicas AS ah
            INNER JOIN simi.claves AS c
                ON c.id_clave = ah.id_clave
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = ah.id_proveedor
            WHERE ah.id_clave = ANY(%s)
            ORDER BY
                ah.id_clave,
                ejercicio NULLS LAST,
                ah.numero_procedimiento,
                pv.razon_social,
                pv.rfc,
                ah.id_adjudicacion_historica;
        """

        return self.custom_query(
            query=query,
            params=(
                self.ORIGEN_HISTORICO,
                ids_clave,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # CONTEXTO COMPLETO
    # ==========================================================

    def obtener_contexto_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        """
        Devuelve el procedimiento, su universo, sus etapas y el
        mercado externo operativo e histórico de las mismas claves.
        """
        procedimiento = self.obtener_procedimiento(
            id_procedimiento=id_procedimiento,
            conn=conn,
        )

        if procedimiento is None:
            return None

        universo = self.obtener_universo_procedimiento(
            id_procedimiento=id_procedimiento,
            conn=conn,
        )

        ids_clave = self._preparar_lista(
            registro.get("id_clave")
            for registro in universo
        )

        return {
            "procedimiento": procedimiento,
            "universo": universo,
            "propuestas_procedimiento": (
                self.obtener_propuestas_procedimiento(
                    id_procedimiento=id_procedimiento,
                    conn=conn,
                )
            ),
            "adjudicaciones_procedimiento": (
                self.obtener_adjudicaciones_procedimiento(
                    id_procedimiento=id_procedimiento,
                    conn=conn,
                )
            ),
            "mercado_operativo": self.obtener_mercado_operativo(
                ids_clave=ids_clave,
                excluir_id_procedimiento=id_procedimiento,
                conn=conn,
            ),
            "mercado_historico": self.obtener_mercado_historico(
                ids_clave=ids_clave,
                conn=conn,
            ),
        }