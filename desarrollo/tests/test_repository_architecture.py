"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_repository_architecture.py

Pruebas estáticas para verificar la arquitectura autorizada
de la capa Repository.

Estas pruebas no requieren conexión a PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import ast
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
REPOSITORIES_DIR = BASE_DIR / "repositories"
SERVICES_DIR = BASE_DIR / "services"


# Repositories que forman parte del alcance actual del Paso 009.3.1.
REPOSITORIES_ACTIVOS = {
    "procedimientos_repository.py",
    "procedimiento_claves_repository.py",
    "procedimiento_fases_repository.py",
    "claves_repository.py",
    "proveedores_repository.py",
    "propuestas_repository.py",
    "usuarios_repository.py",
}


OPERACIONES_PROHIBIDAS = {
    "connect",
    "cursor",
    "commit",
    "rollback",
    "close",
}


NORMALIZACIONES_PROHIBIDAS = {
    "normalizar_texto",
    "normalizar_rfc",
    "normalizar_clave",
    "normalizar_razon_social",
    "normalizar_pais",
    "normalizar_numero",
    "normalizar_decimal",
    "normalizar_booleano",
}


def leer_codigo(ruta: Path) -> str:
    """
    Lee un archivo Python utilizando UTF-8.
    """

    return ruta.read_text(encoding="utf-8")


def obtener_arbol(ruta: Path) -> ast.AST:
    """
    Convierte un archivo Python en árbol sintáctico.
    """

    return ast.parse(
        leer_codigo(ruta),
        filename=str(ruta),
    )


def obtener_llamadas(arbol: ast.AST) -> set[str]:
    """
    Devuelve los nombres de las funciones y métodos llamados.
    """

    llamadas = set()

    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue

        if isinstance(nodo.func, ast.Name):
            llamadas.add(nodo.func.id)

        elif isinstance(nodo.func, ast.Attribute):
            llamadas.add(nodo.func.attr)

    return llamadas


def obtener_clases(arbol: ast.AST) -> list[ast.ClassDef]:
    """
    Devuelve todas las clases declaradas en el archivo.
    """

    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ClassDef)
    ]


def hereda_de_base_repository(clase: ast.ClassDef) -> bool:
    """
    Comprueba si una clase hereda directamente de BaseRepository.
    """

    for base in clase.bases:
        if isinstance(base, ast.Name):
            if base.id == "BaseRepository":
                return True

        if isinstance(base, ast.Attribute):
            if base.attr == "BaseRepository":
                return True

    return False


def test_transaction_service_no_existe():
    """
    transaction_service.py debe haber sido eliminado.
    """

    ruta = SERVICES_DIR / "transaction_service.py"

    assert not ruta.exists(), (
        "transaction_service.py todavía existe. "
        "Su funcionalidad debe residir en database_service.py."
    )


def test_repositories_activos_existen():
    """
    Comprueba que los repositories del alcance actual existan.
    """

    existentes = {
        ruta.name
        for ruta in REPOSITORIES_DIR.glob("*_repository.py")
    }

    faltantes = REPOSITORIES_ACTIVOS - existentes

    assert not faltantes, (
        f"Faltan repositories activos: {sorted(faltantes)}"
    )


def test_repositories_heredan_de_base_repository():
    """
    Todos los repositories especializados deben heredar
    de BaseRepository.
    """

    errores = []

    for nombre_archivo in sorted(REPOSITORIES_ACTIVOS):
        ruta = REPOSITORIES_DIR / nombre_archivo
        arbol = obtener_arbol(ruta)
        clases = obtener_clases(arbol)

        clases_repository = [
            clase
            for clase in clases
            if clase.name.endswith("Repository")
        ]

        if not clases_repository:
            errores.append(
                f"{nombre_archivo}: no contiene clase Repository."
            )
            continue

        for clase in clases_repository:
            if not hereda_de_base_repository(clase):
                errores.append(
                    f"{nombre_archivo}: "
                    f"{clase.name} no hereda de BaseRepository."
                )

    assert not errores, "\n".join(errores)


def test_repositories_no_administran_conexiones():
    """
    Los repositories no pueden crear cursores ni administrar
    commits, rollbacks, conexiones o cierres.
    """

    errores = []

    for nombre_archivo in sorted(REPOSITORIES_ACTIVOS):
        ruta = REPOSITORIES_DIR / nombre_archivo
        arbol = obtener_arbol(ruta)
        llamadas = obtener_llamadas(arbol)

        encontradas = llamadas & OPERACIONES_PROHIBIDAS

        if encontradas:
            errores.append(
                f"{nombre_archivo}: operaciones prohibidas "
                f"{sorted(encontradas)}"
            )

    assert not errores, "\n".join(errores)


def test_repositories_no_normalizan():
    """
    La normalización debe realizarse exclusivamente
    en la capa Service.
    """

    errores = []

    for nombre_archivo in sorted(REPOSITORIES_ACTIVOS):
        ruta = REPOSITORIES_DIR / nombre_archivo
        arbol = obtener_arbol(ruta)
        llamadas = obtener_llamadas(arbol)

        encontradas = llamadas & NORMALIZACIONES_PROHIBIDAS

        if encontradas:
            errores.append(
                f"{nombre_archivo}: normalización encontrada "
                f"{sorted(encontradas)}"
            )

    assert not errores, "\n".join(errores)


def test_repositories_no_importan_database_service():
    """
    Los repositories especializados deben acceder a la base
    exclusivamente mediante BaseRepository.
    """

    errores = []

    for nombre_archivo in sorted(REPOSITORIES_ACTIVOS):
        ruta = REPOSITORIES_DIR / nombre_archivo
        arbol = obtener_arbol(ruta)

        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom):
                modulo = nodo.module or ""

                if modulo == "services.database_service":
                    errores.append(
                        f"{nombre_archivo}: importa directamente "
                        "database_service."
                    )

            elif isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    if alias.name == "services.database_service":
                        errores.append(
                            f"{nombre_archivo}: importa directamente "
                            "database_service."
                        )

    assert not errores, "\n".join(errores)


def test_consultas_personalizadas_usan_schema_simi():
    """
    Las consultas SQL escritas en repositories deben usar
    nombres de tabla calificados con simi.
    """

    errores = []

    palabras_sql = (
        "FROM ",
        "INSERT INTO ",
        "UPDATE ",
        "DELETE FROM ",
        "JOIN ",
    )

    for nombre_archivo in sorted(REPOSITORIES_ACTIVOS):
        ruta = REPOSITORIES_DIR / nombre_archivo
        arbol = obtener_arbol(ruta)

        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Constant):
                continue

            if not isinstance(nodo.value, str):
                continue

            texto = nodo.value.strip()
            texto_mayusculas = texto.upper()

            if not any(
                palabra in texto_mayusculas
                for palabra in palabras_sql
            ):
                continue

            # Las consultas construidas por BaseRepository no están
            # dentro de estos archivos; toda consulta literal de un
            # Repository especializado debe contener simi.
            if "simi." not in texto.lower():
                errores.append(
                    f"{nombre_archivo}: consulta sin esquema simi:\n"
                    f"{texto[:160]}"
                )

    assert not errores, "\n\n".join(errores)