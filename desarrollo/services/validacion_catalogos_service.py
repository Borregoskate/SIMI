"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

validacion_catalogos_service.py

Servicio reutilizable de prevalidación contra base de datos.

Este servicio NO inserta datos.
Solo consulta catálogos y valida consistencia contra PostgreSQL.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""


def normalizar_texto(valor):
    """
    Normaliza textos para comparación.
    """

    if valor is None:
        return ""

    return str(valor).strip().upper()


def obtener_claves_catalogo(conn, claves):
    """
    Consulta claves existentes en el catálogo simi.claves.
    """

    if not claves:
        return {}

    claves_limpias = list({
        str(clave).strip()
        for clave in claves
        if clave is not None and str(clave).strip() and str(clave).strip().lower() != "nan"
    })

    if not claves_limpias:
        return {}

    query = """
        SELECT
            id_clave,
            clave,
            descripcion
        FROM simi.claves
        WHERE clave = ANY(%s);
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (claves_limpias,))
        registros = cursor.fetchall()

    catalogo = {}

    for id_clave, clave, descripcion in registros:
        catalogo[str(clave).strip()] = {
            "id_clave": id_clave,
            "clave": str(clave).strip(),
            "descripcion": normalizar_texto(descripcion)
        }

    return catalogo


def validar_procedimiento_existente(conn, numero_procedimiento):
    """
    Valida si el procedimiento ya existe en simi.procedimientos.
    """

    query = """
        SELECT
            id_procedimiento,
            numero_procedimiento
        FROM simi.procedimientos
        WHERE UPPER(TRIM(numero_procedimiento)) = UPPER(TRIM(%s))
        LIMIT 1;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (numero_procedimiento,))
        registro = cursor.fetchone()

    if registro:
        return {
            "existe": True,
            "id_procedimiento": registro[0],
            "numero_procedimiento": registro[1]
        }

    return {
        "existe": False,
        "id_procedimiento": None,
        "numero_procedimiento": None
    }


def validar_claves_contra_catalogo(df, conn):
    """
    Valida claves del archivo contra simi.claves.

    Reglas:
    - Si la clave existe, agrega ID_CLAVE.
    - Si la clave no existe, marca ES_NUEVA = True.
    - Si existe pero la descripción no coincide, genera error.
    """

    errores = []

    df_validado = df.copy()

    df_validado["ID_CLAVE"] = None
    df_validado["ES_NUEVA"] = False

    claves_archivo = (
        df_validado["CLAVE"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    catalogo_claves = obtener_claves_catalogo(conn, claves_archivo)

    for index, fila in df_validado.iterrows():
        fila_excel = index + 8

        clave = str(fila.get("CLAVE", "")).strip()
        descripcion_archivo = normalizar_texto(fila.get("DESCRIPCION", ""))

        if not clave or clave.lower() == "nan":
            continue

        clave_bd = catalogo_claves.get(clave)

        if clave_bd:
            df_validado.at[index, "ID_CLAVE"] = clave_bd["id_clave"]
            df_validado.at[index, "ES_NUEVA"] = False

            descripcion_bd = normalizar_texto(clave_bd["descripcion"])

            if descripcion_archivo != descripcion_bd:
                errores.append(
                    f"Fila {fila_excel}: la clave '{clave}' ya existe en base de datos, "
                    f"pero la descripción no coincide. "
                    f"Archivo: '{descripcion_archivo}' | BD: '{descripcion_bd}'."
                )

        else:
            df_validado.at[index, "ID_CLAVE"] = None
            df_validado.at[index, "ES_NUEVA"] = True

    total_nuevas = int((df_validado["ES_NUEVA"] == True).sum())
    total_existentes = int((df_validado["ES_NUEVA"] == False).sum())

    resumen = {
        "total_registros": len(df_validado),
        "claves_existentes": total_existentes,
        "claves_nuevas": total_nuevas,
        "errores": len(errores),
    }

    return {
        "success": len(errores) == 0,
        "df": df_validado,
        "errores": errores,
        "resumen": resumen
    }