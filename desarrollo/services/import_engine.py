"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_engine.py

Motor genérico de importación de datos.

Permite procesar DataFrames mediante una función específica
por fila, utilizando conexión, contexto y parámetros
adicionales de cada tipo de carga.

Autor: Jorge Saavedra
Versión: 1.2.0
==============================================================
"""

from services.import_service import validar_columnas_requeridas


def crear_resultado_importacion(tabla):
    """
    Crea la estructura estándar del resultado de importación.
    """

    return {
        "success": True,
        "tabla": tabla,
        "procesados": 0,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": 0,
        "errores": [],
        "advertencias": []
    }


def agregar_error(resultado, fila, error):
    """
    Agrega un error al resultado general.
    """

    resultado["success"] = False

    resultado["errores"].append({
        "fila": fila,
        "error": str(error)
    })


def agregar_advertencia(resultado, fila, advertencia):
    """
    Agrega una advertencia al resultado general.
    """

    resultado["advertencias"].append({
        "fila": fila,
        "advertencia": str(advertencia)
    })


def procesar_dataframe(
    df,
    tabla,
    columnas_requeridas,
    funcion_procesar_fila,
    fila_inicial_excel=2,
    conn=None,
    contexto=None,
    usar_transaccion=False,
    detener_en_error=False,
    **kwargs
):
    """
    Procesa un DataFrame usando una función específica por fila.

    La función procesadora puede recibir:

    - row
    - row, conn
    - row, conn, contexto
    - row, conn y parámetros adicionales mediante **kwargs

    Ejemplo de parámetros adicionales:

        id_procedimiento=1

    La función específica debe devolver:

    {
        "accion": "insertado" | "actualizado" | "omitido",
        "advertencia": "mensaje opcional"
    }
    """

    resultado = crear_resultado_importacion(tabla)

    try:
        validar_columnas_requeridas(
            df,
            columnas_requeridas
        )

        if usar_transaccion and conn:
            conn.autocommit = False

        for index, row in df.iterrows():
            fila_excel = index + fila_inicial_excel

            try:
                respuesta = _ejecutar_funcion_procesar_fila(
                    funcion_procesar_fila=funcion_procesar_fila,
                    row=row,
                    conn=conn,
                    contexto=contexto,
                    kwargs=kwargs
                )

                _interpretar_respuesta(
                    respuesta=respuesta,
                    resultado=resultado,
                    fila_excel=fila_excel
                )

            except Exception as error:
                agregar_error(
                    resultado=resultado,
                    fila=fila_excel,
                    error=error
                )

                if detener_en_error:
                    raise

        if usar_transaccion and conn:
            if resultado["success"]:
                conn.commit()
            else:
                conn.rollback()

    except Exception as error:
        agregar_error(
            resultado=resultado,
            fila=None,
            error=error
        )

        if usar_transaccion and conn:
            conn.rollback()

    return resultado


def _ejecutar_funcion_procesar_fila(
    funcion_procesar_fila,
    row,
    conn=None,
    contexto=None,
    kwargs=None
):
    """
    Ejecuta la función específica de procesamiento.

    Mantiene compatibilidad con las cargas anteriores y
    permite enviar argumentos adicionales para cargas nuevas.
    """

    kwargs = kwargs or {}

    # Conexión, contexto y parámetros adicionales.
    if conn is not None and contexto is not None and kwargs:
        return funcion_procesar_fila(
            row,
            conn,
            contexto,
            **kwargs
        )

    # Conexión y parámetros adicionales.
    if conn is not None and kwargs:
        return funcion_procesar_fila(
            row,
            conn,
            **kwargs
        )

    # Contexto y parámetros adicionales, sin conexión.
    if contexto is not None and kwargs:
        return funcion_procesar_fila(
            row,
            contexto=contexto,
            **kwargs
        )

    # Únicamente parámetros adicionales.
    if kwargs:
        return funcion_procesar_fila(
            row,
            **kwargs
        )

    # Compatibilidad con el funcionamiento anterior.
    if conn is not None and contexto is not None:
        return funcion_procesar_fila(
            row,
            conn,
            contexto
        )

    if conn is not None:
        return funcion_procesar_fila(
            row,
            conn
        )

    if contexto is not None:
        return funcion_procesar_fila(
            row,
            contexto
        )

    return funcion_procesar_fila(row)


def _interpretar_respuesta(
    respuesta,
    resultado,
    fila_excel
):
    """
    Interpreta la respuesta devuelta por el procesamiento
    específico de cada fila.
    """

    if not respuesta:
        respuesta = {
            "accion": "omitido"
        }

    accion = respuesta.get("accion")

    if accion == "insertado":
        resultado["insertados"] += 1
        resultado["procesados"] += 1

    elif accion == "actualizado":
        resultado["actualizados"] += 1
        resultado["procesados"] += 1

    elif accion == "omitido":
        resultado["omitidos"] += 1

    else:
        raise ValueError(
            "La función de procesamiento no devolvió "
            "una acción válida."
        )

    advertencia = respuesta.get("advertencia")

    if advertencia:
        agregar_advertencia(
            resultado=resultado,
            fila=fila_excel,
            advertencia=advertencia
        )
