"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

import_result.py

Objeto estándar de resultado para procesos de importación.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""


class ImportResult:
    def __init__(self, tabla=None):
        self.success = True
        self.tabla = tabla

        self.procesados = 0
        self.insertados = 0
        self.actualizados = 0
        self.omitidos = 0

        self.errores = []
        self.advertencias = []

    def registrar_procesado(self):
        self.procesados += 1

    def registrar_insertado(self):
        self.insertados += 1

    def registrar_actualizado(self):
        self.actualizados += 1

    def registrar_omitido(self):
        self.omitidos += 1

    def registrar_error(self, mensaje, fila=None):
        self.success = False

        if fila is not None:
            mensaje = f"Fila {fila}: {mensaje}"

        self.errores.append(mensaje)

    def registrar_advertencia(self, mensaje, fila=None):
        if fila is not None:
            mensaje = f"Fila {fila}: {mensaje}"

        self.advertencias.append(mensaje)

    def to_dict(self):
        return {
            "success": self.success,
            "tabla": self.tabla,
            "procesados": self.procesados,
            "insertados": self.insertados,
            "actualizados": self.actualizados,
            "omitidos": self.omitidos,
            "errores": self.errores,
            "advertencias": self.advertencias,
        }