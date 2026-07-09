"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

proveedores_service.py

Servicio para carga y mantenimiento de proveedores.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from services.database_service import execute_query
from services.import_service import (
    limpiar_rfc,
    limpiar_razon_social
)
from services.import_engine import procesar_dataframe


def obtener_proveedor_por_rfc(rfc):
    query = """
        SELECT id_proveedor
        FROM simi.proveedores
        WHERE rfc = %s
        LIMIT 1;
    """

    return execute_query(query, (rfc,), fetchone=True)


def insertar_proveedor(rfc, razon_social):
    query = """
        INSERT INTO simi.proveedores (
            rfc,
            razon_social
        )
        VALUES (%s, %s)
        RETURNING id_proveedor;
    """

    return execute_query(
        query,
        (rfc, razon_social),
        fetchone=True
    )


def actualizar_proveedor(id_proveedor, razon_social):
    query = """
        UPDATE simi.proveedores
        SET razon_social = %s
        WHERE id_proveedor = %s;
    """

    execute_query(query, (razon_social, id_proveedor))


def procesar_fila_proveedor(row):
    rfc = limpiar_rfc(row.get("rfc"))
    razon_social = limpiar_razon_social(row.get("razon_social"))

    if not rfc:
        raise ValueError("El RFC es obligatorio")

    if not razon_social:
        raise ValueError("La razón social es obligatoria")

    proveedor_db = obtener_proveedor_por_rfc(rfc)

    if proveedor_db:
        actualizar_proveedor(
            proveedor_db["id_proveedor"],
            razon_social
        )

        return {
            "accion": "actualizado"
        }

    insertar_proveedor(
        rfc,
        razon_social
    )

    return {
        "accion": "insertado"
    }


def cargar_catalogo_proveedores(df):
    columnas_requeridas = [
        "rfc",
        "razon_social"
    ]

    return procesar_dataframe(
        df=df,
        tabla="proveedores",
        columnas_requeridas=columnas_requeridas,
        funcion_procesar_fila=procesar_fila_proveedor
    )