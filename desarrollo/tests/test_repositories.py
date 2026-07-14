"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_repositories.py

Prueba de funcionamiento de los Repositories.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from repositories.procedimientos_repository import ProcedimientosRepository
from repositories.claves_repository import ClavesRepository
from repositories.proveedores_repository import ProveedoresRepository
from repositories.propuestas_repository import PropuestasRepository
from repositories.adjudicaciones_repository import AdjudicacionesRepository
from repositories.usuarios_repository import UsuariosRepository
from repositories.evaluaciones_tecnicas_repository import (
    EvaluacionesTecnicasRepository,
)


def main():

    print("=" * 60)
    print("VALIDANDO REPOSITORIES DE SIMI")
    print("=" * 60)

    repositorios = [
        ProcedimientosRepository(),
        ClavesRepository(),
        ProveedoresRepository(),
        PropuestasRepository(),
        EvaluacionesTecnicasRepository(),
        AdjudicacionesRepository(),
        UsuariosRepository()
    ]

    for repo in repositorios:

        print(
            f"✓ {repo.__class__.__name__}"
            f" -> Tabla: {repo.table_name}"
        )

    print()

    print("Todos los repositories fueron creados correctamente.")

    print("=" * 60)


if __name__ == "__main__":
    main()