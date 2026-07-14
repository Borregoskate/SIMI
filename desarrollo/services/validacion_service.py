"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

validacion_service.py

Servicio general de validación de datos.

Responsabilidades:

1. Construir mensajes estándar de validación.
2. Validar columnas requeridas.
3. Validar campos obligatorios.
4. Detectar filas vacías.
5. Detectar duplicados.
6. Validar reglas generales de contenido.
7. Generar resúmenes de validación.

Este servicio recibe datos previamente normalizados.

Este servicio NO:

- normaliza datos;
- consulta la base de datos;
- abre conexiones;
- crea cursores;
- ejecuta SQL;
- inserta o actualiza información.

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

import pandas as pd

from services.normalizacion_service import normalizar_texto


NIVEL_ERROR = "ERROR"
NIVEL_ADVERTENCIA = "ADVERTENCIA"
NIVEL_INFO = "INFO"


def esta_vacio(valor):
    """
    Determina si un valor debe considerarse vacío.

    Los datos deberían llegar previamente normalizados, pero esta
    función protege las validaciones ante valores None, NaN o cadenas
    vacías.
    """

    if valor is None:
        return True

    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(valor, str):
        return valor.strip() == ""

    return False


def limpiar_texto_usuario(valor):
    """
    Devuelve una representación legible del valor para mensajes.

    No debe utilizarse como normalizador de datos.
    """

    if esta_vacio(valor):
        return ""

    return " ".join(str(valor).strip().split())


def crear_mensaje_validacion(
    nivel,
    campo,
    mensaje,
    fila=None,
    valor=None,
):
    """
    Crea un mensaje estándar de validación.
    """

    if nivel not in {
        NIVEL_ERROR,
        NIVEL_ADVERTENCIA,
        NIVEL_INFO,
    }:
        raise ValueError(
            f"Nivel de validación no permitido: {nivel}"
        )

    return {
        "nivel": nivel,
        "fila": fila,
        "campo": campo,
        "valor": valor,
        "mensaje": str(mensaje),
    }


def validar_columnas_requeridas(
    df,
    columnas_requeridas,
):
    """
    Valida que existan las columnas requeridas.
    """

    mensajes = []

    if df is None:
        mensajes.append(
            crear_mensaje_validacion(
                nivel=NIVEL_ERROR,
                campo="ARCHIVO",
                mensaje="No se recibió información para validar.",
            )
        )
        return mensajes

    if not isinstance(df, pd.DataFrame):
        mensajes.append(
            crear_mensaje_validacion(
                nivel=NIVEL_ERROR,
                campo="ARCHIVO",
                mensaje=(
                    "La información recibida no tiene formato "
                    "de DataFrame."
                ),
            )
        )
        return mensajes

    columnas_archivo = set(df.columns)

    for columna in columnas_requeridas or []:
        if columna not in columnas_archivo:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ERROR,
                    campo=columna,
                    mensaje=(
                        "No se encontró la columna requerida: "
                        f"{columna}"
                    ),
                )
            )

    return mensajes


def validar_campos_obligatorios(
    df,
    campos_obligatorios,
    fila_inicio_excel=2,
):
    """
    Valida que los campos obligatorios tengan información.
    """

    mensajes = []

    if df is None or df.empty:
        return mensajes

    for posicion, (_, row) in enumerate(df.iterrows()):
        fila_excel = fila_inicio_excel + posicion

        for campo in campos_obligatorios or []:
            valor = row.get(campo)

            if esta_vacio(valor):
                mensajes.append(
                    crear_mensaje_validacion(
                        nivel=NIVEL_ERROR,
                        fila=fila_excel,
                        campo=campo,
                        valor=valor,
                        mensaje=f"El campo {campo} es obligatorio.",
                    )
                )

    return mensajes


def validar_filas_vacias(
    df,
    campos_base,
    fila_inicio_excel=2,
):
    """
    Detecta filas completamente vacías.

    Una fila vacía genera advertencia porque puede eliminarse antes
    de continuar con la importación.
    """

    mensajes = []

    if df is None or df.empty:
        return mensajes

    for posicion, (_, row) in enumerate(df.iterrows()):
        fila_excel = fila_inicio_excel + posicion

        fila_vacia = all(
            esta_vacio(row.get(campo))
            for campo in campos_base or []
        )

        if fila_vacia:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ADVERTENCIA,
                    fila=fila_excel,
                    campo="FILA",
                    mensaje=(
                        "Fila completamente vacía. "
                        "Será ignorada."
                    ),
                )
            )

    return mensajes


def validar_duplicados(
    df,
    campos,
    fila_inicio_excel=2,
    nivel=NIVEL_ERROR,
    mensaje=None,
):
    """
    Detecta registros duplicados mediante uno o varios campos.

    Parámetros:
        campos:
            Nombre de una columna o lista de columnas.

    Los valores deben llegar normalizados.
    """

    mensajes = []

    if df is None or df.empty:
        return mensajes

    if isinstance(campos, str):
        campos = [campos]

    campos = list(campos or [])

    if not campos:
        return mensajes

    if any(campo not in df.columns for campo in campos):
        return mensajes

    mascara_valida = pd.Series(
        True,
        index=df.index,
        dtype=bool,
    )

    for campo in campos:
        mascara_valida &= df[campo].apply(
            lambda valor: not esta_vacio(valor)
        )

    df_validos = df[mascara_valida].copy()

    mascara_duplicados = df_validos.duplicated(
        subset=campos,
        keep=False,
    )

    indices_duplicados = set(
        df_validos[mascara_duplicados].index
    )

    for posicion, (indice, row) in enumerate(df.iterrows()):
        if indice not in indices_duplicados:
            continue

        fila_excel = fila_inicio_excel + posicion

        valores = {
            campo: row.get(campo)
            for campo in campos
        }

        mensaje_final = mensaje

        if not mensaje_final:
            campos_texto = ", ".join(campos)
            mensaje_final = (
                "Registro duplicado detectado para los campos: "
                f"{campos_texto}."
            )

        mensajes.append(
            crear_mensaje_validacion(
                nivel=nivel,
                fila=fila_excel,
                campo=", ".join(campos),
                valor=valores,
                mensaje=mensaje_final,
            )
        )

    return mensajes


def validar_descripcion_distinta_por_clave(
    df,
    campo_clave="CLAVE",
    campo_descripcion="DESCRIPCION",
    fila_inicio_excel=2,
):
    """
    Valida consistencia interna del archivo.

    Una misma clave no debe contener descripciones distintas dentro
    del mismo archivo.

    Esta regla NO compara la descripción contra la base de datos.
    """

    mensajes = []

    if (
        df is None
        or df.empty
        or campo_clave not in df.columns
        or campo_descripcion not in df.columns
    ):
        return mensajes

    df_temporal = df.copy()

    df_temporal = df_temporal[
        df_temporal[campo_clave].apply(
            lambda valor: not esta_vacio(valor)
        )
        & df_temporal[campo_descripcion].apply(
            lambda valor: not esta_vacio(valor)
        )
    ]

    if df_temporal.empty:
        return mensajes

    grupos = (
        df_temporal
        .groupby(campo_clave)[campo_descripcion]
        .nunique(dropna=True)
    )

    claves_conflictivas = set(
        grupos[grupos > 1].index
    )

    for posicion, (_, row) in enumerate(df.iterrows()):
        clave = row.get(campo_clave)

        if clave not in claves_conflictivas:
            continue

        fila_excel = fila_inicio_excel + posicion

        mensajes.append(
            crear_mensaje_validacion(
                nivel=NIVEL_ERROR,
                fila=fila_excel,
                campo=campo_descripcion,
                valor=row.get(campo_descripcion),
                mensaje=(
                    "La misma clave tiene descripciones distintas "
                    "dentro del archivo."
                ),
            )
        )

    return mensajes


def validar_longitud_minima_texto(
    df,
    campo,
    longitud_minima=5,
    fila_inicio_excel=2,
):
    """
    Genera una advertencia cuando un texto es demasiado corto.
    """

    mensajes = []

    if (
        df is None
        or df.empty
        or campo not in df.columns
    ):
        return mensajes

    for posicion, (_, row) in enumerate(df.iterrows()):
        fila_excel = fila_inicio_excel + posicion
        valor = limpiar_texto_usuario(row.get(campo))

        if not valor:
            continue

        if len(valor) < longitud_minima:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ADVERTENCIA,
                    fila=fila_excel,
                    campo=campo,
                    valor=valor,
                    mensaje=(
                        f"El texto del campo {campo} parece "
                        "demasiado corto."
                    ),
                )
            )

    return mensajes


def validar_numero_positivo(
    df,
    campo,
    fila_inicio_excel=2,
    obligatorio=True,
):
    """
    Valida que un campo numérico sea mayor a cero.
    """

    mensajes = []

    if (
        df is None
        or df.empty
        or campo not in df.columns
    ):
        return mensajes

    for posicion, (_, row) in enumerate(df.iterrows()):
        fila_excel = fila_inicio_excel + posicion
        valor = row.get(campo)

        if esta_vacio(valor):
            if obligatorio:
                mensajes.append(
                    crear_mensaje_validacion(
                        nivel=NIVEL_ERROR,
                        fila=fila_excel,
                        campo=campo,
                        valor=valor,
                        mensaje=f"El campo {campo} es obligatorio.",
                    )
                )

            continue

        try:
            es_positivo = valor > 0
        except TypeError:
            es_positivo = False

        if not es_positivo:
            mensajes.append(
                crear_mensaje_validacion(
                    nivel=NIVEL_ERROR,
                    fila=fila_excel,
                    campo=campo,
                    valor=valor,
                    mensaje=(
                        f"El campo {campo} debe contener "
                        "un número mayor a cero."
                    ),
                )
            )

    return mensajes


def contar_mensajes_por_nivel(mensajes):
    """
    Cuenta los mensajes agrupados por nivel.
    """

    mensajes = mensajes or []

    return {
        "errores": sum(
            1
            for mensaje in mensajes
            if mensaje.get("nivel") == NIVEL_ERROR
        ),
        "advertencias": sum(
            1
            for mensaje in mensajes
            if mensaje.get("nivel") == NIVEL_ADVERTENCIA
        ),
        "informativos": sum(
            1
            for mensaje in mensajes
            if mensaje.get("nivel") == NIVEL_INFO
        ),
    }


def generar_resumen_validacion(
    df,
    mensajes,
    campo_clave=None,
):
    """
    Genera el resumen general de una validación.
    """

    conteo = contar_mensajes_por_nivel(mensajes)

    resumen = {
        "total_registros": 0 if df is None else len(df),
        "errores": conteo["errores"],
        "advertencias": conteo["advertencias"],
        "informativos": conteo["informativos"],
        "valido": conteo["errores"] == 0,
    }

    if (
        df is not None
        and campo_clave
        and campo_clave in df.columns
    ):
        claves_validas = df[campo_clave].apply(
            lambda valor: None
            if esta_vacio(valor)
            else valor
        ).dropna()

        resumen["claves_unicas"] = claves_validas.nunique()
        resumen["duplicados_clave"] = int(
            claves_validas.duplicated().sum()
        )

    return resumen


def validar_carga_1_universo(
    df,
    fila_inicio_excel=8,
):
    """
    Ejecuta la validación de contenido para la Carga 1.

    Reglas:

    - CLAVE es obligatoria.
    - DESCRIPCION es obligatoria.
    - CANTIDAD_REQUERIDA es opcional.
    - No se permiten claves duplicadas.
    - No se compara la descripción contra la base de datos.
    """

    mensajes = []

    campos_base = [
        "CLAVE",
        "DESCRIPCION",
    ]

    mensajes.extend(
        validar_filas_vacias(
            df=df,
            campos_base=campos_base,
            fila_inicio_excel=fila_inicio_excel,
        )
    )

    if df is None:
        df_validado = pd.DataFrame()
    else:
        mascara_fila_con_datos = ~(
            df["CLAVE"].apply(esta_vacio)
            & df["DESCRIPCION"].apply(esta_vacio)
        )

        df_validado = df[
            mascara_fila_con_datos
        ].copy()

    mensajes.extend(
        validar_campos_obligatorios(
            df=df_validado,
            campos_obligatorios=campos_base,
            fila_inicio_excel=fila_inicio_excel,
        )
    )

    mensajes.extend(
        validar_duplicados(
            df=df_validado,
            campos=["CLAVE"],
            fila_inicio_excel=fila_inicio_excel,
            nivel=NIVEL_ERROR,
            mensaje="La clave aparece duplicada dentro del archivo.",
        )
    )

    mensajes.extend(
        validar_descripcion_distinta_por_clave(
            df=df_validado,
            campo_clave="CLAVE",
            campo_descripcion="DESCRIPCION",
            fila_inicio_excel=fila_inicio_excel,
        )
    )

    resumen = generar_resumen_validacion(
        df=df_validado,
        mensajes=mensajes,
        campo_clave="CLAVE",
    )

    return {
        "valido": resumen["valido"],
        "resumen": resumen,
        "mensajes": mensajes,
        "datos_validados": df_validado.reset_index(drop=True),
    }


__all__ = [
    "NIVEL_ERROR",
    "NIVEL_ADVERTENCIA",
    "NIVEL_INFO",
    "esta_vacio",
    "crear_mensaje_validacion",
    "validar_columnas_requeridas",
    "validar_campos_obligatorios",
    "validar_filas_vacias",
    "validar_duplicados",
    "validar_descripcion_distinta_por_clave",
    "validar_longitud_minima_texto",
    "validar_numero_positivo",
    "contar_mensajes_por_nivel",
    "generar_resumen_validacion",
    "validar_carga_1_universo",
]