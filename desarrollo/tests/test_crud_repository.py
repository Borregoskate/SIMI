"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_crud_repository.py

Pruebas reales de BaseRepository y ClavesRepository
contra PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from repositories.claves_repository import ClavesRepository
from services.database_service import database_transaction


CLAVE_PRUEBA = "TEST.000.0000.00"


def limpiar_registro_prueba(repo, conn=None):
    """
    Elimina el registro temporal cuando existe.
    """

    registro = repo.get_by_clave(
        clave=CLAVE_PRUEBA,
        conn=conn,
    )

    if registro is not None:
        repo.delete(
            record_id=registro["id_clave"],
            conn=conn,
        )


def test_crud_claves():
    """
    Valida INSERT, SELECT, UPDATE y DELETE independientes.
    """

    repo = ClavesRepository()

    limpiar_registro_prueba(repo)

    try:
        nuevo = repo.crear_clave(
            clave=CLAVE_PRUEBA,
            descripcion="CLAVE DE PRUEBA SIMI",
            id_categoria=None,
        )

        assert nuevo is not None
        assert nuevo["clave"] == CLAVE_PRUEBA

        encontrado = repo.get_by_clave(CLAVE_PRUEBA)

        assert encontrado is not None
        assert encontrado["descripcion"] == (
            "CLAVE DE PRUEBA SIMI"
        )

        actualizado = repo.actualizar_descripcion(
            id_clave=encontrado["id_clave"],
            descripcion="CLAVE DE PRUEBA SIMI ACTUALIZADA",
        )

        assert actualizado is not None
        assert actualizado["descripcion"] == (
            "CLAVE DE PRUEBA SIMI ACTUALIZADA"
        )

        eliminado = repo.delete(
            actualizado["id_clave"]
        )

        assert eliminado is not None
        assert eliminado["clave"] == CLAVE_PRUEBA

        verificacion = repo.get_by_clave(CLAVE_PRUEBA)

        assert verificacion is None

    finally:
        limpiar_registro_prueba(repo)


def test_repository_dentro_de_transaccion():
    """
    Comprueba que el Repository utiliza una conexión externa
    administrada por database_transaction().
    """

    repo = ClavesRepository()

    limpiar_registro_prueba(repo)

    try:
        with database_transaction() as conn:
            nuevo = repo.crear_clave(
                clave=CLAVE_PRUEBA,
                descripcion="PRUEBA DE TRANSACCIÓN",
                id_categoria=None,
                conn=conn,
            )

            assert nuevo is not None

            encontrado = repo.get_by_clave(
                clave=CLAVE_PRUEBA,
                conn=conn,
            )

            assert encontrado is not None
            assert encontrado["descripcion"] == (
                "PRUEBA DE TRANSACCIÓN"
            )

            repo.delete(
                record_id=nuevo["id_clave"],
                conn=conn,
            )

        verificacion = repo.get_by_clave(CLAVE_PRUEBA)

        assert verificacion is None

    finally:
        limpiar_registro_prueba(repo)


def test_rollback_automatico():
    """
    Comprueba que database_transaction() revierte todas las
    operaciones cuando ocurre una excepción.
    """

    repo = ClavesRepository()

    limpiar_registro_prueba(repo)

    try:
        try:
            with database_transaction() as conn:
                repo.crear_clave(
                    clave=CLAVE_PRUEBA,
                    descripcion="PRUEBA DE ROLLBACK",
                    id_categoria=None,
                    conn=conn,
                )

                raise RuntimeError(
                    "Error intencional para probar rollback."
                )

        except RuntimeError as error:
            assert str(error) == (
                "Error intencional para probar rollback."
            )

        verificacion = repo.get_by_clave(CLAVE_PRUEBA)

        assert verificacion is None

    finally:
        limpiar_registro_prueba(repo)


if __name__ == "__main__":
    test_crud_claves()
    test_repository_dentro_de_transaccion()
    test_rollback_automatico()

    print("=" * 60)
    print("REPOSITORIES Y TRANSACCIONES VALIDADOS")
    print("=" * 60)