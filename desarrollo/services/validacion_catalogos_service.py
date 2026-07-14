"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

validacion_catalogos_service.py

Servicio reutilizable de validación contra base de datos.

Responsabilidades:

1. Verificar la existencia de procedimientos.
2. Verificar claves contra el catálogo.
3. Enriquecer DataFrames con identificadores encontrados.
4. Identificar registros nuevos.

Este servicio NO inserta ni actualiza datos.

Este servicio NO:

- abre conexiones;
- cierra conexiones;
- crea cursores;
- ejecuta SQL directamente;
- administra commit o rollback.

Toda consulta se delega a los repositories homologados.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

import pandas as pd

from repositories.claves_repository import ClavesRepository
from repositories.procedimientos_repository import (
    ProcedimientosRepository,
)
from services.normalizacion_service import (
    normalizar_clave,
    normalizar_texto,
)


def obtener_claves_catalogo(
    claves,
    conn=None,
):
    """
    Consulta las claves existentes mediante ClavesRepository.

    Devuelve un diccionario indexado por el valor normalizado de la
    clave.
    """

    if not claves:
        return {}

    claves_repository = ClavesRepository()
    catalogo = {}

    claves_unicas = []

    for valor in claves:
        clave = normalizar_clave(valor)

        if clave and clave not in claves_unicas:
            claves_unicas.append(clave)

    for clave in claves_unicas:
        registro = claves_repository.get_by_clave(
            clave=clave,
            conn=conn,
        )

        if not registro:
            continue

        if not isinstance(registro, dict):
            raise TypeError(
                "ClavesRepository debe devolver registros "
                "con formato de diccionario."
            )

        clave_registro = normalizar_clave(
            registro.get("clave")
        )

        if not clave_registro:
            continue

        catalogo[clave_registro] = {
            "id_clave": registro.get("id_clave"),
            "clave": clave_registro,
            "descripcion": normalizar_texto(
                registro.get("descripcion")
            ),
        }

    return catalogo


def validar_procedimiento_existente(
    numero_procedimiento,
    conn=None,
):
    """
    Comprueba si un procedimiento ya existe.

    El número o nombre debe llegar normalizado desde el flujo de
    prevalidación.
    """

    numero_normalizado = normalizar_texto(
        numero_procedimiento
    )

    if not numero_normalizado:
        return {
            "existe": False,
            "id_procedimiento": None,
            "numero_procedimiento": None,
        }

    repository = ProcedimientosRepository()

    registro = repository.get_by_numero_procedimiento(
        numero_procedimiento=numero_normalizado,
        conn=conn,
    )

    if not registro:
        return {
            "existe": False,
            "id_procedimiento": None,
            "numero_procedimiento": None,
        }

    if not isinstance(registro, dict):
        raise TypeError(
            "ProcedimientosRepository debe devolver registros "
            "con formato de diccionario."
        )

    return {
        "existe": True,
        "id_procedimiento": registro.get(
            "id_procedimiento"
        ),
        "numero_procedimiento": registro.get(
            "numero_procedimiento"
        ),
    }


def validar_claves_contra_catalogo(
    df,
    conn=None,
):
    """
    Valida las claves del archivo contra el catálogo.

    Reglas autorizadas:

    - Solo se verifica la existencia de la CLAVE.
    - No se compara la descripción con la base de datos.
    - Si la clave existe, se agrega ID_CLAVE.
    - Si no existe, se marca ES_NUEVA = True.
    - No se inserta información.
    """

    errores = []

    if df is None:
        return {
            "success": False,
            "df": None,
            "errores": [
                "No se recibió información para validar "
                "contra el catálogo."
            ],
            "resumen": {
                "total_registros": 0,
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": 1,
            },
        }

    if not isinstance(df, pd.DataFrame):
        return {
            "success": False,
            "df": None,
            "errores": [
                "La información recibida no tiene formato "
                "de DataFrame."
            ],
            "resumen": {
                "total_registros": 0,
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": 1,
            },
        }

    if "CLAVE" not in df.columns:
        return {
            "success": False,
            "df": df.copy(),
            "errores": [
                "No se encontró la columna CLAVE."
            ],
            "resumen": {
                "total_registros": len(df),
                "claves_existentes": 0,
                "claves_nuevas": 0,
                "errores": 1,
            },
        }

    df_validado = df.copy()

    df_validado["ID_CLAVE"] = pd.Series(
        [None] * len(df_validado),
        index=df_validado.index,
        dtype="object",
    )

    df_validado["ES_NUEVA"] = False

    claves_archivo = [
        clave
        for clave in df_validado["CLAVE"].tolist()
        if normalizar_clave(clave)
    ]

    catalogo_claves = obtener_claves_catalogo(
        claves=claves_archivo,
        conn=conn,
    )

    for indice, fila in df_validado.iterrows():
        clave = normalizar_clave(
            fila.get("CLAVE")
        )

        if not clave:
            continue

        clave_bd = catalogo_claves.get(clave)

        if clave_bd:
            df_validado.at[
                indice,
                "ID_CLAVE",
            ] = clave_bd.get("id_clave")

            df_validado.at[
                indice,
                "ES_NUEVA",
            ] = False

        else:
            df_validado.at[
                indice,
                "ID_CLAVE",
            ] = None

            df_validado.at[
                indice,
                "ES_NUEVA",
            ] = True

    mascara_con_clave = df_validado["CLAVE"].apply(
        lambda valor: normalizar_clave(valor) is not None
    )

    total_nuevas = int(
        (
            mascara_con_clave
            & (df_validado["ES_NUEVA"] == True)
        ).sum()
    )

    total_existentes = int(
        (
            mascara_con_clave
            & (df_validado["ES_NUEVA"] == False)
        ).sum()
    )

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
        "resumen": resumen,
    }


__all__ = [
    "obtener_claves_catalogo",
    "validar_procedimiento_existente",
    "validar_claves_contra_catalogo",
]