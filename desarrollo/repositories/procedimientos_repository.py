"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimientos_repository.py

Repositorio para la tabla simi.procedimientos.

Responsabilidades:

- Consultar procedimientos.
- Crear procedimientos.
- Activar o desactivar procedimientos.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProcedimientosRepository(BaseRepository):
    """
    Repositorio especializado para la tabla procedimientos.
    """

    def __init__(self):
        super().__init__(
            table_name="procedimientos",
            primary_key="id_procedimiento",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_activos(self, conn=None):
        """
        Devuelve todos los procedimientos activos.

        Los registros más recientes aparecen primero.
        """

        query = """
            SELECT *
            FROM simi.procedimientos
            WHERE activo = TRUE
            ORDER BY
                fecha_creacion DESC,
                id_procedimiento DESC;
        """

        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    def get_by_numero_procedimiento(
        self,
        numero_procedimiento: str,
        conn=None,
    ):
        """
        Busca un procedimiento mediante su número o nombre.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.procedimientos
            WHERE numero_procedimiento = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(numero_procedimiento,),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_procedimiento(
        self,
        numero_procedimiento: str,
        descripcion: str | None,
        ejercicio: int,
        activo: bool = True,
        conn=None,
    ):
        """
        Crea un procedimiento.

        Los valores deben llegar normalizados y validados
        desde el Service correspondiente.
        """

        data = {
            "numero_procedimiento": numero_procedimiento,
            "descripcion": descripcion,
            "ejercicio": ejercicio,
            "activo": activo,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ESTADO
    # ==========================================================

    def activar(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Activa un procedimiento.
        """

        return self.update(
            record_id=id_procedimiento,
            data={"activo": True},
            conn=conn,
        )

    def desactivar(
        self,
        id_procedimiento: int,
        conn=None,
    ):
        """
        Desactiva un procedimiento.

        No elimina físicamente el registro.
        """

        return self.update(
            record_id=id_procedimiento,
            data={"activo": False},
            conn=conn,
        )