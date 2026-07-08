"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

procedimientos_repository.py

Repositorio para la tabla procedimientos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProcedimientosRepository(BaseRepository):
    """
    Repositorio específico para procedimientos.
    """

    def __init__(self):
        super().__init__(
            table_name="procedimientos",
            primary_key="id_procedimiento"
        )

    def get_activos(self):
        """
        Obtiene todos los procedimientos activos.
        """
        query = """
            SELECT *
            FROM procedimientos
            WHERE activo = TRUE
            ORDER BY fecha_creacion DESC, id_procedimiento DESC;
        """

        return self.custom_query(query, fetch=True)

    def get_by_numero_procedimiento(self, numero_procedimiento: str):
        """
        Obtiene un procedimiento por número o nombre de procedimiento.
        """
        query = """
            SELECT *
            FROM procedimientos
            WHERE numero_procedimiento = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(numero_procedimiento,),
            fetch=True
        )

        if result:
            return result[0]

        return None

    def crear_procedimiento(
        self,
        numero_procedimiento: str,
        descripcion: str | None,
        ejercicio: int,
        activo: bool = True
    ):
        """
        Crea un nuevo procedimiento.
        """
        data = {
            "numero_procedimiento": numero_procedimiento,
            "descripcion": descripcion,
            "ejercicio": ejercicio,
            "activo": activo
        }

        return self.insert(data)

    def desactivar(self, id_procedimiento: int):
        """
        Desactiva un procedimiento sin eliminarlo físicamente.
        """
        return self.update(
            record_id=id_procedimiento,
            data={"activo": False}
        )