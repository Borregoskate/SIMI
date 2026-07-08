"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

usuarios_repository.py

Repositorio para la tabla usuarios.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class UsuariosRepository(BaseRepository):
    """
    Repositorio para usuarios del sistema SIMI.
    """

    def __init__(self):
        super().__init__(
            table_name="usuarios",
            primary_key="id_usuario"
        )

    def get_by_email(self, email: str):
        query = """
            SELECT *
            FROM usuarios
            WHERE email = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(email,),
            fetch=True
        )

        return result[0] if result else None

    def get_by_username(self, username: str):
        query = """
            SELECT *
            FROM usuarios
            WHERE username = %s
            LIMIT 1;
        """

        result = self.custom_query(
            query,
            params=(username,),
            fetch=True
        )

        return result[0] if result else None

    def get_activos(self):
        query = """
            SELECT *
            FROM usuarios
            WHERE activo = TRUE
            ORDER BY nombre_completo;
        """

        return self.custom_query(query, fetch=True)

    def crear_usuario(
        self,
        username: str,
        email: str,
        nombre_completo: str,
        password_hash: str,
        rol: str,
        activo: bool = True
    ):
        data = {
            "username": username,
            "email": email,
            "nombre_completo": nombre_completo,
            "password_hash": password_hash,
            "rol": rol,
            "activo": activo
        }

        return self.insert(data)

    def desactivar_usuario(self, id_usuario: int):
        return self.update(
            record_id=id_usuario,
            data={"activo": False}
        )

    def actualizar_password(
        self,
        id_usuario: int,
        password_hash: str
    ):
        return self.update(
            record_id=id_usuario,
            data={"password_hash": password_hash}
        )

    def actualizar_rol(
        self,
        id_usuario: int,
        rol: str
    ):
        return self.update(
            record_id=id_usuario,
            data={"rol": rol}
        )