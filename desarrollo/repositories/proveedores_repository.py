"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

proveedores_repository.py

Repositorio para la tabla simi.proveedores.

Responsabilidades:

- Consultar proveedores.
- Crear proveedores.
- Actualizar la razón social.
- Verificar existencia por RFC o razón social.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No realiza normalización ni aplica reglas de negocio.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class ProveedoresRepository(BaseRepository):
    """
    Repositorio especializado para el catálogo de proveedores.
    """

    def __init__(self):
        super().__init__(
            table_name="proveedores",
            primary_key="id_proveedor",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_rfc(
        self,
        rfc: str,
        conn=None,
    ):
        """
        Busca un proveedor mediante su RFC.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.proveedores
            WHERE rfc = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(rfc,),
            conn=conn,
            fetchone=True,
        )

    def get_by_razon_social(
        self,
        razon_social: str,
        conn=None,
    ):
        """
        Busca un proveedor mediante su razón social.

        La comparación no distingue entre mayúsculas y minúsculas.
        El valor no se modifica ni normaliza dentro del Repository.

        Devuelve un solo registro o None.
        """

        query = """
            SELECT *
            FROM simi.proveedores
            WHERE UPPER(razon_social) = UPPER(%s)
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(razon_social,),
            conn=conn,
            fetchone=True,
        )

    def buscar(
        self,
        texto: str,
        conn=None,
    ):
        """
        Busca coincidencias por RFC o razón social.
        """

        parametro = f"%{texto}%"

        query = """
            SELECT *
            FROM simi.proveedores
            WHERE rfc ILIKE %s
               OR razon_social ILIKE %s
            ORDER BY
                razon_social,
                id_proveedor;
        """

        return self.custom_query(
            query=query,
            params=(
                parametro,
                parametro,
            ),
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # EXISTENCIA
    # ==========================================================

    def existe_rfc(
        self,
        rfc: str,
        conn=None,
    ) -> bool:
        """
        Indica si un RFC ya existe en el catálogo.
        """

        return self.exists_by_field(
            field_name="rfc",
            value=rfc,
            conn=conn,
        )

    def existe_razon_social(
        self,
        razon_social: str,
        conn=None,
    ) -> bool:
        """
        Indica si una razón social ya existe.

        La comparación no distingue entre mayúsculas y minúsculas.
        """

        query = """
            SELECT EXISTS (
                SELECT 1
                FROM simi.proveedores
                WHERE UPPER(razon_social) = UPPER(%s)
            ) AS existe;
        """

        result = self.custom_query(
            query=query,
            params=(razon_social,),
            conn=conn,
            fetchone=True,
        )

        if result is None:
            return False

        return bool(result.get("existe", False))

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_proveedor(
        self,
        rfc: str,
        razon_social: str,
        conn=None,
    ):
        """
        Crea un proveedor.

        Los datos deben llegar normalizados, validados y
        verificados desde la capa Service.
        """

        data = {
            "rfc": rfc,
            "razon_social": razon_social,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_razon_social(
        self,
        id_proveedor: int,
        razon_social: str,
        conn=None,
    ):
        """
        Actualiza la razón social de un proveedor.
        """

        return self.update(
            record_id=id_proveedor,
            data={
                "razon_social": razon_social,
            },
            conn=conn,
        )