"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

test_comparador_im_service_014_2_3.py

Pruebas unitarias e integrales del bloque 014.2.3:
- Conversión de entrada.
- Normalización de columnas.
- Preparación y validación de filas.
- Resolución de claves.
- Agrupación del contexto.
- Análisis por clave.
- Resumen general.
- Tablas y datos para gráficas.
- Orquestación completa.

No requieren conexión real a base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal

from services.comparador_im_service import (
    ComparadorIMService,
)


CONEXION_PRUEBA = object()


class DataFrameFalso:
    def __init__(self, registros):
        self.registros = registros

    def to_dict(self, orient="records"):
        assert orient == "records"
        return self.registros


class RepositoryFalso:
    def __init__(self):
        self.llamadas = []

    def obtener_claves_por_codigos(
        self,
        claves,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_claves_por_codigos",
                claves,
                conn,
            )
        )

        catalogo = {
            "010.000.001": {
                "id_clave": 1,
                "clave": "010.000.001",
                "descripcion": "CLAVE UNO",
                "id_categoria": 10,
                "categoria": "MEDICAMENTOS",
            },
            "010.000.002": {
                "id_clave": 2,
                "clave": "010.000.002",
                "descripcion": "CLAVE DOS",
                "id_categoria": 20,
                "categoria": "MATERIAL DE CURACION",
            },
        }

        return [
            catalogo[clave]
            for clave in claves
            if clave in catalogo
        ]

    def obtener_contexto_comparacion(
        self,
        ids_clave,
        conn=None,
    ):
        self.llamadas.append(
            (
                "obtener_contexto_comparacion",
                ids_clave,
                conn,
            )
        )

        claves = [
            {
                "id_clave": 1,
                "clave": "010.000.001",
                "descripcion": "CLAVE UNO",
                "id_categoria": 10,
                "categoria": "MEDICAMENTOS",
            },
            {
                "id_clave": 2,
                "clave": "010.000.002",
                "descripcion": "CLAVE DOS",
                "id_categoria": 20,
                "categoria": "MATERIAL DE CURACION",
            },
        ]

        propuestas = [
            {
                "id_clave": 1,
                "tipo_propuesta": "INICIAL",
                "resultado_tecnico": "POSITIVA",
                "precio_unitario": 110,
            },
            {
                "id_clave": 1,
                "tipo_propuesta": "SUBASTA",
                "resultado_tecnico": "POSITIVA",
                "precio_unitario": 100,
            },
            {
                "id_clave": 2,
                "tipo_propuesta": "INICIAL",
                "resultado_tecnico": "NEGATIVA",
                "precio_unitario": 55,
            },
        ]

        operativas = [
            {
                "id_clave": 1,
                "origen_dato": "OPERATIVO",
                "ejercicio": 2025,
                "numero_procedimiento": "PROC-2025",
                "id_procedimiento": 100,
                "precio_unitario_adjudicado": 105,
            },
            {
                "id_clave": 1,
                "origen_dato": "OPERATIVO",
                "ejercicio": 2026,
                "numero_procedimiento": "PROC-2026",
                "id_procedimiento": 101,
                "precio_unitario_adjudicado": 115,
            },
        ]

        historicas = [
            {
                "id_clave": 1,
                "origen_dato": "HISTORICO",
                "ejercicio": 2024,
                "numero_procedimiento": "HIST-2024",
                "id_procedimiento": None,
                "precio_unitario_adjudicado": 100,
            }
        ]

        return {
            "claves": [
                registro
                for registro in claves
                if registro["id_clave"] in ids_clave
            ],
            "propuestas": [
                registro
                for registro in propuestas
                if registro["id_clave"] in ids_clave
            ],
            "adjudicaciones_operativas": [
                registro
                for registro in operativas
                if registro["id_clave"] in ids_clave
            ],
            "adjudicaciones_historicas": [
                registro
                for registro in historicas
                if registro["id_clave"] in ids_clave
            ],
        }


def test_convertir_registros_lista():
    registros = [{"clave": "010.000.001"}]

    resultado = ComparadorIMService._convertir_registros(
        registros
    )

    assert resultado == registros


def test_convertir_registros_dataframe():
    registros = [{"clave": "010.000.001"}]
    dataframe = DataFrameFalso(registros)

    resultado = ComparadorIMService._convertir_registros(
        dataframe
    )

    assert resultado == registros


def test_convertir_registros_none():
    assert ComparadorIMService._convertir_registros(None) == []


def test_normalizar_claves_registro_aplica_aliases():
    registro = {
        "RAZON SOCIAL": "Proveedor SA de CV",
        "PAIS DE ORIGEN": "México",
        "PRECIO": 100,
        "CANTIDAD": 20,
    }

    resultado = (
        ComparadorIMService._normalizar_claves_registro(
            registro
        )
    )

    assert resultado == {
        "razon_social": "Proveedor SA de CV",
        "pais_origen": "México",
        "precio_unitario": 100,
        "cantidad_ofertada": 20,
    }


def test_normalizar_registro_im_valido():
    resultado = ComparadorIMService.normalizar_registro_im(
        {
            "RFC": "abc010101aa1",
            "RAZON SOCIAL": "Proveedor sa de cv",
            "CLAVE": "010.000.001",
            "DESCRIPCION": "Producto",
            "CANTIDAD": "1000",
            "PAIS DE ORIGEN": "México",
            "PRECIO UNITARIO": "125.50",
        },
        numero_fila=2,
    )

    assert resultado["incidencias"] == []
    assert resultado["numero_fila"] == 2

    registro = resultado["registro"]

    assert registro["rfc"] == "ABC010101AA1"
    assert registro["clave"] == "010.000.001"
    assert registro["cantidad_ofertada"] == Decimal("1000")
    assert registro["precio_unitario"] == Decimal("125.50")
    assert registro["numero_fila"] == 2


def test_normalizar_registro_im_invalido():
    resultado = ComparadorIMService.normalizar_registro_im(
        {
            "RFC": "",
            "RAZON SOCIAL": "",
            "CLAVE": "",
            "CANTIDAD": 0,
            "PRECIO UNITARIO": -1,
        },
        numero_fila=3,
    )

    assert len(resultado["incidencias"]) == 5
    assert "RFC requerido." in resultado["incidencias"]
    assert "Razón social requerida." in resultado["incidencias"]
    assert "Clave requerida." in resultado["incidencias"]


def test_preparar_registros_im_separa_validos_e_invalidos():
    resultado = ComparadorIMService.preparar_registros_im(
        [
            {
                "RFC": "ABC010101AA1",
                "RAZON SOCIAL": "Proveedor SA de CV",
                "CLAVE": "010.000.001",
                "CANTIDAD": 100,
                "PRECIO": 50,
            },
            {
                "RFC": "",
                "RAZON SOCIAL": "",
                "CLAVE": "",
                "CANTIDAD": 0,
                "PRECIO": 0,
            },
        ]
    )

    assert resultado["total_filas_recibidas"] == 2
    assert len(resultado["registros_validos"]) == 1
    assert len(resultado["registros_invalidos"]) == 1
    assert resultado["registros_validos"][0]["numero_fila"] == 2
    assert resultado["registros_invalidos"][0]["numero_fila"] == 3


def test_resolver_claves_im():
    repository = RepositoryFalso()
    service = ComparadorIMService(repository=repository)

    registros = [
        {
            "numero_fila": 2,
            "clave": "010.000.001",
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR",
        },
        {
            "numero_fila": 3,
            "clave": "999.999.999",
            "rfc": "XYZ010101AA1",
            "razon_social": "OTRO",
        },
    ]

    resultado = service.resolver_claves_im(
        registros,
        conn=CONEXION_PRUEBA,
    )

    assert len(resultado["registros_resueltos"]) == 1
    assert resultado["registros_resueltos"][0]["id_clave"] == 1
    assert resultado["registros_resueltos"][0]["categoria"] == "MEDICAMENTOS"

    assert len(resultado["claves_no_encontradas"]) == 1
    assert (
        resultado["claves_no_encontradas"][0]["clave"]
        == "999.999.999"
    )

    assert repository.llamadas == [
        (
            "obtener_claves_por_codigos",
            ["010.000.001", "999.999.999"],
            CONEXION_PRUEBA,
        )
    ]


def test_agrupar_contexto_por_clave():
    contexto = {
        "claves": [
            {"id_clave": 1, "clave": "A"},
            {"id_clave": 2, "clave": "B"},
        ],
        "propuestas": [
            {"id_clave": 1, "id_propuesta": 10},
        ],
        "adjudicaciones_operativas": [
            {"id_clave": 1, "id_adjudicacion": 20},
        ],
        "adjudicaciones_historicas": [
            {
                "id_clave": 2,
                "id_adjudicacion_historica": 30,
            },
        ],
    }

    resultado = (
        ComparadorIMService.agrupar_contexto_por_clave(
            contexto
        )
    )

    assert set(resultado) == {1, 2}
    assert len(resultado[1]["propuestas"]) == 1
    assert len(resultado[1]["adjudicaciones_operativas"]) == 1
    assert len(resultado[2]["adjudicaciones_historicas"]) == 1


def test_construir_resumen_cotizaciones_clave():
    cotizaciones = [
        {
            "precio_unitario": Decimal("100"),
            "precio_im": Decimal("100"),
            "clasificacion_desviacion": "EN MERCADO",
            "nivel_riesgo": "BAJO",
        },
        {
            "precio_unitario": Decimal("120"),
            "precio_im": Decimal("120"),
            "clasificacion_desviacion": "ELEVADO",
            "nivel_riesgo": "ALTO",
        },
    ]

    resultado = (
        ComparadorIMService.construir_resumen_cotizaciones_clave(
            cotizaciones
        )
    )

    assert resultado["total_cotizaciones_im"] == 2
    assert resultado["precio_minimo_im"] == Decimal("100.00")
    assert resultado["precio_maximo_im"] == Decimal("120.00")
    assert resultado["cotizaciones_en_mercado"] == 1
    assert resultado["cotizaciones_elevadas"] == 1
    assert resultado["riesgo_clave"] == "ALTO"
    assert (
        resultado["mejor_cotizacion_im"]["precio_im"]
        == Decimal("100")
    )


def test_construir_analisis_clave():
    clave_catalogo = {
        "id_clave": 1,
        "clave": "010.000.001",
        "descripcion": "CLAVE UNO",
        "id_categoria": 10,
        "categoria": "MEDICAMENTOS",
    }
    cotizaciones = [
        {
            "numero_fila": 2,
            "id_clave": 1,
            "clave": "010.000.001",
            "rfc": "ABC010101AA1",
            "razon_social": "PROVEEDOR",
            "cantidad_ofertada": Decimal("100"),
            "precio_unitario": Decimal("110"),
        }
    ]
    contexto = {
        "propuestas": [],
        "adjudicaciones_operativas": [
            {
                "id_clave": 1,
                "origen_dato": "OPERATIVO",
                "ejercicio": 2025,
                "numero_procedimiento": "P-2025",
                "id_procedimiento": 1,
                "precio_unitario_adjudicado": 100,
            },
            {
                "id_clave": 1,
                "origen_dato": "OPERATIVO",
                "ejercicio": 2026,
                "numero_procedimiento": "P-2026",
                "id_procedimiento": 2,
                "precio_unitario_adjudicado": 110,
            },
        ],
        "adjudicaciones_historicas": [
            {
                "id_clave": 1,
                "origen_dato": "HISTORICO",
                "ejercicio": 2024,
                "numero_procedimiento": "H-2024",
                "id_procedimiento": None,
                "precio_unitario_adjudicado": 90,
            }
        ],
    }

    resultado = ComparadorIMService.construir_analisis_clave(
        clave_catalogo=clave_catalogo,
        cotizaciones_im=cotizaciones,
        contexto_clave=contexto,
    )

    assert resultado["id_clave"] == 1
    assert resultado["referencia"]["fuente_referencia"] == "ADJUDICACIONES"
    assert resultado["referencia"]["precio_referencia"] == Decimal("100.00")
    assert resultado["nivel_confianza"] == "BAJA"
    assert len(resultado["cotizaciones"]) == 1
    assert (
        resultado["cotizaciones"][0][
            "clasificacion_desviacion"
        ]
        == "LIGERAMENTE ELEVADO"
    )


def test_construir_resumen_general():
    preparacion = {
        "total_filas_recibidas": 4,
        "registros_validos": [
            {"clave": "A"},
            {"clave": "A"},
            {"clave": "B"},
        ],
        "registros_invalidos": [{"numero_fila": 5}],
    }
    resolucion = {
        "claves_no_encontradas": [
            {"clave": "B"},
        ]
    }
    analisis_claves = [
        {
            "referencia": {
                "precio_referencia": Decimal("100")
            },
            "cotizaciones": [
                {
                    "clasificacion_desviacion": "COMPETITIVO",
                    "evaluacion_atipico": {
                        "es_valor_atipico": False
                    },
                },
                {
                    "clasificacion_desviacion": "ELEVADO",
                    "evaluacion_atipico": {
                        "es_valor_atipico": True
                    },
                },
            ],
            "resumen": {
                "riesgo_clave": "ALTO",
            },
        }
    ]

    resultado = ComparadorIMService.construir_resumen_general(
        preparacion,
        resolucion,
        analisis_claves,
    )

    assert resultado["total_filas_recibidas"] == 4
    assert resultado["total_filas_validas"] == 3
    assert resultado["total_filas_invalidas"] == 1
    assert resultado["total_claves_im"] == 2
    assert resultado["claves_encontradas"] == 1
    assert resultado["claves_no_encontradas"] == 1
    assert resultado["claves_con_referencia"] == 1
    assert resultado["cotizaciones_competitivas"] == 1
    assert resultado["cotizaciones_elevadas"] == 1
    assert resultado["cotizaciones_atipicas"] == 1
    assert resultado["claves_riesgo_alto"] == 1


def test_construir_tablas_salida():
    analisis_claves = [
        {
            "id_clave": 1,
            "clave": "A",
            "descripcion": "DESC",
            "categoria": "CAT",
            "referencia": {
                "precio_referencia": Decimal("100"),
                "fuente_referencia": "ADJUDICACIONES",
            },
            "nivel_confianza": "ALTA",
            "tendencia": {
                "tendencia": "ESTABLE",
            },
            "resumen": {
                "total_cotizaciones_im": 1,
            },
            "estadisticas_fuentes": {
                "adjudicaciones": {
                    "total_observaciones": 4,
                }
            },
            "cotizaciones": [
                {
                    "numero_fila": 2,
                    "rfc": "ABC",
                    "razon_social": "PROVEEDOR",
                    "recomendaciones": [
                        {
                            "codigo": "PRECIO_EN_MERCADO",
                            "nivel": "FAVORABLE",
                            "titulo": "OK",
                            "mensaje": "OK",
                        }
                    ],
                }
            ],
        }
    ]

    resultado = ComparadorIMService.construir_tablas_salida(
        analisis_claves
    )

    assert len(resultado["resumen_claves"]) == 1
    assert len(resultado["estadisticas_mercado"]) == 1
    assert len(resultado["comparacion_cotizaciones"]) == 1
    assert len(resultado["recomendaciones"]) == 1


def test_construir_datos_graficas():
    analisis_claves = [
        {
            "id_clave": 1,
            "clave": "A",
            "tendencia": {
                "serie": [
                    {
                        "ejercicio": 2025,
                        "precio_mediana": Decimal("100"),
                    }
                ]
            },
            "fuentes_mercado": {
                "adjudicaciones": [
                    Decimal("100"),
                    Decimal("110"),
                ]
            },
            "cotizaciones": [
                {
                    "rfc": "ABC",
                    "razon_social": "PROVEEDOR",
                    "precio_im": Decimal("105"),
                    "clasificacion_desviacion": "EN MERCADO",
                }
            ],
            "resumen": {
                "riesgo_clave": "BAJO",
            },
        }
    ]

    resultado = (
        ComparadorIMService.construir_datos_graficas(
            analisis_claves
        )
    )

    assert len(resultado["evolucion_precios"]) == 1
    assert len(resultado["distribucion_precios"]) == 2
    assert len(resultado["clasificacion_cotizaciones"]) == 1
    assert len(resultado["riesgo_por_clave"]) == 1


def test_comparar_investigacion_completa():
    repository = RepositoryFalso()
    service = ComparadorIMService(repository=repository)

    registros = DataFrameFalso(
        [
            {
                "RFC": "abc010101aa1",
                "RAZON SOCIAL": "Proveedor Uno SA de CV",
                "CLAVE": "010.000.001",
                "DESCRIPCION": "Producto uno",
                "CANTIDAD": 1000,
                "PAIS DE ORIGEN": "México",
                "PRECIO UNITARIO": 120,
            },
            {
                "RFC": "def010101bb2",
                "RAZON SOCIAL": "Proveedor Dos SA de CV",
                "CLAVE": "010.000.002",
                "DESCRIPCION": "Producto dos",
                "CANTIDAD": 500,
                "PAIS DE ORIGEN": "México",
                "PRECIO UNITARIO": 50,
            },
            {
                "RFC": "ghi010101cc3",
                "RAZON SOCIAL": "Proveedor Tres SA de CV",
                "CLAVE": "999.999.999",
                "DESCRIPCION": "No existe",
                "CANTIDAD": 100,
                "PAIS DE ORIGEN": "México",
                "PRECIO UNITARIO": 10,
            },
            {
                "RFC": "",
                "RAZON SOCIAL": "",
                "CLAVE": "",
                "CANTIDAD": 0,
                "PRECIO UNITARIO": 0,
            },
        ]
    )

    resultado = service.comparar_investigacion(
        registros,
        conn=CONEXION_PRUEBA,
    )

    resumen = resultado["resumen"]

    assert resumen["total_filas_recibidas"] == 4
    assert resumen["total_filas_validas"] == 3
    assert resumen["total_filas_invalidas"] == 1
    assert resumen["total_claves_im"] == 3
    assert resumen["claves_encontradas"] == 2
    assert resumen["claves_no_encontradas"] == 1
    assert resumen["total_cotizaciones_analizadas"] == 2
    assert resumen["claves_con_referencia"] == 2

    assert len(resultado["incidencias"]["filas_invalidas"]) == 1
    assert len(resultado["incidencias"]["claves_no_encontradas"]) == 1
    assert len(resultado["claves"]) == 2

    clave_uno = next(
        item
        for item in resultado["claves"]
        if item["id_clave"] == 1
    )
    clave_dos = next(
        item
        for item in resultado["claves"]
        if item["id_clave"] == 2
    )

    assert (
        clave_uno["referencia"]["fuente_referencia"]
        == "ADJUDICACIONES"
    )
    assert (
        clave_uno["referencia"]["precio_referencia"]
        == Decimal("105.00")
    )

    assert (
        clave_dos["referencia"]["fuente_referencia"]
        == "PROPUESTAS_INICIALES"
    )
    assert (
        clave_dos["referencia"]["precio_referencia"]
        == Decimal("55.00")
    )

    assert len(resultado["tablas"]["resumen_claves"]) == 2
    assert (
        len(
            resultado["tablas"][
                "comparacion_cotizaciones"
            ]
        )
        == 2
    )
    assert len(resultado["graficas"]["riesgo_por_clave"]) == 2

    assert repository.llamadas == [
        (
            "obtener_claves_por_codigos",
            [
                "010.000.001",
                "010.000.002",
                "999.999.999",
            ],
            CONEXION_PRUEBA,
        ),
        (
            "obtener_contexto_comparacion",
            [1, 2],
            CONEXION_PRUEBA,
        ),
    ]


def test_comparar_investigacion_sin_registros_validos():
    repository = RepositoryFalso()
    service = ComparadorIMService(repository=repository)

    resultado = service.comparar_investigacion(
        [
            {
                "RFC": "",
                "RAZON SOCIAL": "",
                "CLAVE": "",
                "CANTIDAD": 0,
                "PRECIO": 0,
            }
        ],
        conn=CONEXION_PRUEBA,
    )

    assert resultado["resumen"]["total_filas_recibidas"] == 1
    assert resultado["resumen"]["total_filas_validas"] == 0
    assert resultado["resumen"]["total_filas_invalidas"] == 1
    assert resultado["resumen"]["claves_encontradas"] == 0
    assert resultado["claves"] == []

    assert repository.llamadas == []