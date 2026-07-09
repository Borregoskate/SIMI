from services.database_service import execute_query
from services.import_service import (
    validar_columnas_requeridas,
    limpiar_rfc,
    limpiar_razon_social
)


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


def cargar_catalogo_proveedores(df):
    columnas_requeridas = [
        "rfc",
        "razon_social"
    ]

    validar_columnas_requeridas(df, columnas_requeridas)

    procesados = 0
    insertados = 0
    actualizados = 0
    errores = []

    for index, row in df.iterrows():
        fila_excel = index + 2

        try:
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
                actualizados += 1
            else:
                insertar_proveedor(
                    rfc,
                    razon_social
                )
                insertados += 1

            procesados += 1

        except Exception as e:
            errores.append({
                "fila": fila_excel,
                "error": str(e)
            })

    return {
        "success": len(errores) == 0,
        "tabla": "proveedores",
        "procesados": procesados,
        "insertados": insertados,
        "actualizados": actualizados,
        "errores": errores
    }