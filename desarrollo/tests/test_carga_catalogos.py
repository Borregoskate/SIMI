"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_carga_catalogos.py

Prueba de carga inicial de catálogos maestros:
- cat_categorias_clave
- claves
- proveedores

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# ==========================================================
# RUTA BASE DEL PROYECTO
# ==========================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.append(BASE_DIR)

from modules.catalog_manager import CatalogManager


# ==========================================================
# CARGA DE VARIABLES DE ENTORNO
# ==========================================================

load_dotenv()


# ==========================================================
# CONFIGURACIÓN DE CONEXIÓN
# ==========================================================

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# ==========================================================
# ARCHIVOS DE CATÁLOGOS
# ==========================================================

ARCHIVO_CATEGORIAS = os.path.join(
    BASE_DIR,
    "catalogos",
    "categorias.xlsx"
)

ARCHIVO_CLAVES = os.path.join(
    BASE_DIR,
    "catalogos",
    "claves.xlsx"
)

ARCHIVO_PROVEEDORES = os.path.join(
    BASE_DIR,
    "catalogos",
    "proveedores.xlsx"
)


# ==========================================================
# USUARIO DE PRUEBA
# ==========================================================
# Debe existir previamente en simi.usuarios

ID_USUARIO = 1
USER_ROLE = "ADMINISTRADOR"


# ==========================================================
# FUNCIÓN DE CONEXIÓN
# ==========================================================

def crear_conexion():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ==========================================================
# VALIDACIONES PREVIAS
# ==========================================================

def validar_archivo_existe(ruta_archivo):
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(
            f"No existe el archivo requerido: {ruta_archivo}"
        )


def validar_usuario_existe(connection, id_usuario):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_usuario, username, rol, activo
            FROM simi.usuarios
            WHERE id_usuario = %s;
            """,
            (id_usuario,)
        )

        usuario = cursor.fetchone()

        if usuario is None:
            raise ValueError(
                f"No existe el usuario con id_usuario = {id_usuario}"
            )

        id_usuario_db, username, rol, activo = usuario

        if not activo:
            raise ValueError(
                f"El usuario {username} existe, pero está inactivo."
            )

        if rol not in ("ADMINISTRADOR_MAESTRO", "ADMINISTRADOR"):
            raise PermissionError(
                f"El usuario {username} tiene rol {rol}, "
                "pero no puede cargar catálogos."
            )

        print("Usuario autorizado:")
        print(f"  ID: {id_usuario_db}")
        print(f"  Username: {username}")
        print(f"  Rol: {rol}")


# ==========================================================
# PRUEBA DE CARGA
# ==========================================================

def ejecutar_carga_catalogos():
    print("==================================================")
    print("SIMI - Prueba de carga de catálogos")
    print("==================================================")

    validar_archivo_existe(ARCHIVO_CATEGORIAS)
    validar_archivo_existe(ARCHIVO_CLAVES)
    validar_archivo_existe(ARCHIVO_PROVEEDORES)

    connection = crear_conexion()

    try:
        validar_usuario_existe(connection, ID_USUARIO)

        catalog_manager = CatalogManager(connection)

        print("\nCargando catálogo de categorías...")
        resultado_categorias = catalog_manager.cargar_categorias(
            archivo=ARCHIVO_CATEGORIAS,
            id_usuario=ID_USUARIO,
            user_role=USER_ROLE
        )
        print(resultado_categorias)

        print("\nCargando catálogo de claves...")
        resultado_claves = catalog_manager.cargar_claves(
            archivo=ARCHIVO_CLAVES,
            id_usuario=ID_USUARIO,
            user_role=USER_ROLE
        )
        print(resultado_claves)

        print("\nCargando catálogo de proveedores...")
        resultado_proveedores = catalog_manager.cargar_proveedores(
            archivo=ARCHIVO_PROVEEDORES,
            id_usuario=ID_USUARIO,
            user_role=USER_ROLE
        )
        print(resultado_proveedores)

        print("\nCarga de catálogos finalizada correctamente.")

    except Exception as error:
        print("\nERROR DURANTE LA CARGA DE CATÁLOGOS")
        print(str(error))

    finally:
        connection.close()
        print("\nConexión cerrada.")


# ==========================================================
# EJECUCIÓN
# ==========================================================

if __name__ == "__main__":
    ejecutar_carga_catalogos()