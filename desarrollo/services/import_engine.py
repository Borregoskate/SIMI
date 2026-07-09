"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_engine.py

Motor genérico de importación de datos.

Autor: Jorge Saavedra
Versión: 1.1.0
==============================================================
"""

from services.import_service import validar_columnas_requeridas


def crear_resultado_importacion(tabla):
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
    resultado["success"] = False
    resultado["errores"].append({
        "fila": fila,
        "error": str(error)
    })


def agregar_advertencia(resultado, fila, advertencia):
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
    detener_en_error=False
):
    """
    Procesa un DataFrame usando una función específica por fila.

    La función funcion_procesar_fila puede recibir:
    - row
    - row, conn
    - row, conn, contexto

    Y debe devolver:

    {
        "accion": "insertado" | "actualizado" | "omitido",
        "advertencia": "mensaje opcional"
    }
    """

    resultado = crear_resultado_importacion(tabla)

    try:
        validar_columnas_requeridas(df, columnas_requeridas)

        if usar_transaccion and conn:
            conn.autocommit = False

        for index, row in df.iterrows():
            fila_excel = index + fila_inicial_excel

            try:
                respuesta = _ejecutar_funcion_procesar_fila(
                    funcion_procesar_fila=funcion_procesar_fila,
                    row=row,
                    conn=conn,
                    contexto=contexto
                )

                _interpretar_respuesta(
                    respuesta=respuesta,
                    resultado=resultado,
                    fila_excel=fila_excel
                )

            except Exception as e:
                agregar_error(resultado, fila_excel, e)

                if detener_en_error:
                    raise

        if usar_transaccion and conn:
            if resultado["success"]:
                conn.commit()
            else:
                conn.rollback()

    except Exception as e:
        agregar_error(resultado, None, e)

        if usar_transaccion and conn:
            conn.rollback()

    return resultado


def _ejecutar_funcion_procesar_fila(
    funcion_procesar_fila,
    row,
    conn=None,
    contexto=None
):
    """
    Ejecuta la función específica de procesamiento.

    Mantiene compatibilidad con funciones anteriores que solo reciben row.
    """

    if conn is not None and contexto is not None:
        return funcion_procesar_fila(row, conn, contexto)

    if conn is not None:
        return funcion_procesar_fila(row, conn)

    return funcion_procesar_fila(row)


def _interpretar_respuesta(respuesta, resultado, fila_excel):
    """
    Interpreta la respuesta de cada fila.
    """

    if not respuesta:
        respuesta = {"accion": "omitido"}

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
            "La función de procesamiento no devolvió una acción válida."
        )

    advertencia = respuesta.get("advertencia")

    if advertencia:
        agregar_advertencia(resultado, fila_excel, advertencia)