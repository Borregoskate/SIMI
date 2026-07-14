"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_engine.py

Motor genérico para procesamiento de DataFrames.

Responsabilidades:

1. Validar la entrada del proceso.
2. Recorrer las filas de un DataFrame.
3. Ejecutar una función específica por fila.
4. Interpretar la respuesta de cada fila.
5. Construir un resultado estándar.
6. Registrar errores y advertencias.

IMPORTANTE:

La administración transaccional incluida en este archivo se conserva
temporalmente por compatibilidad con las cargas existentes.

Durante la homologación de los Services de importación, las
transacciones serán trasladadas definitivamente a:

    services.database_service.database_transaction

Después de esa migración se retirará el parámetro:

    usar_transaccion

Autor: Jorge Saavedra
Versión: 2.0.0
==============================================================
"""

from services.import_service import validar_columnas_requeridas


ACCIONES_VALIDAS = {
    "insertado",
    "actualizado",
    "omitido",
}


def crear_resultado_importacion(tabla="importacion"):
    """
    Crea la estructura estándar de resultado de una importación.
    """

    return {
        "success": True,
        "tabla": tabla,
        "procesados": 0,
        "insertados": 0,
        "actualizados": 0,
        "omitidos": 0,
        "errores": [],
        "advertencias": [],
    }


def agregar_error(resultado, fila, error):
    """
    Registra un error dentro del resultado general.
    """

    resultado["success"] = False

    resultado["errores"].append(
        {
            "fila": fila,
            "error": str(error),
        }
    )


def agregar_advertencia(resultado, fila, advertencia):
    """
    Registra una advertencia dentro del resultado general.
    """

    resultado["advertencias"].append(
        {
            "fila": fila,
            "advertencia": str(advertencia),
        }
    )


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
    **kwargs,
):
    """
    Procesa un DataFrame mediante una función específica por fila.

    Parámetros:
        df:
            DataFrame que será procesado.

        columnas_requeridas:
            Columnas obligatorias del DataFrame.

        funcion_procesar_fila:
            Función encargada de procesar cada fila.

        tabla:
            Nombre lógico de la tabla o proceso.

        fila_inicial_excel:
            Número de Excel correspondiente a la primera fila de datos.

        conn:
            Conexión activa opcional.

        contexto:
            Información general opcional para todas las filas.

        usar_transaccion:
            Compatibilidad temporal con servicios anteriores.

            Este parámetro será retirado cuando todos los servicios de
            importación utilicen database_transaction().

        detener_en_error:
            Cuando es True, detiene el procesamiento ante el primer
            error.

        **kwargs:
            Parámetros adicionales enviados a la función procesadora.

    La función procesadora debe devolver:

        {
            "accion": "insertado" | "actualizado" | "omitido",
            "advertencia": "mensaje opcional",
        }
    """

    resultado = crear_resultado_importacion(tabla)

    try:
        _validar_parametros_procesamiento(
            df=df,
            columnas_requeridas=columnas_requeridas,
            funcion_procesar_fila=funcion_procesar_fila,
            fila_inicial_excel=fila_inicial_excel,
            conn=conn,
            usar_transaccion=usar_transaccion,
        )

        _preparar_transaccion_compatible(
            conn=conn,
            usar_transaccion=usar_transaccion,
        )

        for posicion, (_, row) in enumerate(df.iterrows()):
            fila_excel = fila_inicial_excel + posicion

            try:
                respuesta = _ejecutar_funcion_procesar_fila(
                    funcion_procesar_fila=funcion_procesar_fila,
                    row=row,
                    conn=conn,
                    contexto=contexto,
                    parametros_adicionales=kwargs,
                )

                _interpretar_respuesta(
                    respuesta=respuesta,
                    resultado=resultado,
                    fila_excel=fila_excel,
                )

            except Exception as error:
                agregar_error(
                    resultado=resultado,
                    fila=fila_excel,
                    error=error,
                )

                if detener_en_error:
                    raise

        _finalizar_transaccion_compatible(
            resultado=resultado,
            conn=conn,
            usar_transaccion=usar_transaccion,
        )

    except Exception as error:
        _registrar_error_general_si_corresponde(
            resultado=resultado,
            error=error,
        )

        _revertir_transaccion_compatible(
            conn=conn,
            usar_transaccion=usar_transaccion,
        )

        if usar_transaccion:
            _reiniciar_contadores(resultado)

    return resultado


def _validar_parametros_procesamiento(
    df,
    columnas_requeridas,
    funcion_procesar_fila,
    fila_inicial_excel,
    conn,
    usar_transaccion,
):
    """
    Valida los parámetros generales del motor.
    """

    if funcion_procesar_fila is None:
        raise ValueError(
            "No se recibió la función de procesamiento por fila."
        )

    if not callable(funcion_procesar_fila):
        raise TypeError(
            "La función de procesamiento por fila no es ejecutable."
        )

    if not isinstance(fila_inicial_excel, int):
        raise TypeError(
            "La fila inicial de Excel debe ser un número entero."
        )

    if fila_inicial_excel < 1:
        raise ValueError(
            "La fila inicial de Excel debe ser mayor o igual a 1."
        )

    validar_columnas_requeridas(
        df=df,
        columnas_requeridas=columnas_requeridas,
    )

    if usar_transaccion and conn is None:
        raise ValueError(
            "Se solicitó una transacción, pero no se recibió "
            "una conexión activa."
        )


def _ejecutar_funcion_procesar_fila(
    funcion_procesar_fila,
    row,
    conn=None,
    contexto=None,
    parametros_adicionales=None,
):
    """
    Ejecuta la función específica de procesamiento.

    Mantiene compatibilidad con las firmas utilizadas actualmente por
    las diferentes cargas.
    """

    parametros_adicionales = parametros_adicionales or {}

    if conn is not None and contexto is not None:
        return funcion_procesar_fila(
            row,
            conn,
            contexto,
            **parametros_adicionales,
        )

    if conn is not None:
        return funcion_procesar_fila(
            row,
            conn,
            **parametros_adicionales,
        )

    if contexto is not None:
        return funcion_procesar_fila(
            row,
            contexto=contexto,
            **parametros_adicionales,
        )

    return funcion_procesar_fila(
        row,
        **parametros_adicionales,
    )


def _interpretar_respuesta(
    respuesta,
    resultado,
    fila_excel,
):
    """
    Interpreta la respuesta devuelta por el procesador de una fila.
    """

    if respuesta is None:
        respuesta = {
            "accion": "omitido",
        }

    if not isinstance(respuesta, dict):
        raise TypeError(
            "La función de procesamiento debe devolver un diccionario."
        )

    accion = respuesta.get("accion")

    if accion not in ACCIONES_VALIDAS:
        raise ValueError(
            "La función de procesamiento no devolvió una acción válida. "
            "Las acciones permitidas son: "
            + ", ".join(sorted(ACCIONES_VALIDAS))
            + "."
        )

    if accion == "insertado":
        resultado["insertados"] += 1
        resultado["procesados"] += 1

    elif accion == "actualizado":
        resultado["actualizados"] += 1
        resultado["procesados"] += 1

    elif accion == "omitido":
        resultado["omitidos"] += 1

    advertencia = (
        respuesta.get("advertencia")
        or respuesta.get("mensaje")
    )

    if advertencia:
        agregar_advertencia(
            resultado=resultado,
            fila=fila_excel,
            advertencia=advertencia,
        )


def _registrar_error_general_si_corresponde(
    resultado,
    error,
):
    """
    Evita registrar dos veces un mismo error.
    """

    mensaje = str(error)

    error_ya_registrado = any(
        item.get("error") == mensaje
        for item in resultado["errores"]
    )

    if not error_ya_registrado:
        agregar_error(
            resultado=resultado,
            fila=None,
            error=error,
        )


def _preparar_transaccion_compatible(
    conn,
    usar_transaccion,
):
    """
    Compatibilidad temporal con los Services anteriores.

    Esta función será eliminada cuando la transacción se administre
    exclusivamente mediante database_transaction().
    """

    if usar_transaccion:
        conn.autocommit = False


def _finalizar_transaccion_compatible(
    resultado,
    conn,
    usar_transaccion,
):
    """
    Confirma o revierte temporalmente la transacción.

    Esta responsabilidad será retirada del motor durante el Bloque 3.
    """

    if not usar_transaccion:
        return

    if resultado["success"]:
        conn.commit()
        return

    conn.rollback()
    _reiniciar_contadores(resultado)


def _revertir_transaccion_compatible(
    conn,
    usar_transaccion,
):
    """
    Ejecuta rollback en el mecanismo temporal de compatibilidad.
    """

    if usar_transaccion and conn is not None:
        conn.rollback()


def _reiniciar_contadores(resultado):
    """
    Reinicia los contadores cuando la transacción completa fue
    revertida.
    """

    resultado["procesados"] = 0
    resultado["insertados"] = 0
    resultado["actualizados"] = 0
    resultado["omitidos"] = 0