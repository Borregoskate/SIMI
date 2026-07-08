"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_crud_repository.py

Prueba CRUD real para validar BaseRepository contra PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.claves_repository import ClavesRepository


def test_crud_claves():

    repo = ClavesRepository()

    print("=" * 60)
    print("PRUEBA CRUD - CLAVES")
    print("=" * 60)

    clave_prueba = "TEST.000.0000.00"

    # 1. Limpiar si ya existía una prueba anterior
    registro_existente = repo.get_by_clave(clave_prueba)

    if registro_existente:
        repo.delete(registro_existente["id_clave"])
        print("Registro previo de prueba eliminado.")

    # 2. INSERT
    nuevo = repo.crear_clave(
        clave=clave_prueba,
        descripcion="CLAVE DE PRUEBA SIMI",
        id_categoria=None
    )

    assert nuevo is not None
    assert nuevo["clave"] == clave_prueba

    print("✓ INSERT correcto")

    # 3. SELECT
    encontrado = repo.get_by_clave(clave_prueba)

    assert encontrado is not None
    assert encontrado["descripcion"] == "CLAVE DE PRUEBA SIMI"

    print("✓ SELECT correcto")

    # 4. UPDATE
    actualizado = repo.actualizar_descripcion(
        id_clave=encontrado["id_clave"],
        descripcion="CLAVE DE PRUEBA SIMI ACTUALIZADA"
    )

    assert actualizado is not None
    assert actualizado["descripcion"] == "CLAVE DE PRUEBA SIMI ACTUALIZADA"

    print("✓ UPDATE correcto")

    # 5. DELETE
    eliminado = repo.delete(actualizado["id_clave"])

    assert eliminado is not None
    assert eliminado["clave"] == clave_prueba

    print("✓ DELETE correcto")

    # 6. Confirmar eliminación
    verificacion = repo.get_by_clave(clave_prueba)

    assert verificacion is None

    print("✓ VERIFICACIÓN FINAL correcta")

    print("=" * 60)
    print("CRUD validado correctamente.")
    print("=" * 60)


if __name__ == "__main__":
    test_crud_claves()