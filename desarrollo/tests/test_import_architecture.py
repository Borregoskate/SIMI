"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_import_architecture.py

Pruebas de homologación de imports y dependencias entre capas.

Objetivos:
- Evitar referencias a módulos eliminados.
- Evitar acceso directo a PostgreSQL fuera de database_service.py.
- Evitar que repositories dependan de services.
- Evitar imports desde rutas incorrectas.
- Verificar que todos los módulos principales puedan importarse.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

APP_FILE = PROJECT_ROOT / "app.py"
MODULES_DIR = PROJECT_ROOT / "modules"
SERVICES_DIR = PROJECT_ROOT / "services"
REPOSITORIES_DIR = PROJECT_ROOT / "repositories"
CORE_DIR = PROJECT_ROOT / "core"
CONFIG_DIR = PROJECT_ROOT / "config"
UTILS_DIR = PROJECT_ROOT / "utils"


# ============================================================
# MÓDULOS ELIMINADOS
# ============================================================

MODULOS_OBSOLETOS = {
    "services.transaction_service",
    "services.excel_service",
    "services.import_result",
    "services.invitacion_service",
    "services.adjudicaciones_repository",
    "services.evaluaciones_tecnicas_repository",
    "services.propuestas_repository",
    "modules.carga",
    "modules.carga_archivos",
}


# ============================================================
# DEPENDENCIAS DIRECTAS DE BASE DE DATOS PROHIBIDAS
# ============================================================

MODULOS_BASE_DATOS_DIRECTOS = {
    "psycopg2",
    "psycopg",
    "asyncpg",
    "sqlalchemy",
}


# ============================================================
# UTILIDADES
# ============================================================

def obtener_archivos_python():
    """
    Devuelve todos los archivos Python activos del proyecto.

    Excluye:
    - entorno virtual,
    - cachés,
    - archivos temporales.
    """

    archivos = []

    for archivo in PROJECT_ROOT.rglob("*.py"):
        partes = set(archivo.parts)

        if ".venv" in partes:
            continue

        if "venv" in partes:
            continue

        if "__pycache__" in partes:
            continue

        if ".pytest_cache" in partes:
            continue

        archivos.append(archivo)

    return archivos


def leer_ast(archivo: Path):
    """
    Lee un archivo Python y devuelve su árbol AST.
    """

    contenido = archivo.read_text(encoding="utf-8-sig")

    try:
        return ast.parse(contenido, filename=str(archivo))
    except SyntaxError as error:
        pytest.fail(
            f"Error de sintaxis en {archivo.relative_to(PROJECT_ROOT)}: "
            f"{error}"
        )


def extraer_imports(archivo: Path):
    """
    Obtiene todos los módulos importados por un archivo.
    """

    arbol = leer_ast(archivo)
    imports = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append(alias.name)

        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                imports.append(nodo.module)

    return imports


def modulo_coincide(importado: str, objetivo: str):
    """
    Comprueba si un import corresponde exactamente a un módulo
    o a alguno de sus submódulos.
    """

    return (
        importado == objetivo
        or importado.startswith(f"{objetivo}.")
    )


# ============================================================
# PRUEBA 1
# NO DEBEN EXISTIR IMPORTS DE MÓDULOS OBSOLETOS
# ============================================================

def test_no_existen_imports_obsoletos():
    errores = []

    for archivo in obtener_archivos_python():
        imports = extraer_imports(archivo)

        for importado in imports:
            for modulo_obsoleto in MODULOS_OBSOLETOS:
                if modulo_coincide(importado, modulo_obsoleto):
                    errores.append(
                        f"{archivo.relative_to(PROJECT_ROOT)} "
                        f"importa el módulo eliminado "
                        f"{modulo_obsoleto}"
                    )

    assert not errores, (
        "Se encontraron imports hacia módulos obsoletos:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 2
# LOS ARCHIVOS OBSOLETOS NO DEBEN EXISTIR
# ============================================================

def test_archivos_obsoletos_no_existen():
    rutas_obsoletas = {
        PROJECT_ROOT / "services" / "transaction_service.py",
        PROJECT_ROOT / "services" / "excel_service.py",
        PROJECT_ROOT / "services" / "import_result.py",
        PROJECT_ROOT / "services" / "invitacion_service.py",
        PROJECT_ROOT / "services" / "adjudicaciones_repository.py",
        PROJECT_ROOT / "services" / "evaluaciones_tecnicas_repository.py",
        PROJECT_ROOT / "services" / "propuestas_repository.py",
        PROJECT_ROOT / "modules" / "carga.py",
        PROJECT_ROOT / "modules" / "carga_archivos.py",
    }

    existentes = [
        ruta.relative_to(PROJECT_ROOT)
        for ruta in rutas_obsoletas
        if ruta.exists()
    ]

    assert not existentes, (
        "Todavía existen archivos considerados obsoletos:\n- "
        + "\n- ".join(str(ruta) for ruta in existentes)
    )


# ============================================================
# PRUEBA 3
# SOLO DATABASE_SERVICE PUEDE IMPORTAR EL DRIVER DE POSTGRESQL
# ============================================================

def test_solo_database_service_importa_driver_postgresql():
    errores = []

    archivo_autorizado = (
        SERVICES_DIR / "database_service.py"
    ).resolve()

    for archivo in obtener_archivos_python():
        if archivo.resolve() == archivo_autorizado:
            continue

        imports = extraer_imports(archivo)

        for importado in imports:
            modulo_raiz = importado.split(".")[0]

            if modulo_raiz in MODULOS_BASE_DATOS_DIRECTOS:
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa directamente {importado}"
                )

    assert not errores, (
        "Solo services/database_service.py puede importar "
        "el driver o framework de base de datos:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 4
# REPOSITORIES NO DEBEN IMPORTAR SERVICES
# ============================================================

def test_repositories_no_importan_services():
    """
    Los repositories especializados no deben importar services.

    Única excepción autorizada:
    BaseRepository puede importar services.database_service
    para delegar la ejecución SQL centralizada.
    """

    errores = []

    for archivo in REPOSITORIES_DIR.glob("*.py"):
        imports = extraer_imports(archivo)

        for importado in imports:
            if not modulo_coincide(importado, "services"):
                continue

            es_excepcion_autorizada = (
                archivo.name == "base_repository.py"
                and importado == "services.database_service"
            )

            if not es_excepcion_autorizada:
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa {importado}"
                )

    assert not errores, (
        "Los repositories especializados no deben depender "
        "de services:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 5
# REPOSITORIES NO DEBEN IMPORTAR MÓDULOS DE INTERFAZ
# ============================================================

def test_repositories_no_importan_modules():
    errores = []

    for archivo in REPOSITORIES_DIR.glob("*.py"):
        imports = extraer_imports(archivo)

        for importado in imports:
            if modulo_coincide(importado, "modules"):
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa {importado}"
                )

    assert not errores, (
        "Los repositories no deben depender de modules:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 6
# SERVICES NO DEBEN IMPORTAR MÓDULOS STREAMLIT
# ============================================================

def test_services_no_importan_streamlit():
    """
    Los services no deben depender de Streamlit.

    Única excepción:
    database_service.py puede usar st.secrets para obtener
    configuración en Streamlit Cloud.
    """

    errores = []

    for archivo in SERVICES_DIR.glob("*.py"):
        imports = extraer_imports(archivo)

        for importado in imports:
            if not modulo_coincide(importado, "streamlit"):
                continue

            es_excepcion_autorizada = (
                archivo.name == "database_service.py"
            )

            if not es_excepcion_autorizada:
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa {importado}"
                )

    assert not errores, (
        "Solo database_service.py puede importar Streamlit "
        "para consultar st.secrets:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 7
# REPOSITORIES NO DEBEN IMPORTAR STREAMLIT O PANDAS
# ============================================================

def test_repositories_no_importan_interfaz_o_dataframe():
    modulos_prohibidos = {
        "streamlit",
        "pandas",
        "plotly",
    }

    errores = []

    for archivo in REPOSITORIES_DIR.glob("*.py"):
        imports = extraer_imports(archivo)

        for importado in imports:
            modulo_raiz = importado.split(".")[0]

            if modulo_raiz in modulos_prohibidos:
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa {importado}"
                )

    assert not errores, (
        "Los repositories deben limitarse al acceso a datos "
        "y no importar interfaz o DataFrames:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 8
# DATABASE_SERVICE NO DEBE DEPENDER DE REPOSITORIES
# ============================================================

def test_database_service_no_importa_repositories():
    archivo = SERVICES_DIR / "database_service.py"

    assert archivo.exists(), (
        "No existe services/database_service.py"
    )

    imports = extraer_imports(archivo)

    imports_invalidos = [
        importado
        for importado in imports
        if modulo_coincide(importado, "repositories")
    ]

    assert not imports_invalidos, (
        "database_service.py no debe importar repositories: "
        + ", ".join(imports_invalidos)
    )


# ============================================================
# PRUEBA 9
# BASE_REPOSITORY SOLO IMPORTA DATABASE SERVICES
# ============================================================

def test_base_repository_solo_importa_database_service():
    """
    BaseRepository puede depender exclusivamente de
    services.database_service.
    """

    archivo = REPOSITORIES_DIR / "base_repository.py"

    assert archivo.exists(), (
        "No existe repositories/base_repository.py"
    )

    imports = extraer_imports(archivo)

    imports_services = [
        importado
        for importado in imports
        if modulo_coincide(importado, "services")
    ]

    assert imports_services == ["services.database_service"], (
        "BaseRepository solo puede importar "
        "services.database_service. Imports encontrados: "
        + ", ".join(imports_services)
    )


# ============================================================
# PRUEBA 10
# NO DEBEN EXISTIR IMPORTS DESDE CONFIG.DATABASE
# ============================================================

def test_no_existen_imports_desde_config_database():
    errores = []

    for archivo in obtener_archivos_python():
        imports = extraer_imports(archivo)

        for importado in imports:
            if modulo_coincide(importado, "config.database"):
                errores.append(
                    f"{archivo.relative_to(PROJECT_ROOT)} "
                    f"importa {importado}"
                )

    assert not errores, (
        "El acceso a la base de datos debe centralizarse en "
        "services/database_service.py. Se encontraron imports "
        "desde config.database:\n- "
        + "\n- ".join(errores)
    )


# ============================================================
# PRUEBA 11
# LOS MÓDULOS PRINCIPALES DEBEN PODER IMPORTARSE
# ============================================================

@pytest.mark.parametrize(
    "nombre_modulo",
    [
        "services.database_service",
        "services.normalizacion_service",
        "services.validacion_service",
        "services.import_service",
        "services.import_engine",
        "services.prevalidacion_universo_service",
        "services.prevalidacion_propuestas_service",
        "services.universo_import_service",
        "services.propuestas_import_service",
        "repositories.base_repository",
        "repositories.claves_repository",
        "repositories.procedimientos_repository",
        "repositories.proveedores_repository",
        "repositories.propuestas_repository",
        "repositories.evaluaciones_tecnicas_repository",
        "repositories.adjudicaciones_repository",
        "modules.carga_universo",
        "modules.carga_propuestas",
    ],
)
def test_modulos_principales_se_importan(nombre_modulo):
    try:
        importlib.import_module(nombre_modulo)
    except Exception as error:
        pytest.fail(
            f"No se pudo importar {nombre_modulo}: "
            f"{type(error).__name__}: {error}"
        )

# ============================================================
# PRUEBA 12
# SOLO DATABASE_SERVICE PUEDE ADMINISTRAR CONEXIONES
# ============================================================

def test_solo_database_service_administra_conexiones():
    """
    Ningún archivo fuera de database_service.py debe administrar
    directamente una conexión o cursor de base de datos.

    La prueba limita la detección a objetos cuyos nombres
    representan conexiones o cursores, evitando falsos positivos
    como archivo.close(), buffer.close() o excel.close().
    """

    archivo_autorizado = (
        SERVICES_DIR / "database_service.py"
    ).resolve()

    metodos_prohibidos = {
        "cursor",
        "commit",
        "rollback",
        "close",
    }

    nombres_objetos_bd = {
        "conn",
        "connection",
        "conexion",
        "con",
        "cursor",
        "cur",
    }

    errores = []

    for archivo in obtener_archivos_python():
        if archivo.resolve() == archivo_autorizado:
            continue

        arbol = leer_ast(archivo)

        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue

            funcion = nodo.func

            if not isinstance(funcion, ast.Attribute):
                continue

            if funcion.attr not in metodos_prohibidos:
                continue

            objeto = funcion.value

            if not isinstance(objeto, ast.Name):
                continue

            if objeto.id.lower() not in nombres_objetos_bd:
                continue

            errores.append(
                f"{archivo.relative_to(PROJECT_ROOT)} "
                f"ejecuta directamente "
                f"{objeto.id}.{funcion.attr}() "
                f"en la línea {nodo.lineno}"
            )

    assert not errores, (
        "Solo services/database_service.py puede administrar "
        "conexiones o transacciones directamente:\n- "
        + "\n- ".join(errores)
    )

# ============================================================
# PRUEBA 13
# SOLO DATABASE_SERVICE PUEDE MODIFICAR AUTOCOMMIT
# ============================================================

def test_solo_database_service_modifica_autocommit():
    """
    La configuración autocommit pertenece exclusivamente
    a database_service.py.
    """

    archivo_autorizado = (
        SERVICES_DIR / "database_service.py"
    ).resolve()

    errores = []

    for archivo in obtener_archivos_python():
        if archivo.resolve() == archivo_autorizado:
            continue

        arbol = leer_ast(archivo)

        for nodo in ast.walk(arbol):
            if not isinstance(
                nodo,
                (ast.Assign, ast.AnnAssign, ast.AugAssign),
            ):
                continue

            objetivos = []

            if isinstance(nodo, ast.Assign):
                objetivos.extend(nodo.targets)
            else:
                objetivos.append(nodo.target)

            for objetivo in objetivos:
                if (
                    isinstance(objetivo, ast.Attribute)
                    and objetivo.attr == "autocommit"
                ):
                    errores.append(
                        f"{archivo.relative_to(PROJECT_ROOT)} "
                        f"modifica autocommit en la línea "
                        f"{nodo.lineno}"
                    )

    assert not errores, (
        "Solo services/database_service.py puede modificar "
        "autocommit:\n- "
        + "\n- ".join(errores)
    )

# ============================================================
# PRUEBA 14
# IMPORT_ENGINE NO DEBE ADMINISTRAR TRANSACCIONES
# ============================================================

def test_import_engine_no_administra_transacciones():
    """
    import_engine.py debe procesar filas y resultados,
    pero no abrir, confirmar o revertir transacciones.
    """

    archivo = SERVICES_DIR / "import_engine.py"

    assert archivo.exists(), (
        "No existe services/import_engine.py"
    )

    arbol = leer_ast(archivo)

    elementos_prohibidos = {
        "commit",
        "rollback",
        "cursor",
        "close",
        "autocommit",
    }

    errores = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Attribute):
            if nodo.attr in elementos_prohibidos:
                errores.append(
                    f"import_engine.py utiliza "
                    f"'{nodo.attr}' en la línea {nodo.lineno}"
                )

    assert not errores, (
        "import_engine.py no debe administrar conexiones "
        "ni transacciones:\n- "
        + "\n- ".join(errores)
    )

