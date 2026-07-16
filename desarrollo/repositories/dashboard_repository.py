"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

dashboard_repository.py

Repositorio analítico para el Dashboard Ejecutivo.

Responsabilidades:
- Consultar indicadores generales del Dashboard.
- Recuperar el estado analítico de las claves.
- Recuperar la participación de proveedores por etapa.
- Recuperar la aprobación técnica por proveedor.
- Recuperar datos de competencia por procedimiento.
- Recuperar precios iniciales, viables y de subasta por clave.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository:
- No normaliza datos.
- No aplica reglas de presentación.
- No clasifica niveles de competencia.
- No calcula porcentajes en Python.
- No abre ni cierra conexiones.
- No administra commit ni rollback.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class DashboardRepository(BaseRepository):
    """Repositorio especializado para consultas del Dashboard Ejecutivo."""

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"
    RESULTADO_POSITIVA = "POSITIVA"
    RESULTADO_NEGATIVA = "NEGATIVA"

    def __init__(self):
        super().__init__(
            table_name="procedimientos",
            primary_key="id_procedimiento",
        )

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @staticmethod
    def _construir_filtros(
        id_procedimiento=None,
        ejercicio=None,
        alias_procedimiento="pr",
    ):
        """
        Construye filtros SQL parametrizados para procedimiento y ejercicio.

        Los nombres de alias se definen internamente y nunca proceden
        directamente de entradas del usuario.
        """
        condiciones = []
        parametros = []

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

        if not condiciones:
            return "", ()

        return "WHERE " + " AND ".join(condiciones), tuple(parametros)

    # ==========================================================
    # CATÁLOGOS PARA FILTROS
    # ==========================================================

    def obtener_procedimientos_filtro(self, conn=None):
        """Devuelve procedimientos disponibles para el selector del Dashboard."""
        query = """
            SELECT
                id_procedimiento,
                numero_procedimiento,
                descripcion,
                ejercicio,
                activo
            FROM simi.procedimientos
            ORDER BY ejercicio DESC,
                     fecha_creacion DESC,
                     id_procedimiento DESC;
        """
        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    def obtener_ejercicios_filtro(self, conn=None):
        """Devuelve los ejercicios registrados, sin duplicados."""
        query = """
            SELECT DISTINCT
                ejercicio
            FROM simi.procedimientos
            WHERE ejercicio IS NOT NULL
            ORDER BY ejercicio DESC;
        """
        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # INDICADORES PRINCIPALES
    # ==========================================================

    def obtener_indicadores_principales(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve los conteos base del Dashboard.

        Incluye:
        - Total de procedimientos.
        - Total de claves distintas.
        - Total de proveedores participantes en cualquier etapa.
        - Total de propuestas iniciales.
        - Claves adjudicadas.
        - Claves desiertas: claves del universo sin oferta inicial.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            WITH procedimientos_filtrados AS (
                SELECT
                    pr.id_procedimiento
                FROM simi.procedimientos AS pr
                {where_sql}
            ),
            universo AS (
                SELECT
                    pc.id_procedimiento_clave,
                    pc.id_procedimiento,
                    pc.id_clave
                FROM simi.procedimiento_claves AS pc
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = pc.id_procedimiento
            ),
            propuestas_iniciales AS (
                SELECT
                    p.id_propuesta,
                    p.id_procedimiento_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo AS u
                    ON u.id_procedimiento_clave =
                       p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s
            ),
            proveedores_participantes AS (
                SELECT
                    pi.id_proveedor
                FROM propuestas_iniciales AS pi

                UNION

                SELECT
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = et.id_procedimiento

                UNION

                SELECT
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo AS u
                    ON u.id_procedimiento_clave =
                       p.id_procedimiento_clave
                WHERE p.tipo_propuesta = %s

                UNION

                SELECT
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = a.id_procedimiento
            ),
            claves_adjudicadas AS (
                SELECT DISTINCT
                    a.id_procedimiento,
                    a.id_clave
                FROM simi.adjudicaciones AS a
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = a.id_procedimiento
            ),
            claves_desiertas AS (
                SELECT
                    u.id_procedimiento,
                    u.id_clave
                FROM universo AS u
                LEFT JOIN propuestas_iniciales AS pi
                    ON pi.id_procedimiento_clave =
                       u.id_procedimiento_clave
                GROUP BY
                    u.id_procedimiento,
                    u.id_clave
                HAVING COUNT(pi.id_propuesta) = 0
            )
            SELECT
                (
                    SELECT COUNT(*)
                    FROM procedimientos_filtrados
                ) AS total_procedimientos,
                (
                    SELECT COUNT(DISTINCT id_clave)
                    FROM universo
                ) AS total_claves,
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
                    FROM claves_adjudicadas
                ) AS total_claves_adjudicadas,
                (
                    SELECT COUNT(*)
                    FROM claves_desiertas
                ) AS total_claves_desiertas;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.TIPO_INICIAL,
                self.TIPO_SUBASTA,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # COMPETENCIA
    # ==========================================================

    def obtener_competencia_por_clave(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve proveedores con oferta inicial por procedimiento y clave.

        Las claves sin propuestas se conservan con total_proveedores = 0.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            SELECT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_procedimiento_clave,
                pc.id_clave,
                c.clave,
                c.descripcion,
                COUNT(
                    DISTINCT CASE
                        WHEN p.tipo_propuesta = %s
                        THEN p.id_proveedor
                    END
                ) AS total_proveedores
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            LEFT JOIN simi.propuestas AS p
                ON p.id_procedimiento_clave =
                   pc.id_procedimiento_clave
            {where_sql}
            GROUP BY
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_procedimiento_clave,
                pc.id_clave,
                c.clave,
                c.descripcion
            ORDER BY
                pr.ejercicio DESC,
                pr.numero_procedimiento,
                c.clave;
        """

        return self.custom_query(
            query=query,
            params=(
                self.TIPO_INICIAL,
                *params,
            ),
            conn=conn,
            fetchall=True,
        )

    def obtener_resumen_competencia_procedimientos(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve la base agregada para el resumen por procedimiento.

        El nivel cualitativo se asignará posteriormente en el Service.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            WITH competencia_clave AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave,
                    COUNT(
                        DISTINCT CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.id_proveedor
                        END
                    ) AS total_proveedores
                FROM simi.procedimientos AS pr
                INNER JOIN simi.procedimiento_claves AS pc
                    ON pc.id_procedimiento = pr.id_procedimiento
                LEFT JOIN simi.propuestas AS p
                    ON p.id_procedimiento_clave =
                       pc.id_procedimiento_clave
                {where_sql}
                GROUP BY
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio,
                    pc.id_procedimiento_clave,
                    pc.id_clave
            )
            SELECT
                id_procedimiento,
                numero_procedimiento,
                ejercicio,
                COUNT(*) AS total_claves,
                COALESCE(
                    AVG(total_proveedores),
                    0
                ) AS promedio_proveedores_por_clave,
                COUNT(*) FILTER (
                    WHERE total_proveedores = 0
                ) AS claves_desiertas
            FROM competencia_clave
            GROUP BY
                id_procedimiento,
                numero_procedimiento,
                ejercicio
            ORDER BY
                promedio_proveedores_por_clave DESC,
                ejercicio DESC,
                numero_procedimiento;
        """

        return self.custom_query(
            query=query,
            params=(
                self.TIPO_INICIAL,
                *params,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # ESTADO ANALÍTICO DE CLAVES
    # ==========================================================

    def obtener_estado_claves(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve los datos necesarios para clasificar cada clave.

        El Service asignará estados como:
        - DESIERTA
        - CON OFERTAS
        - SIN APROBACIÓN TÉCNICA
        - CON APROBADOS SIN ADJUDICACIÓN
        - ADJUDICADA
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            SELECT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_procedimiento_clave,
                pc.id_clave,
                c.clave,
                c.descripcion,
                COUNT(
                    DISTINCT CASE
                        WHEN p.tipo_propuesta = %s
                        THEN p.id_proveedor
                    END
                ) AS proveedores_oferta_inicial,
                COUNT(
                    DISTINCT CASE
                        WHEN et.resultado = %s
                        THEN et.id_proveedor
                    END
                ) AS evaluaciones_positivas,
                COUNT(
                    DISTINCT CASE
                        WHEN et.resultado = %s
                        THEN et.id_proveedor
                    END
                ) AS evaluaciones_negativas,
                CASE
                    WHEN COUNT(
                        DISTINCT CASE
                            WHEN p.tipo_propuesta = %s
                            THEN p.id_propuesta
                        END
                    ) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS tiene_subasta,
                CASE
                    WHEN COUNT(
                        DISTINCT a.id_adjudicacion
                    ) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS tiene_adjudicacion
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            LEFT JOIN simi.propuestas AS p
                ON p.id_procedimiento_clave =
                   pc.id_procedimiento_clave
            LEFT JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pr.id_procedimiento
               AND et.id_clave = pc.id_clave
            LEFT JOIN simi.adjudicaciones AS a
                ON a.id_procedimiento = pr.id_procedimiento
               AND a.id_clave = pc.id_clave
            {where_sql}
            GROUP BY
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_procedimiento_clave,
                pc.id_clave,
                c.clave,
                c.descripcion
            ORDER BY
                pr.ejercicio DESC,
                pr.numero_procedimiento,
                c.clave;
        """

        return self.custom_query(
            query=query,
            params=(
                self.TIPO_INICIAL,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
                self.TIPO_SUBASTA,
                *params,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # PARTICIPACIÓN Y APROBACIÓN POR PROVEEDOR
    # ==========================================================

    def obtener_participacion_proveedores(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve todos los proveedores presentes en alguna etapa.

        Identifica:
        - Oferta inicial.
        - Evaluación técnica.
        - Subasta.
        - Adjudicación.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            WITH procedimientos_filtrados AS (
                SELECT
                    pr.id_procedimiento,
                    pr.numero_procedimiento,
                    pr.ejercicio
                FROM simi.procedimientos AS pr
                {where_sql}
            ),
            universo AS (
                SELECT
                    pc.id_procedimiento_clave,
                    pc.id_procedimiento,
                    pc.id_clave
                FROM simi.procedimiento_claves AS pc
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = pc.id_procedimiento
            ),
            participantes AS (
                SELECT
                    u.id_procedimiento,
                    u.id_clave,
                    p.id_proveedor
                FROM simi.propuestas AS p
                INNER JOIN universo AS u
                    ON u.id_procedimiento_clave =
                       p.id_procedimiento_clave

                UNION

                SELECT
                    et.id_procedimiento,
                    et.id_clave,
                    et.id_proveedor
                FROM simi.evaluaciones_tecnicas AS et
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = et.id_procedimiento

                UNION

                SELECT
                    a.id_procedimiento,
                    a.id_clave,
                    a.id_proveedor
                FROM simi.adjudicaciones AS a
                INNER JOIN procedimientos_filtrados AS pf
                    ON pf.id_procedimiento = a.id_procedimiento
            )
            SELECT
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social,
                COUNT(
                    DISTINCT pa.id_procedimiento
                ) AS procedimientos_participados,
                COUNT(
                    DISTINCT CASE
                        WHEN pi.id_propuesta IS NOT NULL
                        THEN (
                            pa.id_procedimiento,
                            pa.id_clave
                        )
                    END
                ) AS claves_ofertadas,
                CASE
                    WHEN COUNT(pi.id_propuesta) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS presento_oferta_inicial,
                COUNT(
                    DISTINCT CASE
                        WHEN et.resultado = %s
                        THEN (
                            et.id_procedimiento,
                            et.id_clave
                        )
                    END
                ) AS evaluaciones_positivas,
                COUNT(
                    DISTINCT CASE
                        WHEN et.resultado = %s
                        THEN (
                            et.id_procedimiento,
                            et.id_clave
                        )
                    END
                ) AS evaluaciones_negativas,
                CASE
                    WHEN COUNT(ps.id_propuesta) > 0
                    THEN TRUE
                    ELSE FALSE
                END AS participo_subasta,
                COUNT(
                    DISTINCT (
                        a.id_procedimiento,
                        a.id_clave
                    )
                ) FILTER (
                    WHERE a.id_adjudicacion IS NOT NULL
                ) AS claves_adjudicadas
            FROM participantes AS pa
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = pa.id_proveedor
            LEFT JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pa.id_procedimiento
               AND pc.id_clave = pa.id_clave
            LEFT JOIN simi.propuestas AS pi
                ON pi.id_procedimiento_clave =
                   pc.id_procedimiento_clave
               AND pi.id_proveedor = pa.id_proveedor
               AND pi.tipo_propuesta = %s
            LEFT JOIN simi.propuestas AS ps
                ON ps.id_procedimiento_clave =
                   pc.id_procedimiento_clave
               AND ps.id_proveedor = pa.id_proveedor
               AND ps.tipo_propuesta = %s
            LEFT JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pa.id_procedimiento
               AND et.id_clave = pa.id_clave
               AND et.id_proveedor = pa.id_proveedor
            LEFT JOIN simi.adjudicaciones AS a
                ON a.id_procedimiento = pa.id_procedimiento
               AND a.id_clave = pa.id_clave
               AND a.id_proveedor = pa.id_proveedor
            GROUP BY
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social
            ORDER BY
                pv.razon_social,
                pv.rfc;
        """

        return self.custom_query(
            query=query,
            params=(
                *params,
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
                self.TIPO_INICIAL,
                self.TIPO_SUBASTA,
            ),
            conn=conn,
            fetchall=True,
        )

    def obtener_aprobacion_por_proveedor(
        self,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Devuelve positivas, negativas y total de evaluaciones por proveedor.

        El porcentaje se calculará en el Service para distinguir:
        - 0 % real.
        - SIN EVALUACIONES.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        query = f"""
            SELECT
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social,
                COUNT(et.id_evaluacion) AS total_evaluaciones,
                COUNT(*) FILTER (
                    WHERE et.resultado = %s
                ) AS evaluaciones_positivas,
                COUNT(*) FILTER (
                    WHERE et.resultado = %s
                ) AS evaluaciones_negativas
            FROM simi.procedimientos AS pr
            INNER JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pr.id_procedimiento
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = et.id_proveedor
            {where_sql}
            GROUP BY
                pv.id_proveedor,
                pv.rfc,
                pv.razon_social
            ORDER BY
                pv.razon_social,
                pv.rfc;
        """

        return self.custom_query(
            query=query,
            params=(
                self.RESULTADO_POSITIVA,
                self.RESULTADO_NEGATIVA,
                *params,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # PRECIOS POR CLAVE
    # ==========================================================

    def obtener_precios_por_clave(
        self,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """
        Devuelve:
        - Mejor precio inicial.
        - Mejor precio viable.
        - Mejor precio de subasta.

        Los precios siempre se agrupan por procedimiento y clave.
        """
        where_sql, params = self._construir_filtros(
            id_procedimiento=id_procedimiento,
            ejercicio=ejercicio,
            alias_procedimiento="pr",
        )

        condiciones_adicionales = []
        parametros = list(params)

        if id_clave is not None:
            condiciones_adicionales.append("pc.id_clave = %s")
            parametros.append(id_clave)

        if condiciones_adicionales:
            if where_sql:
                where_sql += " AND " + " AND ".join(
                    condiciones_adicionales
                )
            else:
                where_sql = (
                    "WHERE " + " AND ".join(condiciones_adicionales)
                )

        query = f"""
            SELECT
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_clave,
                c.clave,
                c.descripcion,
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
            FROM simi.procedimientos AS pr
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento = pr.id_procedimiento
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            LEFT JOIN simi.propuestas AS p
                ON p.id_procedimiento_clave =
                   pc.id_procedimiento_clave
            LEFT JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pr.id_procedimiento
               AND et.id_clave = pc.id_clave
               AND et.id_proveedor = p.id_proveedor
            {where_sql}
            GROUP BY
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                pc.id_clave,
                c.clave,
                c.descripcion
            ORDER BY
                pr.ejercicio DESC,
                pr.numero_procedimiento,
                c.clave;
        """

        return self.custom_query(
            query=query,
            params=(
                self.TIPO_INICIAL,
                self.TIPO_INICIAL,
                self.RESULTADO_POSITIVA,
                self.TIPO_SUBASTA,
                self.RESULTADO_POSITIVA,
                *parametros,
            ),
            conn=conn,
            fetchall=True,
        )