"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

evaluaciones_tecnicas_repository.py

Repositorio para la tabla simi.evaluaciones_tecnicas.

Responsabilidades:
- Consultar evaluaciones técnicas.
- Detectar evaluaciones existentes.
- Crear evaluaciones técnicas.
- Actualizar el resultado de una evaluación existente.
- Consultar evaluaciones por procedimiento, proveedor o clave.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza:
- Normalización.
- Validaciones de negocio.
- Apertura o cierre de conexiones.
- Commit o rollback.
- Cálculos técnicos o económicos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class EvaluacionesTecnicasRepository(BaseRepository):
    """
    Repositorio especializado para evaluaciones técnicas.
    """

    RESULTADO_POSITIVA = "POSITIVA"
    RESULTADO_NEGATIVA = "NEGATIVA"

    RESULTADOS_VALIDOS = {
        RESULTADO_POSITIVA,
        RESULTADO_NEGATIVA,
    }

    def __init__(self):
        super().__init__(
            table_name="evaluaciones_tecnicas",
            primary_key="id_evaluacion",
        )

    # ==========================================================
    # CONSULTAS DE EXISTENCIA
    # ==========================================================

    def get_by_combinacion(
        self,
        id_procedimiento: int,
        id_proveedor: int,
        id_clave: int,
        conn=None,
    ):
        """
        Busca una evaluación mediante la combinación única lógica:

        procedimiento + proveedor + clave.

        Devuelve el registro encontrado o None.
        """

        query = """
            SELECT
                id_evaluacion,
                id_procedimiento,
                id_proveedor,
                id_clave,
                resultado
            FROM simi.evaluaciones_tecnicas
            WHERE id_procedimiento = %s
              AND id_proveedor = %s
              AND id_clave = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_proveedor,
                id_clave,
            ),
            conn=conn,
            fetchone=True,
        )

    def existe_evaluacion(
        self,
        id_procedimiento: int,
        id_proveedor: int,
        id_clave: int,
        conn=None,
    ):
        """
        Alias descriptivo para consultar si una evaluación ya existe.

        Devuelve el registro encontrado o None.
        """

        return self.get_by_combinacion(
            id_procedimiento=id_procedimiento,
            id_proveedor=id_proveedor,
            id_clave=id_clave,
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
        Devuelve todas las evaluaciones técnicas de un procedimiento,
        incluyendo información de la clave y del proveedor.
        """

        query = """
            SELECT
                et.id_evaluacion,
                et.id_procedimiento,
                et.id_proveedor,
                et.id_clave,
                et.resultado,

                c.clave,
                c.descripcion,

                p.rfc,
                p.razon_social

            FROM simi.evaluaciones_tecnicas AS et

            INNER JOIN simi.claves AS c
                ON c.id_clave = et.id_clave

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = et.id_proveedor

            WHERE et.id_procedimiento = %s

            ORDER BY
                c.clave,
                p.razon_social,
                et.id_evaluacion;
        """

        return self.custom_query(
            query=query,
            params=(id_procedimiento,),
            conn=conn,
            fetchall=True,
        )

    def get_by_proveedor(
        self,
        id_proveedor: int,
        conn=None,
    ):
        """
        Devuelve todas las evaluaciones técnicas de un proveedor.
        """

        query = """
            SELECT
                et.id_evaluacion,
                et.id_procedimiento,
                et.id_proveedor,
                et.id_clave,
                et.resultado,

                c.clave,
                c.descripcion

            FROM simi.evaluaciones_tecnicas AS et

            INNER JOIN simi.claves AS c
                ON c.id_clave = et.id_clave

            WHERE et.id_proveedor = %s

            ORDER BY
                et.id_procedimiento DESC,
                c.clave,
                et.id_evaluacion;
        """

        return self.custom_query(
            query=query,
            params=(id_proveedor,),
            conn=conn,
            fetchall=True,
        )

    def get_by_clave(
        self,
        id_clave: int,
        conn=None,
    ):
        """
        Devuelve todas las evaluaciones técnicas de una clave.
        """

        query = """
            SELECT
                et.id_evaluacion,
                et.id_procedimiento,
                et.id_proveedor,
                et.id_clave,
                et.resultado,

                p.rfc,
                p.razon_social

            FROM simi.evaluaciones_tecnicas AS et

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = et.id_proveedor

            WHERE et.id_clave = %s

            ORDER BY
                et.id_procedimiento DESC,
                p.razon_social,
                et.id_evaluacion;
        """

        return self.custom_query(
            query=query,
            params=(id_clave,),
            conn=conn,
            fetchall=True,
        )

    def get_positivas_by_procedimiento(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Devuelve las evaluaciones POSITIVAS de un procedimiento.

        Esta consulta será utilizada posteriormente por la carga
        de subasta para verificar proveedores técnicamente aprobados.
        """

        query = """
            SELECT
                et.id_evaluacion,
                et.id_procedimiento,
                et.id_proveedor,
                et.id_clave,
                et.resultado,

                c.clave,
                c.descripcion,

                p.rfc,
                p.razon_social

            FROM simi.evaluaciones_tecnicas AS et

            INNER JOIN simi.claves AS c
                ON c.id_clave = et.id_clave

            INNER JOIN simi.proveedores AS p
                ON p.id_proveedor = et.id_proveedor

            WHERE et.id_procedimiento = %s
              AND et.resultado = %s

            ORDER BY
                c.clave,
                p.razon_social,
                et.id_evaluacion;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                self.RESULTADO_POSITIVA,
            ),
            conn=conn,
            fetchall=True,
        )

    def proveedor_aprobado_para_clave(
        self,
        id_procedimiento: int,
        id_proveedor: int,
        id_clave: int,
        conn=None,
    ):
        """
        Busca una evaluación POSITIVA para la combinación:

        procedimiento + proveedor + clave.

        Devuelve el registro encontrado o None.

        Este método permite que el Service de subasta verifique
        la evaluación técnica previa sin colocar lógica de negocio
        dentro del Repository.
        """

        query = """
            SELECT
                id_evaluacion,
                id_procedimiento,
                id_proveedor,
                id_clave,
                resultado
            FROM simi.evaluaciones_tecnicas
            WHERE id_procedimiento = %s
              AND id_proveedor = %s
              AND id_clave = %s
              AND resultado = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(
                id_procedimiento,
                id_proveedor,
                id_clave,
                self.RESULTADO_POSITIVA,
            ),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_evaluacion(
        self,
        id_procedimiento: int,
        id_proveedor: int,
        id_clave: int,
        resultado: str,
        conn=None,
    ):
        """
        Crea una evaluación técnica.

        Los datos deben llegar previamente normalizados,
        validados y verificados desde la capa Service.
        """

        data = {
            "id_procedimiento": id_procedimiento,
            "id_proveedor": id_proveedor,
            "id_clave": id_clave,
            "resultado": resultado,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_resultado(
        self,
        id_evaluacion: int,
        resultado: str,
        conn=None,
    ):
        """
        Actualiza únicamente el resultado de una evaluación existente.

        La decisión de permitir la actualización pertenece
        exclusivamente a la capa Service.
        """

        data = {
            "resultado": resultado,
        }

        return self.update(
            record_id=id_evaluacion,
            data=data,
            conn=conn,
        )