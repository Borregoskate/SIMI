import pandas as pd


def normalizar_nombre_columna(columna):
    return (
        str(columna)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace(" ", "_")
    )


def normalizar_dataframe(df):
    df = df.copy()
    df.columns = [normalizar_nombre_columna(col) for col in df.columns]
    return df


def validar_dataframe_no_vacio(df):
    if df is None or df.empty:
        raise ValueError("El archivo no contiene registros para importar.")


def validar_columnas_requeridas(df, columnas_requeridas):
    validar_dataframe_no_vacio(df)

    columnas_df = list(df.columns)

    columnas_faltantes = [
        col for col in columnas_requeridas
        if col not in columnas_df
    ]

    if columnas_faltantes:
        raise ValueError(
            "El archivo debe contener las columnas: "
            + ", ".join(columnas_faltantes)
        )


def limpiar_texto(valor):
    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    return valor


def limpiar_rfc(valor):
    valor = limpiar_texto(valor)

    if not valor:
        return None

    return valor.upper()[:13]


def limpiar_clave(valor):
    valor = limpiar_texto(valor)

    if not valor:
        return None

    return valor


def limpiar_razon_social(valor):
    valor = limpiar_texto(valor)

    if not valor:
        return None

    return valor.upper()[:255]


def limpiar_numero(valor):
    if pd.isna(valor):
        return None

    try:
        return float(valor)
    except Exception:
        return None


def leer_excel(file, hoja=None):
    if hoja:
        df = pd.read_excel(file, sheet_name=hoja)
    else:
        df = pd.read_excel(file)

    return normalizar_dataframe(df)