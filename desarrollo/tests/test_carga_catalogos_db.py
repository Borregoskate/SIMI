import pandas as pd

from services.catalogos_service import cargar_catalogo_claves
from services.proveedores_service import cargar_catalogo_proveedores


def test_carga_catalogo_claves():
    df = pd.read_excel("data/catalogo_claves.xlsx")
    df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    resultado = cargar_catalogo_claves(df)
    print(resultado)


def test_carga_catalogo_proveedores():
    df = pd.read_excel("data/catalogo_proveedores.xlsx")
    df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    resultado = cargar_catalogo_proveedores(df)
    print(resultado)


if __name__ == "__main__":
    print("Probando carga de claves...")
    test_carga_catalogo_claves()

    print("\nProbando carga de proveedores...")
    test_carga_catalogo_proveedores()