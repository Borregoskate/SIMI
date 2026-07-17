"""Pruebas unitarias del controlador Streamlit Análisis por Proveedor."""

import importlib
import sys
import types

import pytest


class Contexto:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StreamlitFalso(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.llamadas = []

    def _guardar(self, nombre, *args, **kwargs):
        self.llamadas.append((nombre, args, kwargs))

    def header(self, *args, **kwargs): self._guardar("header", *args, **kwargs)
    def caption(self, *args, **kwargs): self._guardar("caption", *args, **kwargs)
    def subheader(self, *args, **kwargs): self._guardar("subheader", *args, **kwargs)
    def divider(self, *args, **kwargs): self._guardar("divider", *args, **kwargs)
    def info(self, *args, **kwargs): self._guardar("info", *args, **kwargs)
    def warning(self, *args, **kwargs): self._guardar("warning", *args, **kwargs)
    def error(self, *args, **kwargs): self._guardar("error", *args, **kwargs)
    def exception(self, *args, **kwargs): self._guardar("exception", *args, **kwargs)

    def columns(self, especificacion):
        return [ColumnaFalsa(self), ColumnaFalsa(self)]

    def tabs(self, nombres):
        self._guardar("tabs", nombres)
        return [Contexto() for _ in nombres]


class ColumnaFalsa:
    def __init__(self, st): self.st = st
    def markdown(self, *args, **kwargs): self.st._guardar("markdown", *args, **kwargs)
    def write(self, *args, **kwargs): self.st._guardar("write", *args, **kwargs)
    def metric(self, *args, **kwargs): self.st._guardar("metric", *args, **kwargs)


@pytest.fixture
def modulo(monkeypatch):
    st = StreamlitFalso()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    nombres_ui = {
        "competencia": "mostrar_competencia",
        "economia": "mostrar_desempeno_economico",
        "filtros": "mostrar_filtros_analisis_proveedor",
        "graficas": "mostrar_graficas_proveedor",
        "historial": "mostrar_historial_proveedor",
        "indicadores": "mostrar_indicadores_proveedor",
        "participacion": "mostrar_participacion",
        "tecnico": "mostrar_desempeno_tecnico",
    }
    llamadas_ui = []
    for nombre_modulo, nombre_funcion in nombres_ui.items():
        ruta = f"modules.analisis_proveedor_ui.{nombre_modulo}"
        falso = types.ModuleType(ruta)

        def construir(nombre):
            def funcion(*args, **kwargs):
                llamadas_ui.append((nombre, args, kwargs))
                if nombre == "mostrar_filtros_analisis_proveedor":
                    return {"id_proveedor": 1}
            return funcion

        setattr(falso, nombre_funcion, construir(nombre_funcion))
        monkeypatch.setitem(sys.modules, ruta, falso)

    servicio_modulo = types.ModuleType("services.analisis_proveedor_service")

    class ServicioFalso:
        resultado = {
            "proveedor": {"rfc": "AAA", "razon_social": "PROVEEDOR"},
            "tablas": {"participacion_operativa": [{"id": 1}]},
            "limitaciones": {"tipo_procedimiento_disponible": True},
        }

        def obtener_analisis_proveedor(self, **kwargs):
            return self.resultado

    servicio_modulo.AnalisisProveedorService = ServicioFalso
    monkeypatch.setitem(sys.modules, "services.analisis_proveedor_service", servicio_modulo)

    sys.modules.pop("modules.analisis_proveedor", None)
    importado = importlib.import_module("modules.analisis_proveedor")
    importado._st_falso = st
    importado._llamadas_ui = llamadas_ui
    importado._ServicioFalso = ServicioFalso
    return importado


def test_tiene_informacion_detecta_tablas(modulo):
    assert modulo._tiene_informacion({"tablas": {"participacion_operativa": [1]}}) is True
    assert modulo._tiene_informacion({"tablas": {"historial_adjudicaciones": [1]}}) is True
    assert modulo._tiene_informacion({"tablas": {"competidores": [1]}}) is True
    assert modulo._tiene_informacion({"tablas": {}}) is False


def test_encabezado(modulo):
    modulo._mostrar_encabezado()
    nombres = [item[0] for item in modulo._st_falso.llamadas]
    assert "header" in nombres
    assert "caption" in nombres


def test_contenido_distribuye_resultado_a_componentes(modulo):
    resultado = {
        "proveedor": {"rfc": "AAA", "razon_social": "PROVEEDOR"},
        "tablas": {"participacion_operativa": [1]},
        "limitaciones": {"tipo_procedimiento_disponible": True},
    }
    modulo._mostrar_contenido(resultado)
    nombres = [item[0] for item in modulo._llamadas_ui]
    assert "mostrar_indicadores_proveedor" in nombres
    assert "mostrar_participacion" in nombres
    assert "mostrar_desempeno_economico" in nombres
    assert "mostrar_desempeno_tecnico" in nombres
    assert "mostrar_competencia" in nombres
    assert "mostrar_historial_proveedor" in nombres
    assert "mostrar_graficas_proveedor" in nombres


def test_mostrar_analisis_proveedor_flujo_exitoso(modulo):
    modulo.mostrar_analisis_proveedor()
    nombres_ui = [item[0] for item in modulo._llamadas_ui]
    assert "mostrar_filtros_analisis_proveedor" in nombres_ui
    assert "mostrar_indicadores_proveedor" in nombres_ui
    assert not any(item[0] == "error" for item in modulo._st_falso.llamadas)


def test_mostrar_analisis_sin_filtros_muestra_info(modulo, monkeypatch):
    monkeypatch.setattr(modulo, "mostrar_filtros_analisis_proveedor", lambda service: None)
    modulo.mostrar_analisis_proveedor()
    assert any(item[0] == "info" for item in modulo._st_falso.llamadas)


def test_mostrar_analisis_captura_value_error(modulo, monkeypatch):
    class ServicioError:
        def obtener_analisis_proveedor(self, **kwargs):
            raise ValueError("Proveedor inválido")

    monkeypatch.setattr(modulo, "AnalisisProveedorService", ServicioError)
    modulo.mostrar_analisis_proveedor()
    assert any(item[0] == "warning" for item in modulo._st_falso.llamadas)


def test_mostrar_analisis_sin_datos_analiticos(modulo, monkeypatch):
    class ServicioSinDatos:
        def obtener_analisis_proveedor(self, **kwargs):
            return {
                "proveedor": {"rfc": "AAA", "razon_social": "PROVEEDOR"},
                "tablas": {},
            }

    monkeypatch.setattr(modulo, "AnalisisProveedorService", ServicioSinDatos)
    modulo.mostrar_analisis_proveedor()
    mensajes = [args[0] for nombre, args, _ in modulo._st_falso.llamadas if nombre == "info"]
    assert any("no cuenta con información analítica" in mensaje for mensaje in mensajes)
