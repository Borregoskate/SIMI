
"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

prevalidacion_adjudicaciones_service.py

Servicio de prevalidación para la Carga 5:
Adjudicaciones.

Flujo obligatorio:
1. Leer el archivo.
2. Estandarizar nombres de columnas.
3. Validar estructura.
4. Seleccionar únicamente los datos necesarios.
5. Normalizar valores.
6. Eliminar filas completamente vacías.
7. Validar contenido.
8. Validar duplicados y máximo de proveedores por clave.
9. Calcular porcentajes adjudicados enteros.
10. Entregar el DataFrame normalizado al servicio de importación.

Este servicio NO consulta ni modifica la base de datos.

Reglas funcionales:
- Cantidad Max. se utiliza como CANTIDAD_ADJUDICADA.
- Cantidad Min. se ignora.
- Los importes, IVA y totales se ignoran.
- Una clave puede adjudicarse a entre uno y tres proveedores.
- El porcentaje se calcula con las cantidades del archivo.
- Los porcentajes se almacenan como enteros.
- La suma de porcentajes por clave debe ser exactamente 100.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, ROUND_FLOOR

import pandas as pd

from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_nombre_columna,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
)
from services.validacion_service import (
    NIVEL_ERROR,
    esta_vacio,
    validar_campos_obligatorios,
    validar_duplicados,
    validar_numero_positivo,
)


HOJA_ADJUDICACIONES = "Hoja1"
FILA_INICIAL_EXCEL = 2
MAXIMO_PROVEEDORES_POR_CLAVE = 3

COLUMNAS_REQUERIDAS_ADJUDICACIONES = {
    "clave": "CLAVE",
    "descripcion_detallada": "DESCRIPCION",
    "rfc": "RFC",
    "licitante": "RAZON_SOCIAL",
    "precio_unitario": "PRECIO_UNITARIO_ADJUDICADO",
    "cantidad_max": "CANTIDAD_ADJUDICADA",
    "procedimiento": "PROCEDIMIENTO",
}

NORMALIZADORES_ADJUDICACIONES = {
    "CLAVE": normalizar_clave,
    "DESCRIPCION": normalizar_texto,
    "RFC": normalizar_rfc,
    "RAZON_SOCIAL": normalizar_razon_social,
    "PRECIO_UNITARIO_ADJUDICADO": normalizar_decimal,
    "CANTIDAD_ADJUDICADA": normalizar_decimal,
    "PROCEDIMIENTO": normalizar_texto,
}

CAMPOS_OBLIGATORIOS_ADJUDICACIONES = [
    "CLAVE",
    "DESCRIPCION",
    "RFC",
    "RAZON_SOCIAL",
    "PRECIO_UNITARIO_ADJUDICADO",
    "CANTIDAD_ADJUDICADA",
    "PROCEDIMIENTO",
]


def leer_archivo_adjudicaciones(archivo):
    """Lee la hoja oficial del archivo de adjudicaciones."""
    if archivo is None:
        raise ValueError("No se recibió un archivo Excel.")

    if hasattr(archivo, "seek"):
        archivo.seek(0)

    return pd.read_excel(
        archivo,
        sheet_name=HOJA_ADJUDICACIONES,
        header=0,
    )


def estandarizar_columnas_adjudicaciones(df):
    """Estandariza los nombres de las columnas del archivo."""
    if df is None:
        return None

    df_estandarizado = df.copy()
    df_estandarizado.columns = [
        normalizar_nombre_columna(columna)
        for columna in df_estandarizado.columns
    ]
    return df_estandarizado


def validar_columnas_requeridas_adjudicaciones(df):
    """Valida la presencia de las columnas necesarias."""
    if df is None:
        return [{
            "fila": None,
            "error": "No se recibió información para validar.",
        }]

    errores = []
    columnas_archivo = set(df.columns)

    for columna in COLUMNAS_REQUERIDAS_ADJUDICACIONES:
        if columna not in columnas_archivo:
            errores.append({
                "fila": None,
                "error": f"Falta la columna requerida: {columna}",
            })

    return errores


def preparar_dataframe_adjudicaciones(df):
    """
    Selecciona únicamente las columnas necesarias y las renombra
    al formato interno de SIMI.
    """
    columnas_origen = list(
        COLUMNAS_REQUERIDAS_ADJUDICACIONES.keys()
    )

    df_trabajo = df[columnas_origen].copy()

    return df_trabajo.rename(
        columns=COLUMNAS_REQUERIDAS_ADJUDICACIONES
    )


def normalizar_archivo_adjudicaciones(df):
    """Normaliza todos los valores antes de validarlos."""
    df_normalizado = df.copy()

    for columna, normalizador in (
        NORMALIZADORES_ADJUDICACIONES.items()
    ):
        if columna in df_normalizado.columns:
            df_normalizado[columna] = (
                df_normalizado[columna].apply(normalizador)
            )

    return df_normalizado


def eliminar_filas_vacias_adjudicaciones(df):
    """Elimina filas completamente vacías después de normalizar."""
    if df is None:
        return None

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Se esperaba un DataFrame para eliminar filas vacías."
        )

    if df.empty:
        return df.copy()

    mascara_con_datos = df.apply(
        lambda fila: any(
            not esta_vacio(valor)
            for valor in fila
        ),
        axis=1,
    )

    return df[mascara_con_datos].copy()


def convertir_mensajes_a_errores(mensajes):
    """Convierte mensajes estándar al formato utilizado por la UI."""
    errores = []

    for mensaje in mensajes or []:
        if mensaje.get("nivel") != NIVEL_ERROR:
            continue

        errores.append({
            "fila": mensaje.get("fila"),
            "error": mensaje.get("mensaje"),
        })

    return errores


def validar_contenido_adjudicaciones(df):
    """Valida campos obligatorios, cantidades y precios positivos."""
    mensajes = []

    mensajes.extend(
        validar_campos_obligatorios(
            df=df,
            campos_obligatorios=(
                CAMPOS_OBLIGATORIOS_ADJUDICACIONES
            ),
            fila_inicio_excel=FILA_INICIAL_EXCEL,
        )
    )

    mensajes.extend(
        validar_numero_positivo(
            df=df,
            campo="CANTIDAD_ADJUDICADA",
            fila_inicio_excel=FILA_INICIAL_EXCEL,
            obligatorio=False,
        )
    )

    mensajes.extend(
        validar_numero_positivo(
            df=df,
            campo="PRECIO_UNITARIO_ADJUDICADO",
            fila_inicio_excel=FILA_INICIAL_EXCEL,
            obligatorio=False,
        )
    )

    return convertir_mensajes_a_errores(mensajes)


def validar_duplicados_adjudicaciones(df):
    """
    No permite más de una adjudicación para el mismo RFC y la
    misma clave dentro del archivo.
    """
    mensajes = validar_duplicados(
        df=df,
        campos=["RFC", "CLAVE"],
        fila_inicio_excel=FILA_INICIAL_EXCEL,
        nivel=NIVEL_ERROR,
        mensaje=(
            "Existe más de una adjudicación para el mismo RFC "
            "y la misma clave."
        ),
    )

    return convertir_mensajes_a_errores(mensajes)


def validar_unico_procedimiento(df):
    """Verifica que todas las filas pertenezcan a un procedimiento."""
    valores = {
        valor
        for valor in df["PROCEDIMIENTO"].tolist()
        if not esta_vacio(valor)
    }

    if len(valores) <= 1:
        return []

    return [{
        "fila": None,
        "error": (
            "El archivo contiene más de un procedimiento. "
            "Cada carga debe corresponder a un solo procedimiento."
        ),
    }]


def validar_maximo_proveedores_por_clave(df):
    """Valida que cada clave tenga entre uno y tres proveedores."""
    errores = []

    resumen = (
        df.groupby("CLAVE", dropna=False)["RFC"]
        .nunique(dropna=True)
    )

    for clave, total in resumen.items():
        if total > MAXIMO_PROVEEDORES_POR_CLAVE:
            errores.append({
                "fila": None,
                "error": (
                    f"La clave {clave} contiene {total} proveedores "
                    "adjudicados. El máximo permitido es "
                    f"{MAXIMO_PROVEEDORES_POR_CLAVE}."
                ),
            })

    return errores


def _convertir_decimal(valor):
    """Convierte un valor numérico normalizado a Decimal."""
    if isinstance(valor, Decimal):
        return valor

    return Decimal(str(valor))


def calcular_porcentajes_enteros(cantidades):
    """
    Calcula porcentajes enteros mediante el método de restos mayores.

    Garantiza que:
    - Cada porcentaje sea un entero.
    - La suma final sea exactamente 100.
    - En caso de empate se respete el orden original.
    """
    cantidades_decimal = [
        _convertir_decimal(valor)
        for valor in cantidades
    ]

    total = sum(cantidades_decimal, Decimal("0"))

    if total <= 0:
        raise ValueError(
            "La suma de cantidades adjudicadas debe ser mayor que cero."
        )

    porcentajes_exactos = [
        (cantidad / total) * Decimal("100")
        for cantidad in cantidades_decimal
    ]

    porcentajes_base = [
        int(
            porcentaje.to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        for porcentaje in porcentajes_exactos
    ]

    faltantes = 100 - sum(porcentajes_base)

    restos = [
        porcentaje - Decimal(base)
        for porcentaje, base in zip(
            porcentajes_exactos,
            porcentajes_base,
        )
    ]

    orden = sorted(
        range(len(restos)),
        key=lambda indice: (
            -restos[indice],
            indice,
        ),
    )

    for indice in orden[:faltantes]:
        porcentajes_base[indice] += 1

    return porcentajes_base


def agregar_porcentajes_adjudicados(df):
    """
    Agrupa por clave y calcula el porcentaje entero correspondiente
    a cada proveedor según CANTIDAD_ADJUDICADA.
    """
    resultado = df.copy()
    resultado["PORCENTAJE_ADJUDICADO"] = 0

    for _, indices in resultado.groupby(
        "CLAVE",
        sort=False,
        dropna=False,
    ).groups.items():
        indices = list(indices)

        cantidades = (
            resultado.loc[
                indices,
                "CANTIDAD_ADJUDICADA",
            ]
            .tolist()
        )

        porcentajes = calcular_porcentajes_enteros(
            cantidades
        )

        resultado.loc[
            indices,
            "PORCENTAJE_ADJUDICADO",
        ] = porcentajes

    resultado["PORCENTAJE_ADJUDICADO"] = (
        resultado["PORCENTAJE_ADJUDICADO"].astype(int)
    )

    return resultado


def validar_suma_porcentajes(df):
    """Confirma que cada clave tenga exactamente 100 por ciento."""
    errores = []

    totales = (
        df.groupby("CLAVE", dropna=False)[
            "PORCENTAJE_ADJUDICADO"
        ]
        .sum()
    )

    for clave, total in totales.items():
        if int(total) != 100:
            errores.append({
                "fila": None,
                "error": (
                    f"Los porcentajes de la clave {clave} "
                    f"suman {total} y deben sumar exactamente 100."
                ),
            })

    return errores


def prevalidar_archivo_adjudicaciones(archivo):
    """Ejecuta la prevalidación completa de la Carga 5."""
    try:
        df_original = leer_archivo_adjudicaciones(
            archivo
        )
    except Exception as error:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": (
                    "No fue posible leer el archivo Excel: "
                    f"{error}"
                ),
            }],
            "df": None,
        }

    df_estandarizado = (
        estandarizar_columnas_adjudicaciones(
            df_original
        )
    )

    errores_columnas = (
        validar_columnas_requeridas_adjudicaciones(
            df_estandarizado
        )
    )

    if errores_columnas:
        return {
            "valido": False,
            "errores": errores_columnas,
            "df": None,
        }

    df_preparado = preparar_dataframe_adjudicaciones(
        df_estandarizado
    )
    df_normalizado = normalizar_archivo_adjudicaciones(
        df_preparado
    )
    df_normalizado = eliminar_filas_vacias_adjudicaciones(
        df_normalizado
    )

    if df_normalizado is None or df_normalizado.empty:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": (
                    "El archivo no contiene adjudicaciones "
                    "válidas para procesar."
                ),
            }],
            "df": df_normalizado,
        }

    errores = []
    errores.extend(
        validar_contenido_adjudicaciones(
            df_normalizado
        )
    )
    errores.extend(
        validar_duplicados_adjudicaciones(
            df_normalizado
        )
    )
    errores.extend(
        validar_unico_procedimiento(
            df_normalizado
        )
    )
    errores.extend(
        validar_maximo_proveedores_por_clave(
            df_normalizado
        )
    )

    if errores:
        return {
            "valido": False,
            "errores": errores,
            "df": df_normalizado.reset_index(drop=True),
        }

    try:
        df_final = agregar_porcentajes_adjudicados(
            df_normalizado
        )
    except Exception as error:
        return {
            "valido": False,
            "errores": [{
                "fila": None,
                "error": str(error),
            }],
            "df": df_normalizado.reset_index(drop=True),
        }

    errores_porcentajes = validar_suma_porcentajes(
        df_final
    )

    return {
        "valido": len(errores_porcentajes) == 0,
        "errores": errores_porcentajes,
        "df": df_final.reset_index(drop=True),
    }


__all__ = [
    "HOJA_ADJUDICACIONES",
    "FILA_INICIAL_EXCEL",
    "MAXIMO_PROVEEDORES_POR_CLAVE",
    "COLUMNAS_REQUERIDAS_ADJUDICACIONES",
    "NORMALIZADORES_ADJUDICACIONES",
    "CAMPOS_OBLIGATORIOS_ADJUDICACIONES",
    "leer_archivo_adjudicaciones",
    "estandarizar_columnas_adjudicaciones",
    "validar_columnas_requeridas_adjudicaciones",
    "preparar_dataframe_adjudicaciones",
    "normalizar_archivo_adjudicaciones",
    "eliminar_filas_vacias_adjudicaciones",
    "convertir_mensajes_a_errores",
    "validar_contenido_adjudicaciones",
    "validar_duplicados_adjudicaciones",
    "validar_unico_procedimiento",
    "validar_maximo_proveedores_por_clave",
    "calcular_porcentajes_enteros",
    "agregar_porcentajes_adjudicados",
    "validar_suma_porcentajes",
    "prevalidar_archivo_adjudicaciones",
]