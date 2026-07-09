"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_engine.py

Motor genérico de importación de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
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
        "errores": []
    }


def agregar_error(resultado, fila, error):
    resultado["success"] = False
    resultado["errores"].append({
        "fila": fila,
        "error": str(error)
    })


def procesar_dataframe(
    df,
    tabla,
    columnas_requeridas,
    funcion_procesar_fila,
    fila_inicial_excel=2
):
    """
    Procesa un DataFrame usando una función específica por fila.

    La función funcion_procesar_fila debe recibir una fila y devolver:

    {
        "accion": "insertado" | "actualizado" | "omitido"
    }
    """

    validar_columnas_requeridas(df, columnas_requeridas)

    resultado = crear_resultado_importacion(tabla)

    for index, row in df.iterrows():
        fila_excel = index + fila_inicial_excel

        try:
            respuesta = funcion_procesar_fila(row)

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

        except Exception as e:
            agregar_error(resultado, fila_excel, e)

    return resultado