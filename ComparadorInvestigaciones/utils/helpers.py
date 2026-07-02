"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

helpers.py

Funciones auxiliares reutilizables en todo el proyecto.

Versión: 1.0.0
Autor: Jorge Saavedra
==============================================================
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


# ==========================================================
# TEXTO
# ==========================================================

def limpiar_texto(texto: Any) -> str:
    """
    Convierte cualquier valor en texto limpio.

    - Elimina espacios al inicio y final.
    - Sustituye múltiples espacios por uno solo.
    - Convierte None en cadena vacía.
    """

    if texto is None:
        return ""

    texto = str(texto)

    texto = texto.strip()

    texto = re.sub(r"\s+", " ", texto)

    return texto


# ----------------------------------------------------------

def quitar_acentos(texto: Any) -> str:
    """
    Elimina acentos y caracteres especiales.

    Ejemplo:
        MÉXICO -> MEXICO
    """

    texto = limpiar_texto(texto)

    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


# ----------------------------------------------------------

def normalizar_texto(texto: Any) -> str:
    """
    Convierte texto a formato estándar.

    - Sin acentos
    - Mayúsculas
    - Sin espacios dobles
    """

    texto = quitar_acentos(texto)

    return texto.upper()


# ----------------------------------------------------------

def texto_vacio(valor: Any) -> bool:
    """
    Indica si un valor debe considerarse vacío.
    """

    if valor is None:
        return True

    texto = limpiar_texto(valor)

    if texto == "":
        return True

    if texto.upper() == "NAN":
        return True

    return False


# ==========================================================
# RFC
# ==========================================================

def normalizar_rfc(rfc: Any) -> str:
    """
    Limpia un RFC.

    Elimina espacios y convierte a mayúsculas.
    """

    rfc = normalizar_texto(rfc)

    rfc = rfc.replace(" ", "")

    return rfc


# ==========================================================
# PROVEEDORES
# ==========================================================

def normalizar_proveedor(nombre: Any) -> str:
    """
    Normaliza el nombre de un proveedor.
    """

    nombre = normalizar_texto(nombre)

    nombre = nombre.replace(",", "")

    nombre = nombre.replace(".", "")

    return nombre


# ==========================================================
# CLAVES
# ==========================================================

def normalizar_clave(clave: Any) -> str:
    """
    Convierte la clave en texto estándar.
    """

    clave = limpiar_texto(clave)

    return clave.upper()


# ==========================================================
# NUMÉRICOS
# ==========================================================

def convertir_float(valor: Any) -> float:
    """
    Convierte cualquier valor a float.

    Si ocurre un error devuelve 0.
    """

    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    valor = str(valor)

    valor = valor.replace(",", "")

    valor = valor.replace("$", "")

    valor = valor.strip()

    try:

        return float(valor)

    except Exception:

        return 0.0


# ----------------------------------------------------------

def convertir_int(valor: Any) -> int:
    """
    Convierte cualquier valor a entero.
    """

    return int(convertir_float(valor))


# ----------------------------------------------------------

def es_numero(valor: Any) -> bool:
    """
    Devuelve True si puede convertirse a número.
    """

    try:

        float(str(valor).replace(",", ""))

        return True

    except Exception:

        return False


# ==========================================================
# MONEDA
# ==========================================================

def formatear_moneda(valor: Any) -> str:
    """
    Da formato de moneda.

    Ejemplo:

        1250.5

        ->

        $1,250.50
    """

    return "${:,.2f}".format(convertir_float(valor))


# ----------------------------------------------------------

def formatear_porcentaje(valor: float) -> str:
    """
    Devuelve porcentaje con dos decimales.
    """

    return "{:.2f}%".format(valor)


# ==========================================================
# ARCHIVOS
# ==========================================================

def obtener_nombre_archivo(ruta: str) -> str:
    """
    Devuelve únicamente el nombre del archivo.
    """

    return Path(ruta).name


# ----------------------------------------------------------

def obtener_extension(ruta: str) -> str:
    """
    Obtiene la extensión del archivo.
    """

    return Path(ruta).suffix.lower()


# ==========================================================
# DATAFRAME
# ==========================================================

def dataframe_vacio(df: pd.DataFrame) -> bool:
    """
    Comprueba si un DataFrame está vacío.
    """

    return df is None or df.empty


# ----------------------------------------------------------

def convertir_columnas_texto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte todas las columnas tipo objeto a texto limpio.
    """

    for columna in df.columns:

        if df[columna].dtype == object:

            df[columna] = df[columna].astype(str)

            df[columna] = df[columna].apply(limpiar_texto)

    return df


# ==========================================================
# INVESTIGACIONES
# ==========================================================

def extraer_numero_investigacion(nombre_archivo: str) -> str:
    """
    Extrae el número de investigación del nombre del archivo.

    Ejemplos

    IM01.xlsx

    IM_001.xlsx

    Investigación 15.xlsx

    Devuelve:

    01

    001

    15
    """

    nombre = obtener_nombre_archivo(nombre_archivo)

    numeros = re.findall(r"\d+", nombre)

    if numeros:

        return numeros[0]

    return ""

# ==========================================================
# COLUMNAS ESTÁNDAR DEL PROYECTO
# ==========================================================

COLUMNAS_REQUERIDAS = [

    "RFC",

    "RAZON SOCIAL",

    "CLAVE",

    "DESCRIPCION",

    "CANTIDAD OFERTADA",

    "PAIS DE ORIGEN",

    "PRECIO UNITARIO"

]


# ----------------------------------------------------------

def validar_columnas(df: pd.DataFrame) -> tuple[bool, list]:
    """
    Valida que el DataFrame contenga las columnas requeridas.
    """

    faltantes = [
        columna
        for columna in COLUMNAS_REQUERIDAS
        if columna not in df.columns
    ]

    return len(faltantes) == 0, faltantes


# ----------------------------------------------------------

def eliminar_filas_vacias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas completamente vacías.
    """

    return (
        df
        .dropna(how="all")
        .reset_index(drop=True)
    )


# ----------------------------------------------------------

def eliminar_columnas_vacias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina columnas completamente vacías.
    """

    return (
        df
        .dropna(axis=1, how="all")
    )


# ----------------------------------------------------------

def agregar_investigacion(
    df: pd.DataFrame,
    investigacion: str
) -> pd.DataFrame:
    """
    Agrega la columna INVESTIGACION.
    """

    df = df.copy()

    df["INVESTIGACION"] = investigacion

    return df


# ----------------------------------------------------------

def agregar_nombre_archivo(
    df: pd.DataFrame,
    archivo: str
) -> pd.DataFrame:
    """
    Guarda el nombre del archivo origen.
    """

    df = df.copy()

    df["ARCHIVO"] = archivo

    return df


# ----------------------------------------------------------

def unir_dataframes(
    lista_df: list[pd.DataFrame]
) -> pd.DataFrame:
    """
    Une todas las investigaciones.
    """

    if not lista_df:

        return pd.DataFrame()

    return pd.concat(
        lista_df,
        ignore_index=True
    )


# ----------------------------------------------------------

def total_registros(df: pd.DataFrame) -> int:
    """
    Devuelve el total de registros.
    """

    return len(df)


# ----------------------------------------------------------

def total_claves(df: pd.DataFrame) -> int:
    """
    Devuelve el número de claves únicas.
    """

    return df["CLAVE"].nunique()


# ----------------------------------------------------------

def total_proveedores(df: pd.DataFrame) -> int:
    """
    Devuelve el número de proveedores únicos.
    """

    return df["RAZON SOCIAL"].nunique()


# ----------------------------------------------------------

def total_investigaciones(df: pd.DataFrame) -> int:
    """
    Devuelve el número de investigaciones cargadas.
    """

    return df["INVESTIGACION"].nunique()

# ==========================================================
# INVESTIGACIONES
# ==========================================================

def agregar_numero_investigacion(
    df: pd.DataFrame,
    nombre_archivo: str
) -> pd.DataFrame:
    """
    Agrega la columna INVESTIGACION.
    """

    numero = extraer_numero_investigacion(
        nombre_archivo
    )

    df["INVESTIGACION"] = numero

    return df


# ----------------------------------------------------------

def eliminar_filas_vacias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas completamente vacías.
    """

    return df.dropna(
        how="all"
    ).reset_index(drop=True)


# ----------------------------------------------------------

def eliminar_columnas_vacias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina columnas completamente vacías.
    """

    return df.dropna(
        axis=1,
        how="all"
    )


# ----------------------------------------------------------

def ordenar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ordena las columnas dejando primero las principales.
    """

    principales = [

        "INVESTIGACION",

        "RFC",

        "RAZON SOCIAL",

        "CLAVE",

        "DESCRIPCION",

        "PRECIO",

        "CANTIDAD",

        "MONTO",

        "FABRICANTE",

        "PAIS",

        "MARCA"

    ]

    existentes = [
        c for c in principales
        if c in df.columns
    ]

    restantes = [
        c for c in df.columns
        if c not in existentes
    ]

    return df[
        existentes + restantes
    ]


# ----------------------------------------------------------

def unir_dataframes(lista_df: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Une múltiples investigaciones.
    """

    if len(lista_df) == 0:

        return pd.DataFrame()

    return pd.concat(
        lista_df,
        ignore_index=True
    )

# ==========================================================
# PRECIOS
# ==========================================================

def obtener_precio_minimo(df: pd.DataFrame) -> float:
    """
    Precio mínimo.
    """

    return (
        df["PRECIO UNITARIO"]
        .min()
    )


# ----------------------------------------------------------

def obtener_precio_maximo(df: pd.DataFrame) -> float:
    """
    Precio máximo.
    """

    return (
        df["PRECIO UNITARIO"]
        .max()
    )


# ----------------------------------------------------------

def obtener_precio_promedio(df: pd.DataFrame) -> float:
    """
    Precio promedio.
    """

    return (
        df["PRECIO UNITARIO"]
        .mean()
    )


# ----------------------------------------------------------

def obtener_mejor_precio(df: pd.DataFrame) -> dict:
    """
    Devuelve toda la información del mejor precio.
    """

    fila = df.loc[
        df["PRECIO UNITARIO"].idxmin()
    ]

    return {

        "precio": fila["PRECIO UNITARIO"],

        "proveedor": fila["RAZON SOCIAL"],

        "rfc": fila["RFC"],

        "pais": fila["PAIS DE ORIGEN"],

        "investigacion": fila["INVESTIGACION"]

    }


# ----------------------------------------------------------

def obtener_peor_precio(df: pd.DataFrame) -> dict:
    """
    Devuelve toda la información del mayor precio.
    """

    fila = df.loc[
        df["PRECIO UNITARIO"].idxmax()
    ]

    return {

        "precio": fila["PRECIO UNITARIO"],

        "proveedor": fila["RAZON SOCIAL"],

        "rfc": fila["RFC"],

        "pais": fila["PAIS DE ORIGEN"],

        "investigacion": fila["INVESTIGACION"]

    }


# ----------------------------------------------------------

def calcular_variacion(df: pd.DataFrame) -> float:
    """
    Diferencia entre el mayor y menor precio.
    """

    return (

        obtener_precio_maximo(df)

        -

        obtener_precio_minimo(df)

    )


# ----------------------------------------------------------

def calcular_variacion_porcentual(df: pd.DataFrame) -> float:
    """
    Variación porcentual.
    """

    minimo = obtener_precio_minimo(df)

    if minimo == 0:

        return 0

    return (

        calcular_variacion(df)

        /

        minimo

    ) * 100


# ----------------------------------------------------------

def obtener_resumen_precios(
    df: pd.DataFrame
) -> dict:
    """
    Devuelve un resumen completo de precios.
    """

    return {

        "minimo": obtener_precio_minimo(df),

        "maximo": obtener_precio_maximo(df),

        "promedio": obtener_precio_promedio(df),

        "variacion": calcular_variacion(df),

        "variacion_pct": calcular_variacion_porcentual(df),

        "mejor": obtener_mejor_precio(df),

        "peor": obtener_peor_precio(df)

    }


# ----------------------------------------------------------

def ordenar_por_precio(
    df: pd.DataFrame,
    ascendente: bool = True
) -> pd.DataFrame:
    """
    Ordena por precio unitario.
    """

    return df.sort_values(
        "PRECIO UNITARIO",
        ascending=ascendente
    ).reset_index(drop=True)

# ==========================================================
# PROVEEDORES
# ==========================================================

def obtener_lista_proveedores(df: pd.DataFrame) -> list:
    """
    Devuelve la lista de proveedores ordenada alfabéticamente.
    """

    return sorted(
        df["RAZON SOCIAL"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def filtrar_por_proveedor(
    df: pd.DataFrame,
    proveedor: str
) -> pd.DataFrame:
    """
    Filtra un DataFrame por proveedor.
    """

    return (
        df[
            df["RAZON SOCIAL"] == proveedor
        ]
        .copy()
    )


# ----------------------------------------------------------

def obtener_total_proveedores(df: pd.DataFrame) -> int:
    """
    Número total de proveedores.
    """

    return df["RAZON SOCIAL"].nunique()


# ----------------------------------------------------------

def obtener_claves_proveedor(df: pd.DataFrame) -> list:
    """
    Lista de claves ofertadas por el proveedor.
    """

    return sorted(
        df["CLAVE"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def obtener_total_claves_proveedor(df: pd.DataFrame) -> int:
    """
    Número de claves distintas ofertadas.
    """

    return df["CLAVE"].nunique()


# ----------------------------------------------------------

def obtener_total_piezas_proveedor(df: pd.DataFrame) -> float:
    """
    Total de piezas ofertadas.
    """

    return df["CANTIDAD OFERTADA"].sum()


# ----------------------------------------------------------

def obtener_precio_promedio_proveedor(df: pd.DataFrame) -> float:
    """
    Precio promedio ofertado.
    """

    return (
        df["PRECIO UNITARIO"]
        .mean()
    )


# ----------------------------------------------------------

def obtener_precio_minimo_proveedor(df: pd.DataFrame) -> float:
    """
    Precio mínimo ofertado.
    """

    return (
        df["PRECIO UNITARIO"]
        .min()
    )


# ----------------------------------------------------------

def obtener_precio_maximo_proveedor(df: pd.DataFrame) -> float:
    """
    Precio máximo ofertado.
    """

    return (
        df["PRECIO UNITARIO"]
        .max()
    )


# ----------------------------------------------------------

def obtener_investigaciones_proveedor(df: pd.DataFrame) -> list:
    """
    Investigaciones donde aparece el proveedor.
    """

    return sorted(
        df["INVESTIGACION"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def obtener_total_investigaciones_proveedor(df: pd.DataFrame) -> int:
    """
    Número de investigaciones donde participa.
    """

    return df["INVESTIGACION"].nunique()


# ----------------------------------------------------------

def obtener_resumen_proveedor(df: pd.DataFrame) -> dict:
    """
    Devuelve un resumen completo del proveedor.
    """

    return {

        "proveedor":
            df["RAZON SOCIAL"].iloc[0],

        "rfc":
            df["RFC"].iloc[0],

        "pais":
            df["PAIS DE ORIGEN"].mode().iloc[0]
            if not df["PAIS DE ORIGEN"].mode().empty
            else "",

        "total_claves":
            obtener_total_claves_proveedor(df),

        "total_piezas":
            obtener_total_piezas_proveedor(df),

        "precio_promedio":
            obtener_precio_promedio_proveedor(df),

        "precio_minimo":
            obtener_precio_minimo_proveedor(df),

        "precio_maximo":
            obtener_precio_maximo_proveedor(df),

        "investigaciones":
            obtener_investigaciones_proveedor(df),

        "total_investigaciones":
            obtener_total_investigaciones_proveedor(df)

    }


# ----------------------------------------------------------

def obtener_detalle_proveedor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve el detalle ordenado por clave.
    """

    columnas = [

        "INVESTIGACION",

        "CLAVE",

        "DESCRIPCION",

        "CANTIDAD OFERTADA",

        "PRECIO UNITARIO"

    ]

    existentes = [
        c
        for c in columnas
        if c in df.columns
    ]

    return (
        df[existentes]
        .sort_values(
            ["CLAVE", "INVESTIGACION"]
        )
        .reset_index(drop=True)
    )

# ==========================================================
# CLAVES
# ==========================================================

def obtener_lista_claves(df: pd.DataFrame) -> list:
    """
    Devuelve la lista de claves disponibles.
    """

    return sorted(
        df["CLAVE"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def filtrar_por_clave(
    df: pd.DataFrame,
    clave: str
) -> pd.DataFrame:
    """
    Filtra el DataFrame por clave.
    """

    return (
        df[
            df["CLAVE"] == clave
        ]
        .copy()
    )


# ----------------------------------------------------------

def obtener_descripcion_clave(df: pd.DataFrame) -> str:
    """
    Obtiene la descripción de la clave.
    """

    if df.empty:
        return ""

    return df["DESCRIPCION"].iloc[0]


# ----------------------------------------------------------

def obtener_proveedores_por_clave(df: pd.DataFrame) -> list:
    """
    Lista de proveedores que ofertaron la clave.
    """

    return sorted(
        df["RAZON SOCIAL"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def obtener_total_proveedores_clave(df: pd.DataFrame) -> int:
    """
    Número de proveedores participantes.
    """

    return df["RAZON SOCIAL"].nunique()


# ----------------------------------------------------------

def obtener_total_piezas_clave(df: pd.DataFrame) -> float:
    """
    Total de piezas ofertadas.
    """

    return df["CANTIDAD OFERTADA"].sum()


# ----------------------------------------------------------

def obtener_investigaciones_clave(df: pd.DataFrame) -> list:
    """
    Investigaciones donde aparece la clave.
    """

    return sorted(
        df["INVESTIGACION"]
        .dropna()
        .unique()
        .tolist()
    )


# ----------------------------------------------------------

def obtener_total_investigaciones_clave(df: pd.DataFrame) -> int:
    """
    Número de investigaciones donde aparece la clave.
    """

    return df["INVESTIGACION"].nunique()


# ----------------------------------------------------------

def obtener_resumen_clave(df: pd.DataFrame) -> dict:
    """
    Devuelve un resumen completo de una clave.
    """

    return {

        "clave": df["CLAVE"].iloc[0],

        "descripcion": obtener_descripcion_clave(df),

        "total_proveedores": obtener_total_proveedores_clave(df),

        "total_piezas": obtener_total_piezas_clave(df),

        "precio_minimo": obtener_precio_minimo(df),

        "precio_maximo": obtener_precio_maximo(df),

        "precio_promedio": obtener_precio_promedio(df),

        "variacion": calcular_variacion(df),

        "variacion_pct": calcular_variacion_porcentual(df),

        "investigaciones": obtener_investigaciones_clave(df),

        "total_investigaciones": obtener_total_investigaciones_clave(df)

    }


# ----------------------------------------------------------

def obtener_detalle_clave(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve el detalle de la clave ordenado por precio.
    """

    columnas = [

        "INVESTIGACION",

        "RFC",

        "RAZON SOCIAL",

        "PAIS DE ORIGEN",

        "PRECIO UNITARIO",

        "CANTIDAD OFERTADA"

    ]

    existentes = [
        c
        for c in columnas
        if c in df.columns
    ]

    return (
        df[existentes]
        .sort_values(
            "PRECIO UNITARIO"
        )
        .reset_index(drop=True)
    )

# ==========================================================
# CONSULTAS
# ==========================================================

def filtrar(
    df: pd.DataFrame,
    columna: str,
    valor
) -> pd.DataFrame:
    """
    Filtra un DataFrame por igualdad.
    """

    return (
        df[
            df[columna] == valor
        ]
        .copy()
    )


# ----------------------------------------------------------

def filtrar_contiene(
    df: pd.DataFrame,
    columna: str,
    texto: str
) -> pd.DataFrame:
    """
    Filtra utilizando contains().
    """

    return (
        df[
            df[columna]
            .astype(str)
            .str.contains(
                texto,
                case=False,
                na=False
            )
        ]
        .copy()
    )


# ----------------------------------------------------------

def agrupar_por(
    df: pd.DataFrame,
    columna: str
):
    """
    Agrupa un DataFrame.
    """

    return df.groupby(columna)


# ----------------------------------------------------------

def ordenar(
    df: pd.DataFrame,
    columna: str,
    ascendente: bool = True
) -> pd.DataFrame:
    """
    Ordena cualquier DataFrame.
    """

    return (
        df
        .sort_values(
            columna,
            ascending=ascendente
        )
        .reset_index(drop=True)
    )


# ----------------------------------------------------------

def top(
    df: pd.DataFrame,
    columna: str,
    n: int = 10
) -> pd.DataFrame:
    """
    Top N registros.
    """

    return (
        ordenar(
            df,
            columna,
            False
        )
        .head(n)
    )


# ----------------------------------------------------------

def bottom(
    df: pd.DataFrame,
    columna: str,
    n: int = 10
) -> pd.DataFrame:
    """
    Bottom N registros.
    """

    return (
        ordenar(
            df,
            columna,
            True
        )
        .head(n)
    )


# ==========================================================
# ESTADÍSTICAS
# ==========================================================

def media(
    df: pd.DataFrame,
    columna: str
) -> float:

    return df[columna].mean()


# ----------------------------------------------------------

def mediana(
    df: pd.DataFrame,
    columna: str
) -> float:

    return df[columna].median()


# ----------------------------------------------------------

def minimo(
    df: pd.DataFrame,
    columna: str
) -> float:

    return df[columna].min()


# ----------------------------------------------------------

def maximo(
    df: pd.DataFrame,
    columna: str
) -> float:

    return df[columna].max()


# ----------------------------------------------------------

def suma(
    df: pd.DataFrame,
    columna: str
) -> float:

    return df[columna].sum()


# ----------------------------------------------------------

def contar(
    df: pd.DataFrame,
    columna: str
) -> int:

    return df[columna].count()


# ----------------------------------------------------------

def contar_unicos(
    df: pd.DataFrame,
    columna: str
) -> int:

    return df[columna].nunique()


# ==========================================================
# RANKINGS
# ==========================================================

def ranking_proveedores(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Ranking de proveedores por número de claves.
    """

    return (
        df.groupby("RAZON SOCIAL")
        .agg(
            claves=("CLAVE","nunique"),
            piezas=("CANTIDAD OFERTADA","sum"),
            precio_promedio=("PRECIO UNITARIO","mean")
        )
        .sort_values(
            "claves",
            ascending=False
        )
        .reset_index()
    )


# ----------------------------------------------------------

def ranking_claves(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Ranking de claves por número de ofertas.
    """

    return (
        df.groupby("CLAVE")
        .agg(
            proveedores=("RAZON SOCIAL","nunique"),
            investigaciones=("INVESTIGACION","nunique"),
            precio_promedio=("PRECIO UNITARIO","mean")
        )
        .sort_values(
            "proveedores",
            ascending=False
        )
        .reset_index()
    )


# ==========================================================
# RESUMEN GENERAL
# ==========================================================

def obtener_resumen_general(
    df: pd.DataFrame
) -> dict:
    """
    Devuelve el resumen ejecutivo del sistema.
    """

    return {

        "investigaciones":
            total_investigaciones(df),

        "proveedores":
            total_proveedores(df),

        "claves":
            total_claves(df),

        "registros":
            total_registros(df),

        "precio_promedio":
            obtener_precio_promedio(df),

        "precio_minimo":
            obtener_precio_minimo(df),

        "precio_maximo":
            obtener_precio_maximo(df)

    }

# ==========================================================
# LIMPIEZA FINAL DEL DATAFRAME
# ==========================================================

def preparar_dataframe_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el DataFrame principal de SIMI.

    Asume columnas fijas:
    RFC, RAZON SOCIAL, CLAVE, DESCRIPCION,
    CANTIDAD OFERTADA, PAIS DE ORIGEN, PRECIO UNITARIO
    """

    df = df.copy()

    df = eliminar_filas_vacias(df)

    df = convertir_columnas_texto(df)

    df["RFC"] = df["RFC"].apply(normalizar_rfc)
    df["RAZON SOCIAL"] = df["RAZON SOCIAL"].apply(limpiar_texto)
    df["CLAVE"] = df["CLAVE"].apply(normalizar_clave)
    df["DESCRIPCION"] = df["DESCRIPCION"].apply(limpiar_texto)
    df["PAIS DE ORIGEN"] = df["PAIS DE ORIGEN"].apply(limpiar_texto)

    df["CANTIDAD OFERTADA"] = df["CANTIDAD OFERTADA"].apply(convertir_float)
    df["PRECIO UNITARIO"] = df["PRECIO UNITARIO"].apply(convertir_float)

    return df


# ==========================================================
# FORMATO DE TABLAS
# ==========================================================

def formatear_tabla_precios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve una copia del DataFrame con precios formateados.
    """

    df = df.copy()

    if "PRECIO UNITARIO" in df.columns:
        df["PRECIO UNITARIO"] = df["PRECIO UNITARIO"].apply(formatear_moneda)

    if "CANTIDAD OFERTADA" in df.columns:
        df["CANTIDAD OFERTADA"] = df["CANTIDAD OFERTADA"].apply(
            lambda x: f"{convertir_float(x):,.0f}"
        )

    return df


# ==========================================================
# VALIDACIONES
# ==========================================================

def dataframe_valido(df: pd.DataFrame) -> bool:
    """
    Valida si el DataFrame puede ser utilizado por SIMI.
    """

    valido, faltantes = validar_columnas(df)

    if not valido:
        return False

    if df.empty:
        return False

    return True


def obtener_errores_dataframe(df: pd.DataFrame) -> list[str]:
    """
    Devuelve una lista de errores detectados en el DataFrame.
    """

    errores = []

    valido, faltantes = validar_columnas(df)

    if not valido:
        errores.append(
            "Columnas faltantes: " + ", ".join(faltantes)
        )

    if df.empty:
        errores.append("El archivo no contiene registros.")

    return errores


# ==========================================================
# UTILIDADES PARA EXPORTACIÓN
# ==========================================================

def limpiar_nombre_hoja_excel(nombre: str) -> str:
    """
    Limpia un nombre para usarlo como hoja de Excel.
    """

    nombre = limpiar_texto(nombre)

    caracteres_invalidos = ["\\", "/", "*", "[", "]", ":", "?"]

    for caracter in caracteres_invalidos:
        nombre = nombre.replace(caracter, "")

    return nombre[:31]


# ==========================================================
# UTILIDADES FUTURAS PARA ADJUDICACIONES
# ==========================================================

def tiene_columna_adjudicacion(df: pd.DataFrame) -> bool:
    """
    Indica si el DataFrame ya contiene información de adjudicación.

    Esto queda preparado para fases futuras.
    """

    posibles_columnas = [
        "ADJUDICADO",
        "GANADOR",
        "PROVEEDOR ADJUDICADO",
        "CANTIDAD ADJUDICADA",
        "MONTO ADJUDICADO"
    ]

    return any(columna in df.columns for columna in posibles_columnas)