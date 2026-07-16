"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_clave_repository.py

Repositorio analítico para el módulo Análisis por Clave.

Responsabilidades:
- Recuperar las claves disponibles para filtros.
- Recuperar información general de una clave.
- Recuperar procedimientos y ejercicios relacionados.
- Recuperar indicadores base de una clave.
- Recuperar el resumen económico por procedimiento.
- Recuperar el detalle por proveedor y etapa.
- Recuperar el historial de precios.

Este Repository:
- No normaliza datos.
- No aplica reglas de negocio.
- No calcula estados analíticos.
- No calcula variaciones o porcentajes en Python.
- No prepara información para Streamlit.
- No abre ni cierra conexiones.
- No administra commit ni rollback.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class AnalisisClaveRepository(BaseRepository):
    """Repositorio especializado para consultas de Análisis por Clave."""

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"

    RESULTADO_POSITIVA = "POSITIVA"
    RESULTADO_NEGATIVA = "NEGATIVA"

    def __init__(self):
        super().__init__(
            table_name="claves",
            primary_key="id_clave",
        )

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @staticmethod
    def _construir_filtros(
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        alias_clave="pc",
        alias_procedimiento="pr",
    ):
        """
        Construye filtros SQL parametrizados.

        La clave es obligatoria. El procedimiento y el ejercicio son
        filtros opcionales.

        Los alias se definen internamente y nunca proceden directamente
        de entradas del usuario.
        """
        condiciones = [
            f"{alias_clave}.id_clave = %s",
        ]
        parametros = [id_clave]

        if id_procedimiento is not None:
            condiciones.append(
                f"{alias_procedimiento}.id_procedimiento = %s"
            )
            parametros.append(id_procedimiento)

        if ejercicio is not None:
            condiciones.append(
                f"{alias_procedimiento}.ejercicio = %s"
            )
            parametros.append(ejercicio)

        return (
            "WHERE " + " AND ".join(condiciones),
            tuple(parametros),
        )

    # ==========================================================
    # CATÁLOGOS PARA FILTROS
    # ==========================================================

    def obtener_claves_filtro(self, conn=None):
        """
        Devuelve todas las claves del catálogo.

        Las claves sin categoría o sin participación en procedimientos
        también se conservan.
        """
        query = """
            SELECT
                c.id_clave,
                c.clave,
                c.descripcion,
                cc.nombre_categoria AS categoria
            FROM simi.claves AS c
            LEFT JOIN simi.cat_categorias_clave AS cc
                ON cc.id_categoria = c.id_categoria
            ORDER BY
                c.clave,
                c.id_clave;
        """

        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    def obtener_informacion_clave(self, id_clave, conn=None):
        """Devuelve la información general de una clave."""
        query = """
            SELECT
                c.id_clave,
                c.clave,
                c.descripcion,
                c.id_categoria,
                cc.nombre_categoria AS categoria
            FROM simi.claves AS c
            LEFT JOIN simi.cat_categorias_clave AS cc
                ON cc.id_categoria = c.id_categoria
            WHERE c.id_clave = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(id_clave,),
            conn=conn,
            fetchone=True,
        )

    def obtener_procedimientos_filtro(self, id_clave, conn=None):
        """
        Devuelve los procedimientos donde la clave forma parte
        del universo.
        """
        query = """
            SELECT DISTINCT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.descripcion,
                pr.ejercicio,
                pr.activo
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            WHERE pc.id_clave = %s
            ORDER BY
                pr.ejercicio DESC,
                pr.numero_procedimiento,
                pr.id_procedimiento DESC;
        """

        return self.custom_query(
            query=query,
            params=(id_clave,),
            conn=conn,
            fetchall=True,
        )

    def obtener_ejercicios_filtro(self, id_clave, conn=None):
        """
        Devuelve los ejercicios de los procedimientos donde participa
        la clave.
        """
        query = """
            SELECT DISTINCT
                pr.ejercicio
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            WHERE
                pc.id_clave = %s
                AND pr.ejercicio IS NOT NULL
            ORDER BY pr.ejercicio DESC;
        """

        return self.custom_query(
            query=query,
            params=(id_clave,),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # INDICADORES PRINCIPALES
    # ==========================================================

    def obtener_indicadores_clave(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve conteos y acumulados base de la clave.

        El porcentaje adjudicado no se suma históricamente porque
        porcentajes de procedimientos distintos no son comparables.
        """
        where_sql, params = self._construir_filtros(
            id_clave=id_clave,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_clave="pc",
            alias_procedimiento="pr",
        )

        query = f"""
            WITH universo_filtrado AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave
                FROM simi.procedimientos AS pr
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pr.id_procedimiento
                {where_sql}
            ),
            propuestas_iniciales AS (
                SELECT
                    p.id_propuesta,
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento_clave = p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s
            ),
            propuestas_subasta AS (
                SELECT
                    p.id_propuesta,
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento_clave = p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s
            ),
            evaluaciones_filtradas AS (
                SELECT
                    et.id_evaluacion,
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor,
                    et.resultado
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = et.id_procedimiento
                    AND uf.id_clave = et.id_clave
            ),
            adjudicaciones_filtradas AS (
                SELECT
                    a.id_adjudicacion,
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor,
                    a.cantidad_adjudicada
                FROM simi.adjudicaciones AS a
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = a.id_procedimiento
                    AND uf.id_clave = a.id_clave
            ),
            proveedores_participantes AS (
                SELECT
                    pi.id_procedimiento,
                    pi.id_clave,
                    pi.id_proveedor
                FROM propuestas_iniciales AS pi

                UNION

                SELECT
                    ef.id_procedimiento,
                    ef.id_clave,
                    ef.id_proveedor
                FROM evaluaciones_filtradas AS ef

                UNION

                SELECT
                    ps.id_procedimiento,
                    ps.id_clave,
                    ps.id_proveedor
                FROM propuestas_subasta AS ps

                UNION

                SELECT
                    af.id_procedimiento,
                    af.id_clave,
                    af.id_proveedor
                FROM adjudicaciones_filtradas AS af
            )
            SELECT
                (
                    SELECT COUNT(DISTINCT id_procedimiento)
                    FROM universo_filtrado
                ) AS total_procedimientos,

                (
                    SELECT COUNT(DISTINCT id_proveedor)
                    FROM proveedores_participantes
                ) AS total_proveedores_participantes,

                (
                    SELECT COUNT(*)
                    FROM propuestas_iniciales
                ) AS total_propuestas_iniciales,

                (
                    SELECT COUNT(*)
                    FROM evaluaciones_filtradas
                    WHERE resultado = %s
                ) AS total_evaluaciones_positivas,

                (
                    SELECT COUNT(*)
                    FROM evaluaciones_filtradas
                    WHERE resultado = %s
                ) AS total_evaluaciones_negativas,

                (
                    SELECT COUNT(*)
                    FROM propuestas_subasta
                ) AS total_propuestas_subasta,

                (
                    SELECT COUNT(DISTINCT id_proveedor)
                    FROM adjudicaciones_filtradas
                ) AS total_proveedores_adjudicados,

                (
                    SELECT COUNT(DISTINCT id_procedimiento)
                    FROM adjudicaciones_filtradas
                ) AS total_procedimientos_adjudicados,

                (
                    SELECT COALESCE(
                        SUM(cantidad_adjudicada),
                        0
                    )
                    FROM adjudicaciones_filtradas
                ) AS cantidad_total_adjudicada;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.TIPO_INICIAL,
                self.TIPO_SUBASTA,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # RESUMEN POR PROCEDIMIENTO
    # ==========================================================

    def obtener_resumen_procedimientos(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve el resumen analítico base de la clave por procedimiento.

        El Service calculará:
        - Precio adjudicado ponderado.
        - Variaciones.
        - Estado analítico.
        - Clasificaciones.
        """
        where_sql, params = self._construir_filtros(
            id_clave=id_clave,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_clave="pc",
            alias_procedimiento="pr",
        )

        query = f"""
            WITH universo_filtrado AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave,
                    pc.cantidad_requerida
                FROM simi.procedimientos AS pr
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pr.id_procedimiento
                {where_sql}
            ),
            propuestas_agregadas AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,

                    COUNT(
                        DISTINCT CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.id_proveedor
                        END
                    ) AS proveedores_oferta_inicial,

                    COUNT(
                        DISTINCT CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.id_propuesta
                        END
                    ) AS total_propuestas_iniciales,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_inicial,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                                AND et.resultado = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_viable,

                    COUNT(
                        DISTINCT CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.id_propuesta
                        END
                    ) AS total_subastas,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                                AND et.resultado = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_subasta

                FROM universo_filtrado AS uf
                LEFT JOIN simi.propuestas AS p
                    ON p.id_procedimiento_clave =
                        uf.id_procedimiento_clave
                LEFT JOIN simi.evaluaciones_tecnicas AS et
                    ON et.id_procedimiento = uf.id_procedimiento
                    AND et.id_clave = uf.id_clave
                    AND et.id_proveedor = p.id_proveedor
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave
            ),
            evaluaciones_agregadas AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,

                    COUNT(
                        DISTINCT CASE
                            WHEN et.resultado = %s
                            THEN et.id_evaluacion
                        END
                    ) AS evaluaciones_positivas,

                    COUNT(
                        DISTINCT CASE
                            WHEN et.resultado = %s
                            THEN et.id_evaluacion
                        END
                    ) AS evaluaciones_negativas

                FROM universo_filtrado AS uf
                LEFT JOIN simi.evaluaciones_tecnicas AS et
                    ON et.id_procedimiento = uf.id_procedimiento
                    AND et.id_clave = uf.id_clave
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave
            ),
            adjudicaciones_agregadas AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,

                    COUNT(
                        DISTINCT a.id_proveedor
                    ) AS proveedores_adjudicados,

                    MIN(
                        a.precio_unitario_adjudicado
                    ) AS mejor_precio_adjudicado,

                    COALESCE(
                        SUM(a.cantidad_adjudicada),
                        0
                    ) AS cantidad_total_adjudicada,

                    COALESCE(
                        SUM(a.porcentaje_adjudicado),
                        0
                    ) AS porcentaje_total_adjudicado,

                    COALESCE(
                        SUM(
                            a.cantidad_adjudicada
                            * a.precio_unitario_adjudicado
                        ),
                        0
                    ) AS valor_total_adjudicado

                FROM universo_filtrado AS uf
                LEFT JOIN simi.adjudicaciones AS a
                    ON a.id_procedimiento = uf.id_procedimiento
                    AND a.id_clave = uf.id_clave
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave
            )
            SELECT
                uf.id_procedimiento,
                uf.numero_procedimiento,
                uf.ejercicio,
                uf.id_procedimiento_clave,
                uf.id_clave,
                uf.cantidad_requerida,

                COALESCE(
                    pa.proveedores_oferta_inicial,
                    0
                ) AS proveedores_oferta_inicial,

                COALESCE(
                    pa.total_propuestas_iniciales,
                    0
                ) AS total_propuestas_iniciales,

                COALESCE(
                    ea.evaluaciones_positivas,
                    0
                ) AS evaluaciones_positivas,

                COALESCE(
                    ea.evaluaciones_negativas,
                    0
                ) AS evaluaciones_negativas,

                COALESCE(
                    pa.total_subastas,
                    0
                ) AS total_subastas,

                COALESCE(
                    aa.proveedores_adjudicados,
                    0
                ) AS proveedores_adjudicados,

                pa.mejor_precio_inicial,
                pa.mejor_precio_viable,
                pa.mejor_precio_subasta,
                aa.mejor_precio_adjudicado,

                COALESCE(
                    aa.cantidad_total_adjudicada,
                    0
                ) AS cantidad_total_adjudicada,

                COALESCE(
                    aa.porcentaje_total_adjudicado,
                    0
                ) AS porcentaje_total_adjudicado,

                COALESCE(
                    aa.valor_total_adjudicado,
                    0
                ) AS valor_total_adjudicado

            FROM universo_filtrado AS uf
            LEFT JOIN propuestas_agregadas AS pa
                ON pa.id_procedimiento = uf.id_procedimiento
                AND pa.id_clave = uf.id_clave
            LEFT JOIN evaluaciones_agregadas AS ea
                ON ea.id_procedimiento = uf.id_procedimiento
                AND ea.id_clave = uf.id_clave
            LEFT JOIN adjudicaciones_agregadas AS aa
                ON aa.id_procedimiento = uf.id_procedimiento
                AND aa.id_clave = uf.id_clave
            ORDER BY
                uf.ejercicio DESC,
                uf.numero_procedimiento,
                uf.id_procedimiento;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.TIPO_INICIAL,
                self.TIPO_INICIAL,
                self.TIPO_INICIAL,
                self.TIPO_INICIAL,
                self.RESULTADO_POSITIVA,
                self.TIPO_SUBASTA,
                self.TIPO_SUBASTA,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # DETALLE POR PROVEEDOR
    # ==========================================================

    def obtener_detalle_proveedores(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve una fila por procedimiento, clave y proveedor.

        La población incluye proveedores presentes en cualquier etapa:
        propuesta, evaluación, subasta o adjudicación.
        """
        where_sql, params = self._construir_filtros(
            id_clave=id_clave,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_clave="pc",
            alias_procedimiento="pr",
        )

        query = f"""
            WITH universo_filtrado AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave
                FROM simi.procedimientos AS pr
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pr.id_procedimiento
                {where_sql}
            ),
            participantes AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento_clave =
                        p.id_procedimiento_clave

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = et.id_procedimiento
                    AND uf.id_clave = et.id_clave

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = a.id_procedimiento
                    AND uf.id_clave = a.id_clave
            ),
            propuestas_iniciales AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor,
                    MIN(p.id_propuesta) AS id_propuesta_inicial,
                    MAX(p.cantidad_ofertada) AS cantidad_inicial,
                    MIN(p.precio_unitario) AS precio_inicial
                FROM simi.propuestas AS p
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento_clave =
                        p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor
            ),
            propuestas_subasta AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor,
                    MIN(p.id_propuesta) AS id_propuesta_subasta,
                    MAX(p.cantidad_ofertada) AS cantidad_subasta,
                    MIN(p.precio_unitario) AS precio_subasta
                FROM simi.propuestas AS p
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento_clave =
                        p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    p.id_proveedor
            ),
            evaluaciones AS (
                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor,
                    MIN(et.id_evaluacion) AS id_evaluacion,
                    MAX(et.resultado) AS resultado_tecnico
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = et.id_procedimiento
                    AND uf.id_clave = et.id_clave
                GROUP BY
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
            ),
            adjudicaciones AS (
                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor,
                    MIN(a.id_adjudicacion) AS id_adjudicacion,
                    SUM(a.cantidad_adjudicada) AS cantidad_adjudicada,
                    SUM(a.porcentaje_adjudicado) AS porcentaje_adjudicado,
                    MIN(
                        a.precio_unitario_adjudicado
                    ) AS precio_adjudicado
                FROM simi.adjudicaciones AS a
                INNER JOIN universo_filtrado AS uf
                    ON uf.id_procedimiento = a.id_procedimiento
                    AND uf.id_clave = a.id_clave
                GROUP BY
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
            )
            SELECT
                uf.id_procedimiento,
                uf.numero_procedimiento,
                uf.ejercicio,

                pv.id_proveedor,
                pv.rfc,
                pv.razon_social,

                pi.id_propuesta_inicial,
                pi.cantidad_inicial,
                pi.precio_inicial,

                ev.id_evaluacion,
                ev.resultado_tecnico,

                ps.id_propuesta_subasta,
                ps.cantidad_subasta,
                ps.precio_subasta,

                ad.id_adjudicacion,
                ad.cantidad_adjudicada,
                ad.porcentaje_adjudicado,
                ad.precio_adjudicado

            FROM participantes AS pa
            INNER JOIN universo_filtrado AS uf
                ON uf.id_procedimiento = pa.id_procedimiento
                AND uf.id_clave = pa.id_clave
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = pa.id_proveedor
            LEFT JOIN propuestas_iniciales AS pi
                ON pi.id_procedimiento = pa.id_procedimiento
                AND pi.id_clave = pa.id_clave
                AND pi.id_proveedor = pa.id_proveedor
            LEFT JOIN propuestas_subasta AS ps
                ON ps.id_procedimiento = pa.id_procedimiento
                AND ps.id_clave = pa.id_clave
                AND ps.id_proveedor = pa.id_proveedor
            LEFT JOIN evaluaciones AS ev
                ON ev.id_procedimiento = pa.id_procedimiento
                AND ev.id_clave = pa.id_clave
                AND ev.id_proveedor = pa.id_proveedor
            LEFT JOIN adjudicaciones AS ad
                ON ad.id_procedimiento = pa.id_procedimiento
                AND ad.id_clave = pa.id_clave
                AND ad.id_proveedor = pa.id_proveedor
            ORDER BY
                uf.ejercicio DESC,
                uf.numero_procedimiento,
                pv.razon_social,
                pv.rfc;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.TIPO_INICIAL,
                self.TIPO_SUBASTA,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # HISTORIAL DE PRECIOS
    # ==========================================================

    def obtener_historial_precios(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve la base histórica de precios de la clave
        agrupada por procedimiento.

        Las propuestas y adjudicaciones se agregan en CTE separados
        para evitar multiplicar cantidades o valores adjudicados.
        """
        where_sql, params = self._construir_filtros(
            id_clave=id_clave,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_clave="pc",
            alias_procedimiento="pr",
        )

        query = f"""
            WITH universo_filtrado AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave
                FROM simi.procedimientos AS pr
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pr.id_procedimiento
                {where_sql}
            ),
            precios AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_inicial,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                                AND et.resultado = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_viable,

                    MIN(
                        CASE
                            WHEN p.tipo_propuesta = %s
                                AND et.resultado = %s
                            THEN p.precio_unitario
                        END
                    ) AS mejor_precio_subasta

                FROM universo_filtrado AS uf
                LEFT JOIN simi.propuestas AS p
                    ON p.id_procedimiento_clave =
                        uf.id_procedimiento_clave
                LEFT JOIN simi.evaluaciones_tecnicas AS et
                    ON et.id_procedimiento = uf.id_procedimiento
                    AND et.id_clave = uf.id_clave
                    AND et.id_proveedor = p.id_proveedor
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave
            ),
            adjudicaciones AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,

                    MIN(
                        a.precio_unitario_adjudicado
                    ) AS mejor_precio_adjudicado,

                    COALESCE(
                        SUM(a.cantidad_adjudicada),
                        0
                    ) AS cantidad_total_adjudicada,

                    COALESCE(
                        SUM(
                            a.cantidad_adjudicada
                            * a.precio_unitario_adjudicado
                        ),
                        0
                    ) AS valor_total_adjudicado

                FROM universo_filtrado AS uf
                LEFT JOIN simi.adjudicaciones AS a
                    ON a.id_procedimiento = uf.id_procedimiento
                    AND a.id_clave = uf.id_clave
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave
            )
            SELECT
                uf.id_procedimiento,
                uf.numero_procedimiento,
                uf.ejercicio,

                p.mejor_precio_inicial,
                p.mejor_precio_viable,
                p.mejor_precio_subasta,
                a.mejor_precio_adjudicado,

                COALESCE(
                    a.cantidad_total_adjudicada,
                    0
                ) AS cantidad_total_adjudicada,

                COALESCE(
                    a.valor_total_adjudicado,
                    0
                ) AS valor_total_adjudicado

            FROM universo_filtrado AS uf
            LEFT JOIN precios AS p
                ON p.id_procedimiento = uf.id_procedimiento
                AND p.id_clave = uf.id_clave
            LEFT JOIN adjudicaciones AS a
                ON a.id_procedimiento = uf.id_procedimiento
                AND a.id_clave = uf.id_clave
            ORDER BY
                uf.ejercicio,
                uf.numero_procedimiento,
                uf.id_procedimiento;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.TIPO_INICIAL,
                self.TIPO_INICIAL,
                self.RESULTADO_POSITIVA,
                self.TIPO_SUBASTA,
                self.RESULTADO_POSITIVA,
            ),
            conn=conn,
            fetchall=True,
        )