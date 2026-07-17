"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

comparador_im_repository.py

Repositorio analítico para el módulo Comparador de
Investigaciones de Mercado (IM).

Responsabilidades:
- Resolver las claves normalizadas de una nueva IM contra el
  catálogo oficial.
- Recuperar propuestas iniciales y de subasta por lotes.
- Recuperar adjudicaciones operativas por lotes.
- Recuperar adjudicaciones históricas por lotes.
- Entregar al Service un contexto consolidado de solo lectura.

Este Repository:
- No lee archivos Excel.
- No normaliza datos.
- No valida reglas de negocio.
- No calcula indicadores estadísticos.
- No genera recomendaciones.
- No prepara información para Streamlit.
- No inserta, actualiza ni elimina registros.
- No abre ni cierra conexiones.
- No administra commit ni rollback.
- No persiste la nueva IM ni sus resultados.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ComparadorIMRepository(BaseRepository):
    """
    Repository especializado para recuperar la información
    acumulada que utilizará el Comparador de IM.
    """

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"

    ORIGEN_OPERATIVO = "OPERATIVO"
    ORIGEN_HISTORICO = "HISTORICO"

    def __init__(self):
        super().__init__(
            table_name="claves",
            primary_key="id_clave",
        )

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @staticmethod
    def _preparar_lista(valores):
        """
        Convierte una colección en una lista sin duplicados,
        conservando el orden de la primera aparición.

        La normalización del contenido corresponde al Service.
        Esta utilidad únicamente prepara parámetros para SQL.
        """
        if valores is None:
            return []

        resultado = []
        vistos = set()

        for valor in valores:
            if valor is None:
                continue

            if valor in vistos:
                continue

            vistos.add(valor)
            resultado.append(valor)

        return resultado

    def _obtener_claves_por_ids(self, ids_clave, conn=None):
        """
        Recupera la información oficial de varias claves mediante
        sus identificadores.

        Es un método interno utilizado para construir el contexto
        consolidado del comparador.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

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
            WHERE c.id_clave = ANY(%s)
            ORDER BY
                c.clave,
                c.id_clave;
        """

        return self.custom_query(
            query=query,
            params=(ids_clave,),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # RESOLUCIÓN DE CLAVES
    # ==========================================================

    def obtener_claves_por_codigos(self, claves, conn=None):
        """
        Resuelve varias claves normalizadas contra el catálogo
        oficial de SIMI.

        No crea claves inexistentes y no altera el orden ni el
        contenido recibido mediante reglas de normalización.
        """
        claves = self._preparar_lista(claves)

        if not claves:
            return []

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
            WHERE c.clave = ANY(%s)
            ORDER BY
                c.clave,
                c.id_clave;
        """

        return self.custom_query(
            query=query,
            params=(claves,),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # PROPUESTAS ACUMULADAS
    # ==========================================================

    def obtener_propuestas_acumuladas(self, ids_clave, conn=None):
        """
        Recupera todas las propuestas individuales de tipo INICIAL
        y SUBASTA asociadas con las claves solicitadas.

        El resultado técnico se incorpora cuando existe una
        evaluación para la combinación:
        procedimiento + clave + proveedor.

        El Service decidirá qué observaciones son viables y cuáles
        se utilizarán para cada indicador.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

        query = """
            SELECT
                p.id_propuesta,
                pc.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                pr.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                p.id_proveedor,
                pv.rfc,
                pv.razon_social,
                p.tipo_propuesta,
                et.resultado AS resultado_tecnico,
                p.cantidad_ofertada,
                p.pais_origen,
                p.precio_unitario,
                p.fecha_registro
            FROM simi.propuestas AS p
            INNER JOIN simi.procedimiento_claves AS pc
                ON pc.id_procedimiento_clave = p.id_procedimiento_clave
            INNER JOIN simi.claves AS c
                ON c.id_clave = pc.id_clave
            INNER JOIN simi.procedimientos AS pr
                ON pr.id_procedimiento = pc.id_procedimiento
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = p.id_proveedor
            LEFT JOIN simi.evaluaciones_tecnicas AS et
                ON et.id_procedimiento = pr.id_procedimiento
                AND et.id_clave = pc.id_clave
                AND et.id_proveedor = p.id_proveedor
            WHERE pc.id_clave = ANY(%s)
              AND p.tipo_propuesta = ANY(%s)
            ORDER BY
                pc.id_clave,
                pr.ejercicio NULLS LAST,
                pr.numero_procedimiento,
                pr.id_procedimiento,
                p.tipo_propuesta,
                pv.razon_social,
                pv.rfc,
                p.id_propuesta;
        """

        return self.custom_query(
            query=query,
            params=(
                ids_clave,
                [
                    self.TIPO_INICIAL,
                    self.TIPO_SUBASTA,
                ],
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # ADJUDICACIONES OPERATIVAS
    # ==========================================================

    def obtener_adjudicaciones_operativas(
        self,
        ids_clave,
        conn=None,
    ):
        """
        Recupera cada adjudicación operativa como una observación
        independiente.

        No agrupa proveedores, no selecciona precios mínimos y no
        calcula precios ponderados.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

        query = """
            SELECT
                a.id_adjudicacion,
                a.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
                a.id_procedimiento,
                pr.numero_procedimiento,
                pr.ejercicio,
                a.id_proveedor,
                pv.rfc,
                pv.razon_social,
                a.cantidad_adjudicada,
                a.porcentaje_adjudicado,
                a.precio_unitario_adjudicado,
                %s::TEXT AS origen_dato
            FROM simi.adjudicaciones AS a
            INNER JOIN simi.claves AS c
                ON c.id_clave = a.id_clave
            INNER JOIN simi.procedimientos AS pr
                ON pr.id_procedimiento = a.id_procedimiento
            INNER JOIN simi.proveedores AS pv
                ON pv.id_proveedor = a.id_proveedor
            WHERE a.id_clave = ANY(%s)
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
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # ADJUDICACIONES HISTÓRICAS
    # ==========================================================

    def obtener_adjudicaciones_historicas(
        self,
        ids_clave,
        conn=None,
    ):
        """
        Recupera cada adjudicación histórica como una observación
        independiente.

        La tabla histórica no contiene id_procedimiento. El
        ejercicio se obtiene del número de procedimiento únicamente
        cuando existe un año reconocible con formato 20XX.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return []

        query = """
            SELECT
                ah.id_adjudicacion_historica,
                ah.id_clave,
                c.clave,
                c.descripcion AS descripcion_clave,
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
    # CONTEXTO CONSOLIDADO
    # ==========================================================

    def obtener_contexto_comparacion(
        self,
        ids_clave,
        conn=None,
    ):
        """
        Recupera el contexto acumulado de las claves solicitadas.

        Devuelve datos planos y detallados. La agrupación por clave,
        los cálculos estadísticos y las recomendaciones corresponden
        exclusivamente al ComparadorIMService.
        """
        ids_clave = self._preparar_lista(ids_clave)

        if not ids_clave:
            return {
                "claves": [],
                "propuestas": [],
                "adjudicaciones_operativas": [],
                "adjudicaciones_historicas": [],
            }

        return {
            "claves": self._obtener_claves_por_ids(
                ids_clave=ids_clave,
                conn=conn,
            ),
            "propuestas": self.obtener_propuestas_acumuladas(
                ids_clave=ids_clave,
                conn=conn,
            ),
            "adjudicaciones_operativas": (
                self.obtener_adjudicaciones_operativas(
                    ids_clave=ids_clave,
                    conn=conn,
                )
            ),
            "adjudicaciones_historicas": (
                self.obtener_adjudicaciones_historicas(
                    ids_clave=ids_clave,
                    conn=conn,
                )
            ),
        }