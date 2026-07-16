"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_proveedor_repository.py

Repositorio analítico para el módulo Análisis por Proveedor.

Responsabilidades:
- Recuperar proveedores disponibles para filtros.
- Recuperar información general del proveedor.
- Recuperar procedimientos, ejercicios y claves relacionados.
- Recuperar indicadores base operativos e históricos.
- Recuperar la participación operativa por procedimiento y clave.
- Recuperar adjudicaciones operativas e históricas.
- Recuperar competidores por coincidencia procedimiento-clave.

Este Repository:
- No normaliza datos.
- No aplica reglas de negocio.
- No calcula variaciones económicas en Python.
- No clasifica victorias o derrotas comerciales.
- No prepara información para Streamlit.
- No abre ni cierra conexiones.
- No administra commit ni rollback.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class AnalisisProveedorRepository(BaseRepository):
    """Repositorio especializado para Análisis por Proveedor."""

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"

    RESULTADO_POSITIVA = "POSITIVA"
    RESULTADO_NEGATIVA = "NEGATIVA"

    def __init__(self):
        super().__init__(
            table_name="proveedores",
            primary_key="id_proveedor",
        )

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @staticmethod
    def _construir_filtros_operativos(
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        alias_proveedor="pa",
        alias_procedimiento="pr",
        alias_clave="c",
    ):
        """Construye filtros SQL parametrizados para datos operativos."""
        condiciones = [f"{alias_proveedor}.id_proveedor = %s"]
        parametros = [id_proveedor]

        if id_procedimiento is not None:
            condiciones.append(
                f"{alias_procedimiento}.id_procedimiento = %s"
            )
            parametros.append(id_procedimiento)

        if ejercicio is not None:
            condiciones.append(f"{alias_procedimiento}.ejercicio = %s")
            parametros.append(ejercicio)

        if id_clave is not None:
            condiciones.append(f"{alias_clave}.id_clave = %s")
            parametros.append(id_clave)

        return "WHERE " + " AND ".join(condiciones), tuple(parametros)

    @staticmethod
    def _construir_filtros_historicos(
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        alias_historico="ah",
    ):
        """
        Construye filtros para adjudicaciones históricas.

        La tabla histórica no contiene id_procedimiento. Cuando se filtra
        un procedimiento operativo concreto, los históricos se excluyen.
        """
        condiciones = [f"{alias_historico}.id_proveedor = %s"]
        parametros = [id_proveedor]

        if id_procedimiento is not None:
            condiciones.append("FALSE")

        if ejercicio is not None:
            condiciones.append(
                f"""
                SUBSTRING(
                    {alias_historico}.numero_procedimiento
                    FROM '(20[0-9]{{2}})'
                )::INTEGER = %s
                """
            )
            parametros.append(ejercicio)

        if id_clave is not None:
            condiciones.append(f"{alias_historico}.id_clave = %s")
            parametros.append(id_clave)

        return "WHERE " + " AND ".join(condiciones), tuple(parametros)

    # ==========================================================
    # CATÁLOGOS PARA FILTROS
    # ==========================================================

    def obtener_proveedores_filtro(self, conn=None):
        """Devuelve proveedores que tienen información analítica."""
        query = """
            SELECT
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social
            FROM simi.proveedores AS pv
            WHERE
                EXISTS (
                    SELECT 1
                    FROM simi.propuestas AS p
                    WHERE p.id_proveedor = pv.id_proveedor
                )
                OR EXISTS (
                    SELECT 1
                    FROM simi.evaluaciones_tecnicas AS et
                    WHERE et.id_proveedor = pv.id_proveedor
                )
                OR EXISTS (
                    SELECT 1
                    FROM simi.adjudicaciones AS a
                    WHERE a.id_proveedor = pv.id_proveedor
                )
                OR EXISTS (
                    SELECT 1
                    FROM simi.adjudicaciones_historicas AS ah
                    WHERE ah.id_proveedor = pv.id_proveedor
                )
            ORDER BY
                pv.razon_social,
                pv.rfc,
                pv.id_proveedor;
        """
        return self.custom_query(query=query, conn=conn, fetchall=True)

    def obtener_informacion_proveedor(self, id_proveedor, conn=None):
        """Devuelve RFC y razón social del proveedor seleccionado."""
        query = """
            SELECT
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social
            FROM simi.proveedores AS pv
            WHERE pv.id_proveedor = %s
            LIMIT 1;
        """
        return self.custom_query(
            query=query,
            params=(id_proveedor,),
            conn=conn,
            fetchone=True,
        )

    def obtener_procedimientos_filtro(self, id_proveedor, conn=None):
        """Devuelve procedimientos operativos donde participó el proveedor."""
        query = """
            WITH participaciones AS (
                SELECT
                    pc.id_procedimiento,
                    pc.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave
                WHERE p.id_proveedor = %s

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et
                WHERE et.id_proveedor = %s

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
                WHERE a.id_proveedor = %s
            )
            SELECT DISTINCT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.descripcion,
                pr.ejercicio,
                pr.activo
            FROM participaciones AS pa
            INNER JOIN simi.procedimientos AS pr
                ON pr.id_procedimiento = pa.id_procedimiento
            ORDER BY
                pr.ejercicio DESC,
                pr.numero_procedimiento,
                pr.id_procedimiento DESC;
        """
        return self.custom_query(
            query=query,
            params=(id_proveedor, id_proveedor, id_proveedor),
            conn=conn,
            fetchall=True,
        )

    def obtener_ejercicios_filtro(self, id_proveedor, conn=None):
        """Devuelve ejercicios operativos e históricos identificables."""
        query = """
            WITH ejercicios AS (
                SELECT DISTINCT pr.ejercicio
                FROM simi.procedimientos AS pr
                INNER JOIN (
                    SELECT
                        pc.id_procedimiento,
                        p.id_proveedor
                    FROM simi.propuestas AS p
                    INNER JOIN simi.procedimiento_claves AS pc
                        ON pc.id_procedimiento_clave =
                            p.id_procedimiento_clave
                    WHERE p.id_proveedor = %s

                    UNION

                    SELECT
                        et.id_procedimiento,
                        et.id_proveedor
                    FROM simi.evaluaciones_tecnicas AS et
                    WHERE et.id_proveedor = %s

                    UNION

                    SELECT
                        a.id_procedimiento,
                        a.id_proveedor
                    FROM simi.adjudicaciones AS a
                    WHERE a.id_proveedor = %s
                ) AS pa
                    ON pa.id_procedimiento = pr.id_procedimiento
                WHERE pr.ejercicio IS NOT NULL

                UNION

                SELECT DISTINCT
                    SUBSTRING(
                        ah.numero_procedimiento
                        FROM '(20[0-9]{2})'
                    )::INTEGER AS ejercicio
                FROM simi.adjudicaciones_historicas AS ah
                WHERE
                    ah.id_proveedor = %s
                    AND SUBSTRING(
                        ah.numero_procedimiento
                        FROM '(20[0-9]{2})'
                    ) IS NOT NULL
            )
            SELECT ejercicio
            FROM ejercicios
            WHERE ejercicio IS NOT NULL
            ORDER BY ejercicio DESC;
        """
        return self.custom_query(
            query=query,
            params=(
                id_proveedor,
                id_proveedor,
                id_proveedor,
                id_proveedor,
            ),
            conn=conn,
            fetchall=True,
        )

    def obtener_claves_filtro(self, id_proveedor, conn=None):
        """Devuelve claves operativas e históricas del proveedor."""
        query = """
            WITH claves_proveedor AS (
                SELECT pc.id_clave
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave
                WHERE p.id_proveedor = %s

                UNION

                SELECT et.id_clave
                FROM simi.evaluaciones_tecnicas AS et
                WHERE et.id_proveedor = %s

                UNION

                SELECT a.id_clave
                FROM simi.adjudicaciones AS a
                WHERE a.id_proveedor = %s

                UNION

                SELECT ah.id_clave
                FROM simi.adjudicaciones_historicas AS ah
                WHERE ah.id_proveedor = %s
            )
            SELECT
                c.id_clave,
                c.clave,
                c.descripcion,
                cc.nombre_categoria AS categoria
            FROM claves_proveedor AS cp
            INNER JOIN simi.claves AS c
                ON c.id_clave = cp.id_clave
            LEFT JOIN simi.cat_categorias_clave AS cc
                ON cc.id_categoria = c.id_categoria
            ORDER BY
                c.clave,
                c.id_clave;
        """
        return self.custom_query(
            query=query,
            params=(
                id_proveedor,
                id_proveedor,
                id_proveedor,
                id_proveedor,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # INDICADORES PRINCIPALES
    # ==========================================================

    def obtener_indicadores_proveedor(
        self,
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """Devuelve conteos y acumulados base del proveedor."""
        where_operativo, params_operativos = self._construir_filtros_operativos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_proveedor="pa",
            alias_procedimiento="pr",
            alias_clave="c",
        )
        where_historico, params_historicos = self._construir_filtros_historicos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_historico="ah",
        )

        query = f"""
            WITH participaciones AS (
                SELECT
                    pc.id_procedimiento,
                    pc.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
            ),
            operativo_filtrado AS (
                SELECT
                    pa.id_procedimiento,
                    pa.id_clave,
                    pa.id_proveedor,
                    pr.numero_procedimiento,
                    pr.ejercicio
                FROM participaciones AS pa
                INNER JOIN simi.procedimientos AS pr
                    ON pr.id_procedimiento = pa.id_procedimiento
                INNER JOIN simi.claves AS c
                    ON c.id_clave = pa.id_clave
                {where_operativo}
            ),
            propuestas_iniciales AS (
                SELECT p.*
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave
                INNER JOIN operativo_filtrado AS ofi
                    ON ofi.id_procedimiento = pc.id_procedimiento
                    AND ofi.id_clave = pc.id_clave
                    AND ofi.id_proveedor = p.id_proveedor
                WHERE p.tipo_propuesta = %s
            ),
            propuestas_subasta AS (
                SELECT p.*
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave
                INNER JOIN operativo_filtrado AS ofi
                    ON ofi.id_procedimiento = pc.id_procedimiento
                    AND ofi.id_clave = pc.id_clave
                    AND ofi.id_proveedor = p.id_proveedor
                WHERE p.tipo_propuesta = %s
            ),
            evaluaciones AS (
                SELECT et.*
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN operativo_filtrado AS ofi
                    ON ofi.id_procedimiento = et.id_procedimiento
                    AND ofi.id_clave = et.id_clave
                    AND ofi.id_proveedor = et.id_proveedor
            ),
            adjudicaciones_operativas AS (
                SELECT a.*
                FROM simi.adjudicaciones AS a
                INNER JOIN operativo_filtrado AS ofi
                    ON ofi.id_procedimiento = a.id_procedimiento
                    AND ofi.id_clave = a.id_clave
                    AND ofi.id_proveedor = a.id_proveedor
            ),
            adjudicaciones_historicas AS (
                SELECT ah.*
                FROM simi.adjudicaciones_historicas AS ah
                {where_historico}
            )
            SELECT
                (
                    SELECT COUNT(DISTINCT id_procedimiento)
                    FROM operativo_filtrado
                ) AS total_procedimientos_participados,
                (
                    SELECT COUNT(DISTINCT id_clave)
                    FROM propuestas_iniciales AS pi
                    INNER JOIN simi.procedimiento_claves AS pc
                        ON pc.id_procedimiento_clave =
                            pi.id_procedimiento_clave
                ) AS total_claves_ofertadas,
                (
                    SELECT COUNT(*)
                    FROM (
                        SELECT DISTINCT
                            pc.id_procedimiento,
                            pc.id_clave
                        FROM propuestas_iniciales AS pi
                        INNER JOIN simi.procedimiento_claves AS pc
                            ON pc.id_procedimiento_clave =
                                pi.id_procedimiento_clave
                    ) AS participaciones_ofertadas
                ) AS total_participaciones_procedimiento_clave,
                (
                    SELECT COUNT(*)
                    FROM propuestas_iniciales
                ) AS total_propuestas_iniciales,
                (
                    SELECT COUNT(*)
                    FROM propuestas_subasta
                ) AS total_propuestas_subasta,
                (
                    SELECT COUNT(*)
                    FROM evaluaciones
                    WHERE resultado = %s
                ) AS total_evaluaciones_positivas,
                (
                    SELECT COUNT(*)
                    FROM evaluaciones
                    WHERE resultado = %s
                ) AS total_evaluaciones_negativas,
                (
                    SELECT COUNT(DISTINCT id_clave)
                    FROM adjudicaciones_operativas
                ) AS total_claves_adjudicadas_operativas,
                (
                    SELECT COUNT(DISTINCT id_procedimiento)
                    FROM adjudicaciones_operativas
                ) AS total_procedimientos_adjudicados,
                (
                    SELECT COUNT(*)
                    FROM adjudicaciones_operativas
                ) AS total_adjudicaciones_operativas,
                (
                    SELECT COALESCE(SUM(cantidad_adjudicada), 0)
                    FROM adjudicaciones_operativas
                ) AS cantidad_adjudicada_operativa,
                (
                    SELECT COALESCE(
                        SUM(
                            cantidad_adjudicada *
                            precio_unitario_adjudicado
                        ),
                        0
                    )
                    FROM adjudicaciones_operativas
                ) AS valor_adjudicado_operativo,
                (
                    SELECT COUNT(*)
                    FROM adjudicaciones_historicas
                ) AS total_adjudicaciones_historicas,
                (
                    SELECT COUNT(DISTINCT id_clave)
                    FROM adjudicaciones_historicas
                ) AS total_claves_adjudicadas_historicas,
                (
                    SELECT COALESCE(SUM(cantidad_adjudicada), 0)
                    FROM adjudicaciones_historicas
                ) AS cantidad_adjudicada_historica,
                (
                    SELECT COALESCE(
                        SUM(
                            cantidad_adjudicada *
                            precio_unitario_adjudicado
                        ),
                        0
                    )
                    FROM adjudicaciones_historicas
                ) AS valor_adjudicado_historico;
        """

        return self.custom_query(
            query=query,
            params=(
                *params_operativos,
                self.TIPO_INICIAL,
                self.TIPO_SUBASTA,
                *params_historicos,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # PARTICIPACIÓN OPERATIVA
    # ==========================================================

    def obtener_participacion_operativa(
        self,
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """
        Devuelve una fila por proveedor, procedimiento y clave.

        Incluye las etapas inicial, técnica, subasta y adjudicación.
        """
        where_sql, params = self._construir_filtros_operativos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_proveedor="pa",
            alias_procedimiento="pr",
            alias_clave="c",
        )

        query = f"""
            WITH participantes AS (
                SELECT
                    pc.id_procedimiento,
                    pc.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
            ),
            universo_filtrado AS (
                SELECT
                    pa.id_procedimiento,
                    pa.id_clave,
                    pa.id_proveedor,
                    pr.numero_procedimiento,
                    pr.descripcion AS descripcion_procedimiento,
                    pr.ejercicio,
                    pr.activo,
                    c.clave,
                    c.descripcion AS descripcion_clave,
                    pc.id_procedimiento_clave,
                    pc.cantidad_requerida
                FROM participantes AS pa
                INNER JOIN simi.procedimientos AS pr
                    ON pr.id_procedimiento = pa.id_procedimiento
                INNER JOIN simi.claves AS c
                    ON c.id_clave = pa.id_clave
                LEFT JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pa.id_procedimiento
                    AND pc.id_clave = pa.id_clave
                {where_sql}
            ),
            propuestas_iniciales AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor,
                    MIN(p.id_propuesta) AS id_propuesta_inicial,
                    MAX(p.cantidad_ofertada) AS cantidad_inicial,
                    MIN(p.precio_unitario) AS precio_inicial
                FROM universo_filtrado AS uf
                INNER JOIN simi.propuestas AS p
                    ON p.id_procedimiento_clave =
                        uf.id_procedimiento_clave
                    AND p.id_proveedor = uf.id_proveedor
                WHERE p.tipo_propuesta = %s
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor
            ),
            propuestas_subasta AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor,
                    MIN(p.id_propuesta) AS id_propuesta_subasta,
                    MAX(p.cantidad_ofertada) AS cantidad_subasta,
                    MIN(p.precio_unitario) AS precio_subasta
                FROM universo_filtrado AS uf
                INNER JOIN simi.propuestas AS p
                    ON p.id_procedimiento_clave =
                        uf.id_procedimiento_clave
                    AND p.id_proveedor = uf.id_proveedor
                WHERE p.tipo_propuesta = %s
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor
            ),
            evaluaciones AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor,
                    MIN(et.id_evaluacion) AS id_evaluacion,
                    MAX(et.resultado) AS resultado_tecnico
                FROM universo_filtrado AS uf
                INNER JOIN simi.evaluaciones_tecnicas AS et
                    ON et.id_procedimiento = uf.id_procedimiento
                    AND et.id_clave = uf.id_clave
                    AND et.id_proveedor = uf.id_proveedor
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor
            ),
            adjudicaciones AS (
                SELECT
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor,
                    MIN(a.id_adjudicacion) AS id_adjudicacion,
                    SUM(a.cantidad_adjudicada) AS cantidad_adjudicada,
                    SUM(a.porcentaje_adjudicado) AS porcentaje_adjudicado,
                    CASE
                        WHEN SUM(a.cantidad_adjudicada) > 0
                        THEN SUM(
                            a.precio_unitario_adjudicado *
                            a.cantidad_adjudicada
                        ) / SUM(a.cantidad_adjudicada)
                        ELSE MIN(a.precio_unitario_adjudicado)
                    END AS precio_adjudicado
                FROM universo_filtrado AS uf
                INNER JOIN simi.adjudicaciones AS a
                    ON a.id_procedimiento = uf.id_procedimiento
                    AND a.id_clave = uf.id_clave
                    AND a.id_proveedor = uf.id_proveedor
                GROUP BY
                    uf.id_procedimiento,
                    uf.id_clave,
                    uf.id_proveedor
            )
            SELECT
                uf.id_procedimiento,
                uf.numero_procedimiento,
                uf.descripcion_procedimiento,
                uf.ejercicio,
                uf.activo,
                uf.id_procedimiento_clave,
                uf.cantidad_requerida,
                uf.id_clave,
                uf.clave,
                uf.descripcion_clave,
                uf.id_proveedor,

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
                ad.precio_adjudicado,
                COALESCE(
                    ad.cantidad_adjudicada * ad.precio_adjudicado,
                    0
                ) AS valor_adjudicado
            FROM universo_filtrado AS uf
            LEFT JOIN propuestas_iniciales AS pi
                ON pi.id_procedimiento = uf.id_procedimiento
                AND pi.id_clave = uf.id_clave
                AND pi.id_proveedor = uf.id_proveedor
            LEFT JOIN propuestas_subasta AS ps
                ON ps.id_procedimiento = uf.id_procedimiento
                AND ps.id_clave = uf.id_clave
                AND ps.id_proveedor = uf.id_proveedor
            LEFT JOIN evaluaciones AS ev
                ON ev.id_procedimiento = uf.id_procedimiento
                AND ev.id_clave = uf.id_clave
                AND ev.id_proveedor = uf.id_proveedor
            LEFT JOIN adjudicaciones AS ad
                ON ad.id_procedimiento = uf.id_procedimiento
                AND ad.id_clave = uf.id_clave
                AND ad.id_proveedor = uf.id_proveedor
            ORDER BY
                uf.ejercicio DESC NULLS LAST,
                uf.numero_procedimiento,
                uf.clave,
                uf.id_clave;
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
    # HISTORIAL DE ADJUDICACIONES
    # ==========================================================

    def obtener_historial_adjudicaciones(
        self,
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """Une adjudicaciones operativas e históricas normalizadas."""
        where_operativo, params_operativos = self._construir_filtros_operativos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_proveedor="a",
            alias_procedimiento="pr",
            alias_clave="c",
        )
        where_historico, params_historicos = self._construir_filtros_historicos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_historico="ah",
        )

        query = f"""
            WITH operativas AS (
                SELECT
                    'OPERATIVO'::TEXT AS origen_dato,
                    a.id_adjudicacion AS id_registro,
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    a.id_clave,
                    c.clave,
                    c.descripcion AS descripcion_clave,
                    a.id_proveedor,
                    a.cantidad_adjudicada,
                    a.porcentaje_adjudicado,
                    a.precio_unitario_adjudicado AS precio_adjudicado,
                    COALESCE(
                        a.cantidad_adjudicada *
                        a.precio_unitario_adjudicado,
                        0
                    ) AS valor_adjudicado
                FROM simi.adjudicaciones AS a
                INNER JOIN simi.procedimientos AS pr
                    ON pr.id_procedimiento = a.id_procedimiento
                INNER JOIN simi.claves AS c
                    ON c.id_clave = a.id_clave
                {where_operativo}
            ),
            historicas AS (
                SELECT
                    'HISTORICO'::TEXT AS origen_dato,
                    ah.id_adjudicacion_historica AS id_registro,
                    NULL::INTEGER AS id_procedimiento,
                    ah.numero_procedimiento,
                    SUBSTRING(
                        ah.numero_procedimiento
                        FROM '(20[0-9]{{2}})'
                    )::INTEGER AS ejercicio,
                    ah.id_clave,
                    c.clave,
                    c.descripcion AS descripcion_clave,
                    ah.id_proveedor,
                    ah.cantidad_adjudicada,
                    ah.porcentaje_adjudicado,
                    ah.precio_unitario_adjudicado AS precio_adjudicado,
                    COALESCE(
                        ah.cantidad_adjudicada *
                        ah.precio_unitario_adjudicado,
                        0
                    ) AS valor_adjudicado
                FROM simi.adjudicaciones_historicas AS ah
                INNER JOIN simi.claves AS c
                    ON c.id_clave = ah.id_clave
                {where_historico}
            )
            SELECT * FROM operativas
            UNION ALL
            SELECT * FROM historicas
            ORDER BY
                ejercicio DESC NULLS LAST,
                numero_procedimiento,
                clave,
                origen_dato,
                id_registro;
        """

        return self.custom_query(
            query=query,
            params=(*params_operativos, *params_historicos),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # COMPETENCIA
    # ==========================================================

    def obtener_competidores(
        self,
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """
        Devuelve enfrentamientos operativos por competidor.

        La coincidencia se define por procedimiento + clave. Los datos
        históricos no participan porque no contienen el universo de
        proveedores que compitieron y no fueron adjudicados.
        """
        where_sql, params = self._construir_filtros_operativos(
            id_proveedor=id_proveedor,
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            id_clave=id_clave,
            alias_proveedor="objetivo",
            alias_procedimiento="pr",
            alias_clave="c",
        )

        query = f"""
            WITH participantes AS (
                SELECT
                    pc.id_procedimiento,
                    pc.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento_clave = p.id_procedimiento_clave

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
            ),
            universo_objetivo AS (
                SELECT
                    objetivo.id_procedimiento,
                    objetivo.id_clave,
                    objetivo.id_proveedor
                FROM participantes AS objetivo
                INNER JOIN simi.procedimientos AS pr
                    ON pr.id_procedimiento = objetivo.id_procedimiento
                INNER JOIN simi.claves AS c
                    ON c.id_clave = objetivo.id_clave
                {where_sql}
            ),
            enfrentamientos AS (
                SELECT
                    uo.id_procedimiento,
                    uo.id_clave,
                    uo.id_proveedor AS id_proveedor_objetivo,
                    rival.id_proveedor AS id_competidor
                FROM universo_objetivo AS uo
                INNER JOIN participantes AS rival
                    ON rival.id_procedimiento = uo.id_procedimiento
                    AND rival.id_clave = uo.id_clave
                    AND rival.id_proveedor <> uo.id_proveedor
            ),
            adjudicados AS (
                SELECT DISTINCT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
            ),
            clasificados AS (
                SELECT
                    e.id_procedimiento,
                    e.id_clave,
                    e.id_competidor,
                    CASE WHEN ao.id_proveedor IS NOT NULL
                        THEN 1 ELSE 0 END AS objetivo_adjudicado,
                    CASE WHEN ac.id_proveedor IS NOT NULL
                        THEN 1 ELSE 0 END AS competidor_adjudicado
                FROM enfrentamientos AS e
                LEFT JOIN adjudicados AS ao
                    ON ao.id_procedimiento = e.id_procedimiento
                    AND ao.id_clave = e.id_clave
                    AND ao.id_proveedor = e.id_proveedor_objetivo
                LEFT JOIN adjudicados AS ac
                    ON ac.id_procedimiento = e.id_procedimiento
                    AND ac.id_clave = e.id_clave
                    AND ac.id_proveedor = e.id_competidor
            )
            SELECT
                cl.id_competidor,
                pv.rfc AS rfc_competidor,
                pv.razon_social AS razon_social_competidor,
                COUNT(*) AS coincidencias,
                COUNT(DISTINCT cl.id_procedimiento) AS procedimientos_compartidos,
                COUNT(DISTINCT cl.id_clave) AS claves_compartidas,
                SUM(
                    CASE
                        WHEN cl.objetivo_adjudicado = 1
                            AND cl.competidor_adjudicado = 0
                        THEN 1 ELSE 0
                    END
                ) AS victorias_proveedor,
                SUM(
                    CASE
                        WHEN cl.objetivo_adjudicado = 0
                            AND cl.competidor_adjudicado = 1
                        THEN 1 ELSE 0
                    END
                ) AS victorias_competidor,
                SUM(
                    CASE
                        WHEN cl.objetivo_adjudicado = 1
                            AND cl.competidor_adjudicado = 1
                        THEN 1 ELSE 0
                    END
                ) AS adjudicaciones_compartidas,
                SUM(
                    CASE
                        WHEN cl.objetivo_adjudicado = 0
                            AND cl.competidor_adjudicado = 0
                        THEN 1 ELSE 0
                    END
                ) AS sin_adjudicacion
            FROM clasificados AS cl
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = cl.id_competidor
            GROUP BY
                cl.id_competidor,
                pv.rfc,
                pv.razon_social
            ORDER BY
                coincidencias DESC,
                victorias_proveedor DESC,
                pv.razon_social,
                pv.rfc;
        """

        return self.custom_query(
            query=query,
            params=params,
            conn=conn,
            fetchall=True,
        )