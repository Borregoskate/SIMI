from services.database_service import execute_query
from services.import_service import (
    validar_columnas_requeridas,
    limpiar_texto,
    limpiar_clave
)


def obtener_categoria_por_nombre(nombre_categoria):
    query = """
        SELECT id_categoria
        FROM simi.cat_categorias_clave
        WHERE UPPER(nombre_categoria) = UPPER(%s)
        LIMIT 1;
    """

    return execute_query(query, (nombre_categoria,), fetchone=True)


def obtener_clave_por_clave(clave):
    query = """
        SELECT id_clave
        FROM simi.claves
        WHERE clave = %s
        LIMIT 1;
    """

    return execute_query(query, (clave,), fetchone=True)


def insertar_clave(clave, descripcion, id_categoria):
    query = """
        INSERT INTO simi.claves (
            clave,
            descripcion,
            id_categoria
        )
        VALUES (%s, %s, %s)
        RETURNING id_clave;
    """

    return execute_query(
        query,
        (clave, descripcion, id_categoria),
        fetchone=True
    )


def actualizar_clave(id_clave, descripcion, id_categoria):
    query = """
        UPDATE simi.claves
        SET
            descripcion = %s,
            id_categoria = %s
        WHERE id_clave = %s;
    """

    execute_query(query, (descripcion, id_categoria, id_clave))


def cargar_catalogo_claves(df):
    columnas_requeridas = [
        "clave",
        "descripcion",
        "categoria"
    ]

    validar_columnas_requeridas(df, columnas_requeridas)

    procesados = 0
    insertados = 0
    actualizados = 0
    errores = []

    for index, row in df.iterrows():
        fila_excel = index + 2

        try:
            clave = limpiar_clave(row.get("clave"))
            descripcion = limpiar_texto(row.get("descripcion"))
            categoria = limpiar_texto(row.get("categoria"))

            if not clave:
                raise ValueError("La clave es obligatoria")

            if not descripcion:
                raise ValueError("La descripción es obligatoria")

            if not categoria:
                raise ValueError("La categoría es obligatoria")

            categoria_db = obtener_categoria_por_nombre(categoria)

            if not categoria_db:
                raise ValueError(f"La categoría no existe: {categoria}")

            id_categoria = categoria_db["id_categoria"]

            clave_db = obtener_clave_por_clave(clave)

            if clave_db:
                actualizar_clave(
                    clave_db["id_clave"],
                    descripcion,
                    id_categoria
                )
                actualizados += 1
            else:
                insertar_clave(
                    clave,
                    descripcion,
                    id_categoria
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
        "tabla": "claves",
        "procesados": procesados,
        "insertados": insertados,
        "actualizados": actualizados,
        "errores": errores
    }