"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_engine.py

Motor genérico para procesamiento de DataFrames.

Este archivo NO abre conexiones y NO administra transacciones.
La transacción debe ser controlada por el Service correspondiente
mediante services.database_service.database_transaction.

Autor: Jorge Saavedra
Versión: 3.0.0
==============================================================
"""

from services.import_service import validar_columnas_requeridas


ACCIONES_VALIDAS = {"insertado", "actualizado", "omitido"}


class ImportacionConErrores(Exception):
    """Excepción controlada para solicitar rollback sin perder el resultado."""

    def __init__(self, resultado):
        self.resultado = resultado
        super().__init__("La importación contiene errores.")


def crear_resultado_importacion(tabla="importacion"):
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
    resultado["success"] = False
    resultado["errores"].append({"fila": fila, "error": str(error)})


def agregar_advertencia(resultado, fila, advertencia):
    resultado["advertencias"].append(
        {"fila": fila, "advertencia": str(advertencia)}
    )


def procesar_dataframe(
    df,
    columnas_requeridas,
    funcion_procesar_fila,
    tabla="importacion",
    fila_inicial_excel=2,
    conn=None,
    contexto=None,
    detener_en_error=False,
    **kwargs,
):
    """Procesa un DataFrame sin administrar la conexión recibida."""

    resultado = crear_resultado_importacion(tabla)

    _validar_parametros_procesamiento(
        df=df,
        columnas_requeridas=columnas_requeridas,
        funcion_procesar_fila=funcion_procesar_fila,
        fila_inicial_excel=fila_inicial_excel,
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
            agregar_error(resultado, fila_excel, error)
            if detener_en_error:
                break

    return resultado


def exigir_importacion_exitosa(resultado):
    """Provoca rollback desde el Service cuando el motor detectó errores."""

    if not resultado.get("success", False):
        raise ImportacionConErrores(resultado)
    return resultado


def _validar_parametros_procesamiento(
    df,
    columnas_requeridas,
    funcion_procesar_fila,
    fila_inicial_excel,
):
    if funcion_procesar_fila is None:
        raise ValueError("No se recibió la función de procesamiento por fila.")
    if not callable(funcion_procesar_fila):
        raise TypeError("La función de procesamiento por fila no es ejecutable.")
    if not isinstance(fila_inicial_excel, int):
        raise TypeError("La fila inicial de Excel debe ser un número entero.")
    if fila_inicial_excel < 1:
        raise ValueError("La fila inicial de Excel debe ser mayor o igual a 1.")

    validar_columnas_requeridas(
        df=df,
        columnas_requeridas=columnas_requeridas,
    )


def _ejecutar_funcion_procesar_fila(
    funcion_procesar_fila,
    row,
    conn=None,
    contexto=None,
    parametros_adicionales=None,
):
    parametros_adicionales = parametros_adicionales or {}

    if conn is not None and contexto is not None:
        return funcion_procesar_fila(
            row, conn, contexto, **parametros_adicionales
        )
    if conn is not None:
        return funcion_procesar_fila(row, conn, **parametros_adicionales)
    if contexto is not None:
        return funcion_procesar_fila(
            row, contexto=contexto, **parametros_adicionales
        )
    return funcion_procesar_fila(row, **parametros_adicionales)


def _interpretar_respuesta(respuesta, resultado, fila_excel):
    if respuesta is None:
        respuesta = {"accion": "omitido"}
    if not isinstance(respuesta, dict):
        raise TypeError("La función de procesamiento debe devolver un diccionario.")

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
    else:
        resultado["omitidos"] += 1

    advertencia = respuesta.get("advertencia") or respuesta.get("mensaje")
    if advertencia:
        agregar_advertencia(resultado, fila_excel, advertencia)


__all__ = [
    "ImportacionConErrores",
    "crear_resultado_importacion",
    "agregar_error",
    "agregar_advertencia",
    "procesar_dataframe",
    "exigir_importacion_exitosa",
]
