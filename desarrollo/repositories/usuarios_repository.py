"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

usuarios_repository.py

Repositorio para la tabla simi.usuarios.

Responsabilidades:

- Consultar usuarios.
- Crear usuarios.
- Activar o desactivar usuarios.
- Actualizar contraseña y rol.
- Registrar el último inicio de sesión.
- Delegar toda ejecución SQL a BaseRepository.

Este Repository recibe datos previamente normalizados,
validados y verificados por la capa Service.

No aplica permisos, normalización ni reglas de autenticación.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.base_repository import BaseRepository


class UsuariosRepository(BaseRepository):
    """
    Repositorio especializado para usuarios del sistema SIMI.
    """

    def __init__(self):
        super().__init__(
            table_name="usuarios",
            primary_key="id_usuario",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def get_by_email(
        self,
        email: str,
        conn=None,
    ):
        """
        Busca un usuario mediante su correo electrónico.

        Devuelve un registro o None.
        """

        query = """
            SELECT *
            FROM simi.usuarios
            WHERE email = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(email,),
            conn=conn,
            fetchone=True,
        )

    def get_by_username(
        self,
        username: str,
        conn=None,
    ):
        """
        Busca un usuario mediante su nombre de usuario.

        Devuelve un registro o None.
        """

        query = """
            SELECT *
            FROM simi.usuarios
            WHERE username = %s
            LIMIT 1;
        """

        return self.custom_query(
            query=query,
            params=(username,),
            conn=conn,
            fetchone=True,
        )

    def get_activos(self, conn=None):
        """
        Devuelve todos los usuarios activos.
        """

        query = """
            SELECT *
            FROM simi.usuarios
            WHERE activo = TRUE
            ORDER BY
                nombre_completo,
                id_usuario;
        """

        return self.custom_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    # ==========================================================
    # EXISTENCIA
    # ==========================================================

    def existe_email(
        self,
        email: str,
        conn=None,
    ) -> bool:
        """
        Indica si ya existe un usuario con el correo recibido.
        """

        return self.exists_by_field(
            field_name="email",
            value=email,
            conn=conn,
        )

    def existe_username(
        self,
        username: str,
        conn=None,
    ) -> bool:
        """
        Indica si ya existe el nombre de usuario recibido.
        """

        return self.exists_by_field(
            field_name="username",
            value=username,
            conn=conn,
        )

    # ==========================================================
    # CREACIÓN
    # ==========================================================

    def crear_usuario(
        self,
        username: str,
        email: str,
        nombre_completo: str,
        password_hash: str,
        rol: str,
        activo: bool = True,
        conn=None,
    ):
        """
        Crea un usuario.

        La contraseña debe llegar previamente convertida en hash.
        El Repository nunca recibe ni procesa contraseñas abiertas.
        """

        data = {
            "username": username,
            "email": email,
            "nombre_completo": nombre_completo,
            "password_hash": password_hash,
            "rol": rol,
            "activo": activo,
        }

        return self.insert(
            data=data,
            conn=conn,
        )

    # ==========================================================
    # ESTADO
    # ==========================================================

    def activar_usuario(
        self,
        id_usuario: int,
        conn=None,
    ):
        """
        Activa un usuario.
        """

        return self.update(
            record_id=id_usuario,
            data={"activo": True},
            conn=conn,
        )

    def desactivar_usuario(
        self,
        id_usuario: int,
        conn=None,
    ):
        """
        Desactiva un usuario sin eliminarlo físicamente.
        """

        return self.update(
            record_id=id_usuario,
            data={"activo": False},
            conn=conn,
        )

    # ==========================================================
    # ACTUALIZACIONES
    # ==========================================================

    def actualizar_password(
        self,
        id_usuario: int,
        password_hash: str,
        conn=None,
    ):
        """
        Actualiza el hash de contraseña de un usuario.
        """

        return self.update(
            record_id=id_usuario,
            data={"password_hash": password_hash},
            conn=conn,
        )

    def actualizar_rol(
        self,
        id_usuario: int,
        rol: str,
        conn=None,
    ):
        """
        Actualiza el rol de un usuario.

        La autorización y validación del rol pertenecen
        a la capa Service.
        """

        return self.update(
            record_id=id_usuario,
            data={"rol": rol},
            conn=conn,
        )

    def registrar_ultimo_login(
        self,
        id_usuario: int,
        conn=None,
    ):
        """
        Registra automáticamente la fecha del último inicio
        de sesión mediante PostgreSQL.
        """

        query = """
            UPDATE simi.usuarios
            SET fecha_ultimo_login = CURRENT_TIMESTAMP
            WHERE id_usuario = %s
            RETURNING *;
        """

        return self.custom_query(
            query=query,
            params=(id_usuario,),
            conn=conn,
            fetchone=True,
        )