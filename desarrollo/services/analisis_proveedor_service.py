"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_proveedor_service.py

Servicio analítico para el módulo Análisis por Proveedor.

Responsabilidades:
- Coordinar las consultas de AnalisisProveedorRepository.
- Normalizar valores numéricos para análisis.
- Construir indicadores comerciales y técnicos.
- Analizar precios exclusivamente por procedimiento y clave.
- Calcular variaciones entre oferta inicial, subasta y adjudicación.
- Calcular ahorro estimado de subasta con una cantidad de referencia.
- Procesar competencia operativa por procedimiento-clave.
- Integrar adjudicaciones operativas e históricas.
- Preparar una respuesta única para la interfaz Streamlit.

Este Service:
- No ejecuta SQL.
- No abre ni cierra conexiones.
- No administra transacciones.
- No contiene componentes de Streamlit.
- No modifica información en la base de datos.
- No mezcla precios de claves diferentes en promedios globales.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from collections import defaultdict
from decimal import Decimal

from repositories.analisis_proveedor_repository import (
    AnalisisProveedorRepository,
)
from services.analisis_economico_service import AnalisisEconomicoService


class AnalisisProveedorService(AnalisisEconomicoService):
    """Servicio de inteligencia comercial por proveedor."""

    RESULTADO_POSITIVA = AnalisisProveedorRepository.RESULTADO_POSITIVA
    RESULTADO_NEGATIVA = AnalisisProveedorRepository.RESULTADO_NEGATIVA

    ORIGEN_OPERATIVO = "OPERATIVO"
    ORIGEN_HISTORICO = "HISTORICO"

    ESTADO_ADJUDICADO = "ADJUDICADO"
    ESTADO_SUBASTA = "SUBASTA"
    ESTADO_APROBADO = "APROBADO TÉCNICAMENTE"
    ESTADO_DESCARTADO = "DESCARTADO TÉCNICAMENTE"
    ESTADO_OFERTA_INICIAL = "OFERTA INICIAL"
    ESTADO_SIN_INFORMACION = "SIN INFORMACIÓN"

    def __init__(self, repository=None):
        self.repository = repository or AnalisisProveedorRepository()

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @classmethod
    def _cero_precio(cls):
        return cls.CERO.quantize(cls.CUANTIZADOR_PRECIO)

    @classmethod
    def _cero_porcentaje(cls):
        return cls.CERO.quantize(cls.CUANTIZADOR_PORCENTAJE)

    @classmethod
    def _cero_cantidad(cls):
        return cls.CERO.quantize(cls.CUANTIZADOR_CANTIDAD)

    @classmethod
    def _sumar_decimal(cls, registros, campo):
        """Suma valores válidos de un campo sin convertir ausencias en error."""
        return sum(
            (
                cls._decimal(registro.get(campo), cls.CERO)
                for registro in registros or []
            ),
            cls.CERO,
        )

    @staticmethod
    def _orden_ejercicio(valor):
        """Permite ordenar ejercicios identificados antes de los desconocidos."""
        if valor is None:
            return -1
        try:
            return int(valor)
        except (TypeError, ValueError):
            return -1

    @classmethod
    def _seleccionar_cantidad_referencia(cls, item):
        """
        Selecciona la cantidad para estimar ahorro de subasta.

        Prioridad aprobada:
        1. Cantidad adjudicada.
        2. Cantidad ofertada en subasta.
        3. Cantidad ofertada inicialmente.
        """
        candidatos = (
            ("ADJUDICADA", item.get("cantidad_adjudicada")),
            ("SUBASTA", item.get("cantidad_subasta")),
            ("INICIAL", item.get("cantidad_inicial")),
        )

        for origen, valor in candidatos:
            cantidad = cls._decimal(valor)
            if cantidad is not None and cantidad > cls.CERO:
                return origen, cantidad

        return None, None

    @classmethod
    def _clasificar_estado_participacion(cls, item):
        """Clasifica la etapa máxima alcanzada por procedimiento-clave."""
        if item.get("adjudicado"):
            return cls.ESTADO_ADJUDICADO
        if item.get("tiene_subasta"):
            return cls.ESTADO_SUBASTA
        if item.get("aprobado_tecnicamente"):
            return cls.ESTADO_APROBADO
        if item.get("descartado_tecnicamente"):
            return cls.ESTADO_DESCARTADO
        if item.get("tiene_oferta_inicial"):
            return cls.ESTADO_OFERTA_INICIAL
        return cls.ESTADO_SIN_INFORMACION

    # ==========================================================
    # PARTICIPACIÓN OPERATIVA
    # ==========================================================

    @classmethod
    def procesar_participacion_operativa(cls, registros):
        """
        Normaliza y enriquece una fila por procedimiento y clave.

        Las comparaciones económicas se realizan únicamente dentro de la
        misma fila, por lo que nunca se mezclan precios de claves distintas.
        """
        resultado = []

        for registro in registros or []:
            item = dict(registro)

            for campo in (
                "cantidad_requerida",
                "cantidad_inicial",
                "cantidad_subasta",
                "cantidad_adjudicada",
            ):
                item[campo] = cls.redondear_cantidad(item.get(campo))

            for campo in (
                "precio_inicial",
                "precio_subasta",
                "precio_adjudicado",
                "valor_adjudicado",
            ):
                item[campo] = cls.redondear_precio(item.get(campo))

            item["porcentaje_adjudicado"] = cls.redondear_porcentaje(
                item.get("porcentaje_adjudicado")
            )

            item["tiene_oferta_inicial"] = (
                item.get("id_propuesta_inicial") is not None
            )
            item["evaluado"] = item.get("id_evaluacion") is not None
            item["aprobado_tecnicamente"] = (
                item.get("resultado_tecnico") == cls.RESULTADO_POSITIVA
            )
            item["descartado_tecnicamente"] = (
                item.get("resultado_tecnico") == cls.RESULTADO_NEGATIVA
            )
            item["tiene_subasta"] = (
                item.get("id_propuesta_subasta") is not None
            )
            item["adjudicado"] = item.get("id_adjudicacion") is not None

            item["variacion_inicial_subasta"] = cls.calcular_variacion(
                item.get("precio_inicial"),
                item.get("precio_subasta"),
            )
            item["variacion_subasta_adjudicacion"] = cls.calcular_variacion(
                item.get("precio_subasta"),
                item.get("precio_adjudicado"),
            )
            item["variacion_inicial_adjudicacion"] = cls.calcular_variacion(
                item.get("precio_inicial"),
                item.get("precio_adjudicado"),
            )

            item["clasificacion_inicial_subasta"] = (
                cls.clasificar_variacion(
                    item["variacion_inicial_subasta"]
                )
            )
            item["clasificacion_subasta_adjudicacion"] = (
                cls.clasificar_variacion(
                    item["variacion_subasta_adjudicacion"]
                )
            )
            item["clasificacion_inicial_adjudicacion"] = (
                cls.clasificar_variacion(
                    item["variacion_inicial_adjudicacion"]
                )
            )

            origen_cantidad, cantidad_referencia = (
                cls._seleccionar_cantidad_referencia(item)
            )
            item["origen_cantidad_ahorro"] = origen_cantidad
            item["cantidad_referencia_ahorro"] = cantidad_referencia
            item["ahorro_unitario_subasta"] = cls.calcular_ahorro_unitario(
                item.get("precio_inicial"),
                item.get("precio_subasta"),
            )
            item["ahorro_estimado_subasta"] = cls.calcular_ahorro_estimado(
                item.get("precio_inicial"),
                item.get("precio_subasta"),
                cantidad_referencia,
            )
            item["estado_participacion"] = (
                cls._clasificar_estado_participacion(item)
            )

            resultado.append(item)

        return resultado

    # ==========================================================
    # INDICADORES
    # ==========================================================

    @classmethod
    def completar_indicadores(cls, indicadores_base, participaciones):
        """Completa los indicadores del Repository con métricas derivadas."""
        resultado = dict(indicadores_base or {})

        campos_enteros = (
            "total_procedimientos_participados",
            "total_claves_ofertadas",
            "total_participaciones_procedimiento_clave",
            "total_propuestas_iniciales",
            "total_propuestas_subasta",
            "total_evaluaciones_positivas",
            "total_evaluaciones_negativas",
            "total_claves_adjudicadas_operativas",
            "total_procedimientos_adjudicados",
            "total_adjudicaciones_operativas",
            "total_adjudicaciones_historicas",
            "total_claves_adjudicadas_historicas",
        )
        for campo in campos_enteros:
            resultado[campo] = cls._entero(resultado.get(campo))

        for campo in (
            "cantidad_adjudicada_operativa",
            "cantidad_adjudicada_historica",
        ):
            resultado[campo] = (
                cls.redondear_cantidad(resultado.get(campo))
                or cls._cero_cantidad()
            )

        for campo in (
            "valor_adjudicado_operativo",
            "valor_adjudicado_historico",
        ):
            resultado[campo] = (
                cls.redondear_precio(resultado.get(campo))
                or cls._cero_precio()
            )

        total_evaluaciones = (
            resultado["total_evaluaciones_positivas"]
            + resultado["total_evaluaciones_negativas"]
        )
        resultado["total_evaluaciones"] = total_evaluaciones
        resultado["porcentaje_aprobacion_tecnica"] = (
            cls.calcular_porcentaje(
                resultado["total_evaluaciones_positivas"],
                total_evaluaciones,
            )
            or cls._cero_porcentaje()
        )
        resultado["porcentaje_procedimientos_adjudicados"] = (
            cls.calcular_porcentaje(
                resultado["total_procedimientos_adjudicados"],
                resultado["total_procedimientos_participados"],
            )
            or cls._cero_porcentaje()
        )

        resultado["total_adjudicaciones"] = (
            resultado["total_adjudicaciones_operativas"]
            + resultado["total_adjudicaciones_historicas"]
        )
        resultado["valor_adjudicado_total"] = (
            resultado["valor_adjudicado_operativo"]
            + resultado["valor_adjudicado_historico"]
        ).quantize(cls.CUANTIZADOR_PRECIO)

        resultado["claves_descartadas_tecnicamente"] = len(
            {
                item.get("id_clave")
                for item in participaciones or []
                if item.get("descartado_tecnicamente")
            }
        )

        return resultado

    # ==========================================================
    # DESEMPEÑO ECONÓMICO
    # ==========================================================

    @classmethod
    def construir_resumen_economico(cls, participaciones):
        """Construye KPIs económicos sin promediar claves diferentes."""
        comparables = [
            item
            for item in participaciones or []
            if item.get("variacion_inicial_subasta") is not None
        ]

        reducciones = [
            item
            for item in comparables
            if item.get("clasificacion_inicial_subasta")
            == cls.CLASIFICACION_AHORRO
        ]
        sin_cambio = [
            item
            for item in comparables
            if item.get("clasificacion_inicial_subasta")
            == cls.CLASIFICACION_SIN_CAMBIO
        ]
        incrementos = [
            item
            for item in comparables
            if item.get("clasificacion_inicial_subasta")
            == cls.CLASIFICACION_INCREMENTO
        ]

        ahorros_positivos = [
            cls._decimal(item.get("ahorro_estimado_subasta"))
            for item in reducciones
            if cls._decimal(item.get("ahorro_estimado_subasta")) is not None
        ]
        incrementos_estimados = [
            abs(cls._decimal(item.get("ahorro_estimado_subasta")))
            for item in incrementos
            if cls._decimal(item.get("ahorro_estimado_subasta")) is not None
        ]

        mayor_reduccion = min(
            reducciones,
            key=lambda item: item.get("variacion_inicial_subasta"),
            default=None,
        )
        mayor_incremento = max(
            incrementos,
            key=lambda item: item.get("variacion_inicial_subasta"),
            default=None,
        )

        return {
            "combinaciones_comparables": len(comparables),
            "claves_con_reduccion": len(reducciones),
            "claves_sin_cambio": len(sin_cambio),
            "claves_con_incremento": len(incrementos),
            "ahorro_estimado_total": sum(
                ahorros_positivos,
                cls.CERO,
            ).quantize(cls.CUANTIZADOR_PRECIO),
            "incremento_estimado_total": sum(
                incrementos_estimados,
                cls.CERO,
            ).quantize(cls.CUANTIZADOR_PRECIO),
            "mayor_reduccion": dict(mayor_reduccion) if mayor_reduccion else None,
            "mayor_incremento": (
                dict(mayor_incremento) if mayor_incremento else None
            ),
        }

    # ==========================================================
    # DESEMPEÑO TÉCNICO
    # ==========================================================

    @classmethod
    def construir_desempeno_tecnico(cls, participaciones):
        """Resume evaluaciones técnicas y claves descartadas."""
        positivas = [
            item
            for item in participaciones or []
            if item.get("aprobado_tecnicamente")
        ]
        negativas = [
            item
            for item in participaciones or []
            if item.get("descartado_tecnicamente")
        ]
        total = len(positivas) + len(negativas)

        return {
            "evaluaciones_positivas": len(positivas),
            "evaluaciones_negativas": len(negativas),
            "total_evaluaciones": total,
            "porcentaje_aprobacion": (
                cls.calcular_porcentaje(len(positivas), total)
                or cls._cero_porcentaje()
            ),
            "claves_descartadas": len(
                {
                    item.get("id_clave")
                    for item in negativas
                }
            ),
            "detalle_descartadas": negativas,
        }

    # ==========================================================
    # PARTICIPACIÓN POR EJERCICIO
    # ==========================================================

    @classmethod
    def construir_participacion_por_ejercicio(
        cls,
        participaciones,
        historial,
    ):
        """Agrupa participación operativa e histórica por ejercicio."""
        grupos = defaultdict(
            lambda: {
                "procedimientos": set(),
                "claves_ofertadas": set(),
                "evaluaciones_positivas": 0,
                "evaluaciones_negativas": 0,
                "claves_adjudicadas_operativas": set(),
                "adjudicaciones_historicas": 0,
                "valor_adjudicado_operativo": cls.CERO,
                "valor_adjudicado_historico": cls.CERO,
            }
        )

        for item in participaciones or []:
            ejercicio = item.get("ejercicio")
            grupo = grupos[ejercicio]
            grupo["procedimientos"].add(item.get("id_procedimiento"))

            if item.get("tiene_oferta_inicial"):
                grupo["claves_ofertadas"].add(item.get("id_clave"))
            if item.get("aprobado_tecnicamente"):
                grupo["evaluaciones_positivas"] += 1
            if item.get("descartado_tecnicamente"):
                grupo["evaluaciones_negativas"] += 1
            if item.get("adjudicado"):
                grupo["claves_adjudicadas_operativas"].add(
                    item.get("id_clave")
                )
                grupo["valor_adjudicado_operativo"] += cls._decimal(
                    item.get("valor_adjudicado"),
                    cls.CERO,
                )

        for item in historial or []:
            if item.get("origen_dato") != cls.ORIGEN_HISTORICO:
                continue
            ejercicio = item.get("ejercicio")
            grupo = grupos[ejercicio]
            grupo["adjudicaciones_historicas"] += 1
            grupo["valor_adjudicado_historico"] += cls._decimal(
                item.get("valor_adjudicado"),
                cls.CERO,
            )

        resultado = []
        for ejercicio, grupo in grupos.items():
            valor_operativo = grupo["valor_adjudicado_operativo"].quantize(
                cls.CUANTIZADOR_PRECIO
            )
            valor_historico = grupo["valor_adjudicado_historico"].quantize(
                cls.CUANTIZADOR_PRECIO
            )
            resultado.append(
                {
                    "ejercicio": ejercicio,
                    "etiqueta_ejercicio": (
                        str(ejercicio)
                        if ejercicio is not None
                        else "Ejercicio no identificado"
                    ),
                    "procedimientos_participados": len(
                        {
                            valor
                            for valor in grupo["procedimientos"]
                            if valor is not None
                        }
                    ),
                    "claves_ofertadas": len(grupo["claves_ofertadas"]),
                    "evaluaciones_positivas": grupo["evaluaciones_positivas"],
                    "evaluaciones_negativas": grupo["evaluaciones_negativas"],
                    "claves_adjudicadas_operativas": len(
                        grupo["claves_adjudicadas_operativas"]
                    ),
                    "adjudicaciones_historicas": (
                        grupo["adjudicaciones_historicas"]
                    ),
                    "valor_adjudicado_operativo": valor_operativo,
                    "valor_adjudicado_historico": valor_historico,
                    "valor_adjudicado_total": (
                        valor_operativo + valor_historico
                    ).quantize(cls.CUANTIZADOR_PRECIO),
                }
            )

        return sorted(
            resultado,
            key=lambda item: cls._orden_ejercicio(item.get("ejercicio")),
        )

    # ==========================================================
    # HISTORIAL
    # ==========================================================

    @classmethod
    def procesar_historial_adjudicaciones(cls, registros):
        """Normaliza adjudicaciones operativas e históricas."""
        resultado = []

        for indice, registro in enumerate(registros or []):
            item = dict(registro)
            item["origen_dato"] = (
                item.get("origen_dato") or cls.ORIGEN_OPERATIVO
            )
            item["es_historico"] = (
                item["origen_dato"] == cls.ORIGEN_HISTORICO
            )
            item["cantidad_adjudicada"] = cls.redondear_cantidad(
                item.get("cantidad_adjudicada")
            )
            item["porcentaje_adjudicado"] = cls.redondear_porcentaje(
                item.get("porcentaje_adjudicado")
            )
            item["precio_adjudicado"] = cls.redondear_precio(
                item.get("precio_adjudicado")
            )
            item["valor_adjudicado"] = (
                cls.redondear_precio(item.get("valor_adjudicado"))
                or cls._cero_precio()
            )
            item["orden_fuente"] = indice
            resultado.append(item)

        return resultado

    @classmethod
    def construir_evolucion_por_clave(cls, participaciones, historial):
        """
        Construye series cronológicas por proveedor-clave.

        Cada punto conserva sus propias etapas. No se promedian precios entre
        procedimientos ni entre claves.
        """
        grupos = defaultdict(
            lambda: {
                "id_clave": None,
                "clave": None,
                "descripcion_clave": None,
                "puntos": [],
            }
        )

        for item in participaciones or []:
            id_clave = item.get("id_clave")
            grupo = grupos[id_clave]
            grupo["id_clave"] = id_clave
            grupo["clave"] = item.get("clave")
            grupo["descripcion_clave"] = item.get("descripcion_clave")
            grupo["puntos"].append(
                {
                    "origen_dato": cls.ORIGEN_OPERATIVO,
                    "id_procedimiento": item.get("id_procedimiento"),
                    "numero_procedimiento": item.get("numero_procedimiento"),
                    "ejercicio": item.get("ejercicio"),
                    "precio_inicial": item.get("precio_inicial"),
                    "precio_subasta": item.get("precio_subasta"),
                    "precio_adjudicado": item.get("precio_adjudicado"),
                    "resultado_tecnico": item.get("resultado_tecnico"),
                    "orden_fuente": 0,
                }
            )

        for item in historial or []:
            if item.get("origen_dato") != cls.ORIGEN_HISTORICO:
                continue
            id_clave = item.get("id_clave")
            grupo = grupos[id_clave]
            grupo["id_clave"] = id_clave
            grupo["clave"] = item.get("clave")
            grupo["descripcion_clave"] = item.get("descripcion_clave")
            grupo["puntos"].append(
                {
                    "origen_dato": cls.ORIGEN_HISTORICO,
                    "id_procedimiento": None,
                    "numero_procedimiento": item.get("numero_procedimiento"),
                    "ejercicio": item.get("ejercicio"),
                    "precio_inicial": None,
                    "precio_subasta": None,
                    "precio_adjudicado": item.get("precio_adjudicado"),
                    "resultado_tecnico": None,
                    "orden_fuente": item.get("orden_fuente", 0),
                }
            )

        resultado = []
        for grupo in grupos.values():
            grupo["puntos"] = sorted(
                grupo["puntos"],
                key=lambda punto: (
                    cls._orden_ejercicio(punto.get("ejercicio")),
                    punto.get("numero_procedimiento") or "",
                    punto.get("orden_fuente", 0),
                ),
            )
            grupo["total_puntos"] = len(grupo["puntos"])
            grupo["total_operativos"] = sum(
                1
                for punto in grupo["puntos"]
                if punto.get("origen_dato") == cls.ORIGEN_OPERATIVO
            )
            grupo["total_historicos"] = sum(
                1
                for punto in grupo["puntos"]
                if punto.get("origen_dato") == cls.ORIGEN_HISTORICO
            )
            resultado.append(grupo)

        return sorted(
            resultado,
            key=lambda item: (
                item.get("clave") or "",
                item.get("id_clave") or 0,
            ),
        )

    # ==========================================================
    # COMPETENCIA
    # ==========================================================

    @classmethod
    def procesar_competidores(cls, registros):
        """Normaliza los enfrentamientos contra cada competidor."""
        resultado = []

        for registro in registros or []:
            item = dict(registro)
            for campo in (
                "coincidencias",
                "procedimientos_compartidos",
                "claves_compartidas",
                "victorias_proveedor",
                "victorias_competidor",
                "adjudicaciones_compartidas",
                "sin_adjudicacion",
            ):
                item[campo] = cls._entero(item.get(campo))

            item["derrotas_proveedor"] = item["victorias_competidor"]
            item["porcentaje_victorias"] = (
                cls.calcular_porcentaje(
                    item["victorias_proveedor"],
                    item["coincidencias"],
                )
                or cls._cero_porcentaje()
            )
            item["porcentaje_derrotas"] = (
                cls.calcular_porcentaje(
                    item["victorias_competidor"],
                    item["coincidencias"],
                )
                or cls._cero_porcentaje()
            )
            resultado.append(item)

        return resultado

    # ==========================================================
    # RESPUESTAS PARA STREAMLIT
    # ==========================================================

    def obtener_catalogos_filtros(self, id_proveedor=None, conn=None):
        """Obtiene catálogos dependientes para la interfaz."""
        respuesta = {
            "proveedores": (
                self.repository.obtener_proveedores_filtro(conn=conn) or []
            ),
            "procedimientos": [],
            "ejercicios": [],
            "claves": [],
        }

        if id_proveedor is not None:
            respuesta["procedimientos"] = (
                self.repository.obtener_procedimientos_filtro(
                    id_proveedor=id_proveedor,
                    conn=conn,
                )
                or []
            )
            respuesta["ejercicios"] = (
                self.repository.obtener_ejercicios_filtro(
                    id_proveedor=id_proveedor,
                    conn=conn,
                )
                or []
            )
            respuesta["claves"] = (
                self.repository.obtener_claves_filtro(
                    id_proveedor=id_proveedor,
                    conn=conn,
                )
                or []
            )

        return respuesta

    def obtener_analisis_proveedor(
        self,
        id_proveedor,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """Construye la respuesta completa que consumirá Streamlit."""
        if id_proveedor is None:
            raise ValueError(
                "id_proveedor es obligatorio para obtener el análisis."
            )

        informacion = (
            self.repository.obtener_informacion_proveedor(
                id_proveedor=id_proveedor,
                conn=conn,
            )
            or {}
        )
        if not informacion:
            raise ValueError("El proveedor seleccionado no existe.")

        argumentos = {
            "id_proveedor": id_proveedor,
            "id_procedimiento": id_procedimiento,
            "ejercicio": ejercicio,
            "id_clave": id_clave,
            "conn": conn,
        }

        indicadores_base = (
            self.repository.obtener_indicadores_proveedor(**argumentos) or {}
        )
        participacion_base = (
            self.repository.obtener_participacion_operativa(**argumentos) or []
        )
        historial_base = (
            self.repository.obtener_historial_adjudicaciones(**argumentos) or []
        )
        competidores_base = (
            self.repository.obtener_competidores(**argumentos) or []
        )

        participaciones = self.procesar_participacion_operativa(
            participacion_base
        )
        historial = self.procesar_historial_adjudicaciones(historial_base)
        competidores = self.procesar_competidores(competidores_base)
        indicadores = self.completar_indicadores(
            indicadores_base,
            participaciones,
        )
        resumen_economico = self.construir_resumen_economico(
            participaciones
        )
        desempeno_tecnico = self.construir_desempeno_tecnico(
            participaciones
        )
        participacion_ejercicio = self.construir_participacion_por_ejercicio(
            participaciones,
            historial,
        )
        evolucion_por_clave = self.construir_evolucion_por_clave(
            participaciones,
            historial,
        )

        return {
            "filtros": {
                "id_proveedor": id_proveedor,
                "id_procedimiento": id_procedimiento,
                "ejercicio": ejercicio,
                "id_clave": id_clave,
            },
            "proveedor": dict(informacion),
            "indicadores": indicadores,
            "resumen_economico": resumen_economico,
            "desempeno_tecnico": desempeno_tecnico,
            "tablas": {
                "participacion_operativa": participaciones,
                "economia_por_clave": participaciones,
                "claves_descartadas": desempeno_tecnico[
                    "detalle_descartadas"
                ],
                "competidores": competidores,
                "historial_adjudicaciones": historial,
                "participacion_por_ejercicio": participacion_ejercicio,
                "evolucion_por_clave": evolucion_por_clave,
            },
            "graficas": {
                "participacion_por_ejercicio": participacion_ejercicio,
                "embudo_tecnico": [
                    {
                        "etapa": "OFERTADAS",
                        "total": indicadores[
                            "total_participaciones_procedimiento_clave"
                        ],
                    },
                    {
                        "etapa": "APROBADAS",
                        "total": desempeno_tecnico[
                            "evaluaciones_positivas"
                        ],
                    },
                    {
                        "etapa": "SUBASTADAS",
                        "total": indicadores["total_propuestas_subasta"],
                    },
                    {
                        "etapa": "ADJUDICADAS",
                        "total": indicadores[
                            "total_adjudicaciones_operativas"
                        ],
                    },
                ],
                "ahorro_subasta": [
                    item
                    for item in participaciones
                    if item.get("variacion_inicial_subasta") is not None
                ],
                "competidores": competidores,
                "evolucion_por_clave": evolucion_por_clave,
            },
            "limitaciones": {
                "tipo_procedimiento_disponible": False,
                "mensaje_tipo_procedimiento": (
                    "La clasificación por tipo de procedimiento no está "
                    "disponible en el modelo de datos actual."
                ),
                "competencia_incluye_historicos": False,
                "precios_promedio_globales": False,
            },
        }