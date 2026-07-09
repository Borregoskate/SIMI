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


def obtener_claves_catalogo(conn, claves):
    """
    Consulta en base de datos las claves recibidas.

    Retorna un diccionario con esta estructura:

    {
        "010.000.0000.00": {
            "id_clave": 1,
            "clave": "010.000.0000.00",
            "descripcion": "DESCRIPCION"
        }
    }
    """

    if not claves:
        return {}

    claves_limpias = list(set([str(c).strip() for c in claves if c]))

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

    for registro in registros:
        id_clave, clave, descripcion = registro

        catalogo[str(clave).strip()] = {
            "id_clave": id_clave,
            "clave": str(clave).strip(),
            "descripcion": str(descripcion).strip().upper() if descripcion else ""
        }

    return catalogo


def normalizar_texto_bd(valor):
    """
    Normaliza texto para comparación contra base de datos.
    """

    if valor is None:
        return ""

    return str(valor).strip().upper()


def validar_claves_contra_catalogo(df, conn):
    """
    Valida las claves del DataFrame contra el catálogo de claves.

    Reglas:
    - Si la clave existe, agrega id_clave.
    - Si la clave no existe, la marca como nueva.
    - Si la clave existe pero la descripción no coincide, genera error.
    - No inserta datos.
    """

    errores = []

    df_validado = df.copy()

    df_validado["ID_CLAVE"] = None
    df_validado["ES_NUEVA"] = False

    claves_archivo = df_validado["CLAVE"].dropna().astype(str).str.strip().tolist()

    catalogo_claves = obtener_claves_catalogo(conn, claves_archivo)

    for index, fila in df_validado.iterrows():
        numero_fila = index + 2

        clave = str(fila.get("CLAVE", "")).strip()
        descripcion_archivo = normalizar_texto_bd(fila.get("DESCRIPCION", ""))

        if not clave:
            continue

        clave_bd = catalogo_claves.get(clave)

        if clave_bd:
            df_validado.at[index, "ID_CLAVE"] = clave_bd["id_clave"]
            df_validado.at[index, "ES_NUEVA"] = False

            descripcion_bd = normalizar_texto_bd(clave_bd["descripcion"])

            if descripcion_archivo != descripcion_bd:
                errores.append({
                    "fila": numero_fila,
                    "columna": "DESCRIPCION",
                    "valor": fila.get("DESCRIPCION", ""),
                    "error": (
                        "La clave ya existe en el catálogo, "
                        "pero la descripción no coincide con la registrada en base de datos."
                    ),
                    "descripcion_bd": descripcion_bd
                })

        else:
            df_validado.at[index, "ID_CLAVE"] = None
            df_validado.at[index, "ES_NUEVA"] = True

    resumen = {
        "total_registros": len(df_validado),
        "claves_existentes": int((df_validado["ES_NUEVA"] == False).sum()),
        "claves_nuevas": int((df_validado["ES_NUEVA"] == True).sum()),
        "errores": len(errores),
    }

    return {
        "success": len(errores) == 0,
        "df": df_validado,
        "errores": errores,
        "resumen": resumen
    }


def validar_procedimiento_existente(conn, numero_procedimiento):
    """
    Valida si un procedimiento ya existe en base de datos.

    Retorna:
    {
        "existe": True/False,
        "id_procedimiento": valor o None
    }
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