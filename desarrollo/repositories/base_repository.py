"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

base_repository.py

Repositorio base para acceso a datos.

Centraliza las operaciones comunes de persistencia y delega
completamente la administración de conexiones y transacciones
a services.database_service.

Este archivo no contiene:

- Lógica de negocio.
- Normalización.
- Validación.
- Apertura o cierre manual de conexiones.
- Commit o rollback manual.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from services.database_service import execute_query


class BaseRepository:
    """
    Clase base para todos los Repository de SIMI.

    Los Repository especializados deben:

    - Heredar de esta clase.
    - Enviar siempre conn cuando participen en una transacción.
    - Recibir datos previamente normalizados y validados.
    - No administrar conexiones directamente.
    """

    SCHEMA = "simi"

    def __init__(self, table_name: str, primary_key: str):
        if not table_name or not table_name.strip():
            raise ValueError(
                "El nombre de la tabla no puede estar vacío."
            )

        if not primary_key or not primary_key.strip():
            raise ValueError(
                "El nombre de la llave primaria no puede estar vacío."
            )

        self.table_name = table_name.strip()
        self.primary_key = primary_key.strip()

    # ==========================================================
    # INFORMACIÓN DE TABLA
    # ==========================================================

    @property
    def full_table_name(self):
        """
        Devuelve el nombre completamente calificado de la tabla.
        """

        return f"{self.SCHEMA}.{self.table_name}"

    def _full_table_name(self):
        """
        Alias temporal para conservar compatibilidad.

        Los Repository nuevos pueden utilizar la propiedad
        full_table_name.
        """

        return self.full_table_name

    # ==========================================================
    # CONSULTAS BÁSICAS
    # ==========================================================

    def get_all(self, conn=None):
        """
        Devuelve todos los registros de la tabla.
        """

        query = f"""
            SELECT *
            FROM {self.full_table_name}
            ORDER BY {self.primary_key};
        """

        return execute_query(
            query=query,
            conn=conn,
            fetchall=True,
        )

    def get_by_id(self, record_id, conn=None):
        """
        Busca un registro mediante su llave primaria.
        """

        query = f"""
            SELECT *
            FROM {self.full_table_name}
            WHERE {self.primary_key} = %s
            LIMIT 1;
        """

        return execute_query(
            query=query,
            params=(record_id,),
            conn=conn,
            fetchone=True,
        )

    def get_by_field(self, field_name: str, value, conn=None):
        """
        Devuelve los registros que coincidan con un campo.

        Este método debe utilizarse únicamente con nombres de campo
        definidos internamente por el sistema. Nunca debe recibir
        nombres de columna proporcionados directamente por el usuario.
        """

        self._validate_identifier(field_name)

        query = f"""
            SELECT *
            FROM {self.full_table_name}
            WHERE {field_name} = %s
            ORDER BY {self.primary_key};
        """

        return execute_query(
            query=query,
            params=(value,),
            conn=conn,
            fetchall=True,
        )

    def get_one_by_field(self, field_name: str, value, conn=None):
        """
        Devuelve el primer registro que coincida con un campo.
        """

        self._validate_identifier(field_name)

        query = f"""
            SELECT *
            FROM {self.full_table_name}
            WHERE {field_name} = %s
            ORDER BY {self.primary_key}
            LIMIT 1;
        """

        return execute_query(
            query=query,
            params=(value,),
            conn=conn,
            fetchone=True,
        )

    def exists_by_field(self, field_name: str, value, conn=None):
        """
        Indica si existe un registro con el valor solicitado.
        """

        self._validate_identifier(field_name)

        query = f"""
            SELECT EXISTS (
                SELECT 1
                FROM {self.full_table_name}
                WHERE {field_name} = %s
            ) AS existe;
        """

        result = execute_query(
            query=query,
            params=(value,),
            conn=conn,
            fetchone=True,
        )

        if result is None:
            return False

        return bool(result.get("existe", False))

    # ==========================================================
    # INSERT
    # ==========================================================

    def insert(self, data: dict, conn=None):
        """
        Inserta un registro y devuelve la fila creada.

        Los datos deben llegar normalizados y validados.
        """

        self._validate_data(data)

        columns = list(data.keys())

        for column in columns:
            self._validate_identifier(column)

        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        values = tuple(data[column] for column in columns)

        query = f"""
            INSERT INTO {self.full_table_name} (
                {column_names}
            )
            VALUES (
                {placeholders}
            )
            RETURNING *;
        """

        return execute_query(
            query=query,
            params=values,
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, record_id, data: dict, conn=None):
        """
        Actualiza un registro mediante su llave primaria.
        """

        self._validate_data(data)

        columns = list(data.keys())

        for column in columns:
            self._validate_identifier(column)

        set_clause = ", ".join(
            f"{column} = %s"
            for column in columns
        )

        values = tuple(
            data[column]
            for column in columns
        ) + (record_id,)

        query = f"""
            UPDATE {self.full_table_name}
            SET {set_clause}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        return execute_query(
            query=query,
            params=values,
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(self, record_id, conn=None):
        """
        Elimina un registro mediante su llave primaria.

        La autorización para eliminar debe validarse previamente
        en la capa de permisos o servicio correspondiente.
        """

        query = f"""
            DELETE FROM {self.full_table_name}
            WHERE {self.primary_key} = %s
            RETURNING *;
        """

        return execute_query(
            query=query,
            params=(record_id,),
            conn=conn,
            fetchone=True,
        )

    # ==========================================================
    # CONSULTAS PERSONALIZADAS
    # ==========================================================

    def custom_query(
        self,
        query: str,
        params=None,
        conn=None,
        fetch=False,
        fetchone=False,
        fetchall=False,
    ):
        """
        Ejecuta una consulta personalizada mediante el servicio
        central de base de datos.

        fetch se mantiene temporalmente para compatibilidad.
        """

        return execute_query(
            query=query,
            params=params,
            conn=conn,
            fetch=fetch,
            fetchone=fetchone,
            fetchall=fetchall,
        )

    # ==========================================================
    # VALIDACIONES INTERNAS DE INFRAESTRUCTURA
    # ==========================================================

    @staticmethod
    def _validate_data(data):
        """
        Verifica únicamente que los datos sean utilizables por
        la operación SQL.

        No normaliza ni aplica reglas de negocio.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Los datos deben proporcionarse como diccionario."
            )

        if not data:
            raise ValueError(
                "No se recibieron datos para ejecutar la operación."
            )

    @staticmethod
    def _validate_identifier(identifier):
        """
        Verifica que un identificador SQL interno solo contenga
        caracteres seguros.

        Esto protege los métodos genéricos que construyen nombres
        de columnas dinámicamente.
        """

        if not isinstance(identifier, str):
            raise TypeError(
                "El identificador SQL debe ser una cadena de texto."
            )

        if not identifier:
            raise ValueError(
                "El identificador SQL no puede estar vacío."
            )

        normalized_identifier = identifier.replace("_", "")

        if not normalized_identifier.isalnum():
            raise ValueError(
                f"Identificador SQL no permitido: {identifier}"
            )