"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimientos_repository.py

Repositorio para la tabla procedimientos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProcedimientosRepository(BaseRepository):

    def __init__(self):
        super().__init__(
            table_name="procedimientos",
            primary_key="id_procedimiento"
        )

    def get_activos(self, conn=None):
        query = """
            SELECT *
            FROM simi.procedimientos
            WHERE activo = TRUE
            ORDER BY fecha_creacion DESC, id_procedimiento DESC;
        """
        return self.custom_query(query, conn=conn, fetch=True)

    def get_by_numero_procedimiento(self, numero_procedimiento: str, conn=None):
        query = """
            SELECT *
            FROM simi.procedimientos
            WHERE numero_procedimiento = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(numero_procedimiento,),
            conn=conn,
            fetch=True
        )

        return result[0] if result else None

    def crear_procedimiento(
        self,
        numero_procedimiento: str,
        descripcion: str | None,
        ejercicio: int,
        activo: bool = True,
        conn=None
    ):
        data = {
            "numero_procedimiento": numero_procedimiento,
            "descripcion": descripcion,
            "ejercicio": ejercicio,
            "activo": activo
        }

        return self.insert(data, conn=conn)

    def desactivar(self, id_procedimiento: int, conn=None):
        return self.update(
            record_id=id_procedimiento,
            data={"activo": False},
            conn=conn
        )