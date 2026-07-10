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
Versión: 1.3.0
==============================================================
"""

from services.import_service import validar_columnas_requeridas


def crear_resultado_importacion(tabla="importacion"):
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
    columnas_requeridas,
    funcion_procesar_fila,
    tabla="importacion",
    fila_inicial_excel=2,
    conn=None,
    contexto=None,
    usar_transaccion=False,
    detener_en_error=False,
    **kwargs
):
    """
    Procesa un DataFrame usando una función específica por fila.

    Parámetros:
    - df: DataFrame que se procesará.
    - columnas_requeridas: columnas obligatorias.
    - funcion_procesar_fila: función particular de cada carga.
    - tabla: nombre lógico de la tabla o proceso.
    - fila_inicial_excel: número de la primera fila de datos.
    - conn: conexión activa a PostgreSQL.
    - contexto: información general opcional.
    - usar_transaccion: activa commit o rollback general.
    - detener_en_error: detiene el ciclo ante el primer error.
    - **kwargs: parámetros adicionales de cada carga.

    La función procesadora puede recibir:
    - row
    - row, conn
    - row, conn, contexto
    - row, conn y argumentos adicionales

    Debe devolver:
    {
        "accion": "insertado" | "actualizado" | "omitido",
        "advertencia": "mensaje opcional"
    }
    """

    resultado = crear_resultado_importacion(tabla)

    if funcion_procesar_fila is None:
        agregar_error(
            resultado,
            None,
            "No se recibió la función de procesamiento por fila."
        )
        return resultado

    try:
        validar_columnas_requeridas(
            df,
            columnas_requeridas
        )

        if usar_transaccion and conn is None:
            raise ValueError(
                "Se solicitó una transacción, pero no se recibió "
                "una conexión activa."
            )

        if usar_transaccion:
            conn.autocommit = False

        for index, row in df.iterrows():
            fila_excel = index + fila_inicial_excel

            try:
                respuesta = _ejecutar_funcion_procesar_fila(
                    funcion_procesar_fila=funcion_procesar_fila,
                    row=row,
                    conn=conn,
                    contexto=contexto,
                    parametros_adicionales=kwargs
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

        if usar_transaccion:
            if resultado["success"]:
                conn.commit()
            else:
                conn.rollback()

                # Si hubo rollback, ningún registro quedó guardado.
                resultado["procesados"] = 0
                resultado["insertados"] = 0
                resultado["actualizados"] = 0
                resultado["omitidos"] = 0

    except Exception as error:
        # Evita registrar dos veces el mismo error cuando
        # detener_en_error=True.
        mensaje = str(error)

        if not any(
            item.get("error") == mensaje
            for item in resultado["errores"]
        ):
            agregar_error(
                resultado=resultado,
                fila=None,
                error=error
            )

        if usar_transaccion and conn:
            conn.rollback()

            resultado["procesados"] = 0
            resultado["insertados"] = 0
            resultado["actualizados"] = 0
            resultado["omitidos"] = 0

    return resultado


def _ejecutar_funcion_procesar_fila(
    funcion_procesar_fila,
    row,
    conn=None,
    contexto=None,
    parametros_adicionales=None
):
    """
    Ejecuta la función específica de procesamiento.

    Mantiene compatibilidad con las cargas anteriores y
    permite argumentos adicionales para las cargas nuevas.
    """

    parametros_adicionales = parametros_adicionales or {}

    if conn is not None and contexto is not None:
        return funcion_procesar_fila(
            row,
            conn,
            contexto,
            **parametros_adicionales
        )

    if conn is not None:
        return funcion_procesar_fila(
            row,
            conn,
            **parametros_adicionales
        )

    if contexto is not None:
        return funcion_procesar_fila(
            row,
            contexto=contexto,
            **parametros_adicionales
        )

    return funcion_procesar_fila(
        row,
        **parametros_adicionales
    )


def _interpretar_respuesta(
    respuesta,
    resultado,
    fila_excel
):
    """
    Interpreta la respuesta del procesamiento de una fila.
    """

    if not respuesta:
        respuesta = {
            "accion": "omitido"
        }

    if not isinstance(respuesta, dict):
        raise ValueError(
            "La función de procesamiento debe devolver "
            "un diccionario."
        )

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

    advertencia = (
        respuesta.get("advertencia")
        or respuesta.get("mensaje")
    )

    if advertencia:
        agregar_advertencia(
            resultado=resultado,
            fila=fila_excel,
            advertencia=advertencia
        )