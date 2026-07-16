"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_clave_service.py

Servicio analítico para el módulo Análisis por Clave.

Responsabilidades:
- Coordinar las consultas de AnalisisClaveRepository.
- Normalizar valores numéricos para análisis.
- Calcular estados analíticos por procedimiento.
- Calcular el estado analítico consolidado.
- Calcular precios adjudicados ponderados.
- Calcular variaciones entre etapas.
- Clasificar ahorro, incremento, sin cambio o información insuficiente.
- Construir indicadores consolidados.
- Preparar una respuesta única para la interfaz Streamlit.

Este Service:
- No ejecuta SQL.
- No abre ni cierra conexiones.
- No administra transacciones.
- No contiene componentes de Streamlit.
- No modifica información en la base de datos.
- No reutiliza directamente DashboardService, pero conserva
  los mismos criterios numéricos aprobados.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from repositories.analisis_clave_repository import AnalisisClaveRepository


class AnalisisClaveService:
    """Servicio de reglas analíticas para el módulo Análisis por Clave."""

    # ==========================================================
    # ESTADOS ANALÍTICOS
    # ==========================================================

    ESTADO_SIN_PROPUESTAS = "SIN PROPUESTAS"
    ESTADO_SOLO_OFERTA_INICIAL = "SOLO OFERTA INICIAL"
    ESTADO_SIN_APROBACION = "SIN APROBACIÓN TÉCNICA"
    ESTADO_CON_OFERTA_VIABLE = "CON OFERTA VIABLE"
    ESTADO_CON_SUBASTA = "CON SUBASTA"
    ESTADO_ADJUDICADO = "ADJUDICADO"
    ESTADO_SIN_INFORMACION = "SIN INFORMACIÓN"

    # ==========================================================
    # CLASIFICACIONES ECONÓMICAS
    # ==========================================================

    CLASIFICACION_AHORRO = "AHORRO"
    CLASIFICACION_SIN_CAMBIO = "SIN CAMBIO"
    CLASIFICACION_INCREMENTO = "INCREMENTO"
    CLASIFICACION_INSUFICIENTE = "INFORMACIÓN INSUFICIENTE"

    # ==========================================================
    # CONFIGURACIÓN NUMÉRICA
    # ==========================================================

    CUANTIZADOR_PRECIO = Decimal("0.01")
    CUANTIZADOR_PORCENTAJE = Decimal("0.01")
    CERO = Decimal("0")

    def __init__(self, repository=None):
        self.repository = repository or AnalisisClaveRepository()

    # ==========================================================
    # UTILIDADES NUMÉRICAS
    # ==========================================================

    @classmethod
    def _decimal(cls, valor, default=None):
        """
        Convierte un valor a Decimal de forma controlada.

        - None permanece como None cuando no se proporciona default.
        - Los valores inválidos devuelven default.
        - No convierte ausencias en cero salvo que el llamador
          lo solicite expresamente.
        """
        if valor is None:
            return default

        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                return default

        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return default

        if not numero.is_finite():
            return default

        return numero

    @classmethod
    def _entero(cls, valor, default=0):
        """Convierte un valor a entero sin propagar errores."""
        numero = cls._decimal(valor)
        if numero is None:
            return default

        try:
            return int(numero)
        except (ValueError, TypeError, OverflowError):
            return default

    @classmethod
    def redondear_precio(cls, valor):
        """Redondea un precio a dos decimales con ROUND_HALF_UP."""
        numero = cls._decimal(valor)
        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def redondear_porcentaje(cls, valor):
        """Redondea un porcentaje a dos decimales con ROUND_HALF_UP."""
        numero = cls._decimal(valor)
        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_PORCENTAJE,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_porcentaje(cls, numerador, denominador):
        """
        Calcula numerador / denominador * 100.

        Devuelve None cuando el denominador es inexistente o no positivo.
        """
        numero = cls._decimal(numerador)
        total = cls._decimal(denominador)

        if numero is None or total is None or total <= cls.CERO:
            return None

        return (
            (numero / total) * Decimal("100")
        ).quantize(
            cls.CUANTIZADOR_PORCENTAJE,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_variacion(cls, precio_origen, precio_destino):
        """
        Calcula la variación porcentual entre dos precios.

        Fórmula:
            ((destino - origen) / origen) * 100

        Devuelve None cuando falta algún precio o el precio de origen
        es menor o igual a cero.
        """
        origen = cls._decimal(precio_origen)
        destino = cls._decimal(precio_destino)

        if (
            origen is None
            or destino is None
            or origen <= cls.CERO
        ):
            return None

        return (
            ((destino - origen) / origen) * Decimal("100")
        ).quantize(
            cls.CUANTIZADOR_PORCENTAJE,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def clasificar_variacion(cls, variacion):
        """Clasifica una variación económica."""
        valor = cls._decimal(variacion)

        if valor is None:
            return cls.CLASIFICACION_INSUFICIENTE

        if valor < cls.CERO:
            return cls.CLASIFICACION_AHORRO

        if valor > cls.CERO:
            return cls.CLASIFICACION_INCREMENTO

        return cls.CLASIFICACION_SIN_CAMBIO

    @classmethod
    def calcular_precio_adjudicado_ponderado(
        cls,
        cantidad_total_adjudicada,
        valor_total_adjudicado,
    ):
        """
        Calcula el precio adjudicado ponderado.

        precio ponderado =
            valor total adjudicado / cantidad total adjudicada
        """
        cantidad = cls._decimal(cantidad_total_adjudicada)
        valor = cls._decimal(valor_total_adjudicado)

        if (
            cantidad is None
            or valor is None
            or cantidad <= cls.CERO
        ):
            return None

        return (valor / cantidad).quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    # ==========================================================
    # ESTADO ANALÍTICO
    # ==========================================================

    @classmethod
    def clasificar_estado_procedimiento(cls, registro):
        """
        Clasifica el avance analítico de una clave dentro de un
        procedimiento.

        Prioridad:
        1. Adjudicado.
        2. Con subasta.
        3. Con oferta viable.
        4. Sin aprobación técnica.
        5. Solo oferta inicial.
        6. Sin propuestas.
        """
        item = registro or {}

        propuestas_iniciales = cls._entero(
            item.get("total_propuestas_iniciales")
        )
        positivas = cls._entero(
            item.get("evaluaciones_positivas")
        )
        negativas = cls._entero(
            item.get("evaluaciones_negativas")
        )
        subastas = cls._entero(
            item.get("total_subastas")
        )
        adjudicados = cls._entero(
            item.get("proveedores_adjudicados")
        )
        cantidad_adjudicada = cls._decimal(
            item.get("cantidad_total_adjudicada"),
            cls.CERO,
        )

        if adjudicados > 0 or cantidad_adjudicada > cls.CERO:
            return cls.ESTADO_ADJUDICADO

        if subastas > 0:
            return cls.ESTADO_CON_SUBASTA

        if positivas > 0:
            return cls.ESTADO_CON_OFERTA_VIABLE

        if propuestas_iniciales > 0 and negativas > 0:
            return cls.ESTADO_SIN_APROBACION

        if propuestas_iniciales > 0:
            return cls.ESTADO_SOLO_OFERTA_INICIAL

        return cls.ESTADO_SIN_PROPUESTAS

    @classmethod
    def clasificar_estado_consolidado(cls, procedimientos):
        """
        Obtiene el estado consolidado usando la etapa máxima alcanzada.
        """
        registros = procedimientos or []

        if not registros:
            return cls.ESTADO_SIN_INFORMACION

        prioridad = {
            cls.ESTADO_SIN_PROPUESTAS: 0,
            cls.ESTADO_SOLO_OFERTA_INICIAL: 1,
            cls.ESTADO_SIN_APROBACION: 2,
            cls.ESTADO_CON_OFERTA_VIABLE: 3,
            cls.ESTADO_CON_SUBASTA: 4,
            cls.ESTADO_ADJUDICADO: 5,
        }

        estados = [
            registro.get("estado_analitico")
            or cls.clasificar_estado_procedimiento(registro)
            for registro in registros
        ]

        return max(
            estados,
            key=lambda estado: prioridad.get(estado, -1),
        )

    # ==========================================================
    # PROCESAMIENTO POR PROCEDIMIENTO
    # ==========================================================

    @classmethod
    def procesar_resumen_procedimientos(cls, registros):
        """
        Enriquece cada procedimiento con precios normalizados,
        precio adjudicado ponderado, variaciones y clasificaciones.
        """
        resultado = []

        for registro in registros or []:
            item = dict(registro)

            item["cantidad_requerida"] = cls._decimal(
                item.get("cantidad_requerida")
            )
            item["cantidad_total_adjudicada"] = cls._decimal(
                item.get("cantidad_total_adjudicada"),
                cls.CERO,
            )
            item["porcentaje_total_adjudicado"] = (
                cls.redondear_porcentaje(
                    item.get("porcentaje_total_adjudicado")
                )
                or cls.CERO.quantize(cls.CUANTIZADOR_PORCENTAJE)
            )
            item["valor_total_adjudicado"] = cls.redondear_precio(
                item.get("valor_total_adjudicado")
            ) or cls.CERO.quantize(cls.CUANTIZADOR_PRECIO)

            for campo in (
                "mejor_precio_inicial",
                "mejor_precio_viable",
                "mejor_precio_subasta",
                "mejor_precio_adjudicado",
            ):
                item[campo] = cls.redondear_precio(item.get(campo))

            item["precio_adjudicado_ponderado"] = (
                cls.calcular_precio_adjudicado_ponderado(
                    item.get("cantidad_total_adjudicada"),
                    item.get("valor_total_adjudicado"),
                )
            )

            precio_adjudicado = item["precio_adjudicado_ponderado"]

            item["variacion_inicial_viable"] = (
                cls.calcular_variacion(
                    item.get("mejor_precio_inicial"),
                    item.get("mejor_precio_viable"),
                )
            )
            item["variacion_viable_subasta"] = (
                cls.calcular_variacion(
                    item.get("mejor_precio_viable"),
                    item.get("mejor_precio_subasta"),
                )
            )
            item["variacion_subasta_adjudicacion"] = (
                cls.calcular_variacion(
                    item.get("mejor_precio_subasta"),
                    precio_adjudicado,
                )
            )
            item["variacion_viable_adjudicacion"] = (
                cls.calcular_variacion(
                    item.get("mejor_precio_viable"),
                    precio_adjudicado,
                )
            )

            item["clasificacion_inicial_viable"] = (
                cls.clasificar_variacion(
                    item["variacion_inicial_viable"]
                )
            )
            item["clasificacion_viable_subasta"] = (
                cls.clasificar_variacion(
                    item["variacion_viable_subasta"]
                )
            )
            item["clasificacion_subasta_adjudicacion"] = (
                cls.clasificar_variacion(
                    item["variacion_subasta_adjudicacion"]
                )
            )
            item["clasificacion_viable_adjudicacion"] = (
                cls.clasificar_variacion(
                    item["variacion_viable_adjudicacion"]
                )
            )

            item["estado_analitico"] = (
                cls.clasificar_estado_procedimiento(item)
            )

            resultado.append(item)

        return resultado

    # ==========================================================
    # CONSOLIDADO
    # ==========================================================

    @classmethod
    def _promedio(cls, valores, cuantizador):
        """Calcula un promedio ignorando valores nulos."""
        numeros = [
            cls._decimal(valor)
            for valor in valores
            if cls._decimal(valor) is not None
        ]

        if not numeros:
            return None

        return (
            sum(numeros, cls.CERO) / Decimal(len(numeros))
        ).quantize(
            cuantizador,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_precios_consolidados(cls, procedimientos):
        """
        Calcula precios promedio consolidados por etapa.

        Cada procedimiento aporta como máximo un valor por etapa,
        evitando ponderar accidentalmente por cantidad de proveedores.
        """
        registros = procedimientos or []

        return {
            "mejor_precio_inicial": cls._promedio(
                [
                    item.get("mejor_precio_inicial")
                    for item in registros
                ],
                cls.CUANTIZADOR_PRECIO,
            ),
            "mejor_precio_viable": cls._promedio(
                [
                    item.get("mejor_precio_viable")
                    for item in registros
                ],
                cls.CUANTIZADOR_PRECIO,
            ),
            "mejor_precio_subasta": cls._promedio(
                [
                    item.get("mejor_precio_subasta")
                    for item in registros
                ],
                cls.CUANTIZADOR_PRECIO,
            ),
            "precio_adjudicado_ponderado": (
                cls.calcular_precio_adjudicado_ponderado(
                    sum(
                        (
                            cls._decimal(
                                item.get(
                                    "cantidad_total_adjudicada"
                                ),
                                cls.CERO,
                            )
                            for item in registros
                        ),
                        cls.CERO,
                    ),
                    sum(
                        (
                            cls._decimal(
                                item.get(
                                    "valor_total_adjudicado"
                                ),
                                cls.CERO,
                            )
                            for item in registros
                        ),
                        cls.CERO,
                    ),
                )
            ),
        }

    @classmethod
    def calcular_variaciones_consolidadas(cls, precios):
        """Calcula las cuatro variaciones consolidadas."""
        precios = precios or {}

        inicial_viable = cls.calcular_variacion(
            precios.get("mejor_precio_inicial"),
            precios.get("mejor_precio_viable"),
        )
        viable_subasta = cls.calcular_variacion(
            precios.get("mejor_precio_viable"),
            precios.get("mejor_precio_subasta"),
        )
        subasta_adjudicacion = cls.calcular_variacion(
            precios.get("mejor_precio_subasta"),
            precios.get("precio_adjudicado_ponderado"),
        )
        viable_adjudicacion = cls.calcular_variacion(
            precios.get("mejor_precio_viable"),
            precios.get("precio_adjudicado_ponderado"),
        )

        return {
            "variacion_inicial_viable": inicial_viable,
            "variacion_viable_subasta": viable_subasta,
            "variacion_subasta_adjudicacion": (
                subasta_adjudicacion
            ),
            "variacion_viable_adjudicacion": viable_adjudicacion,
            "clasificacion_inicial_viable": (
                cls.clasificar_variacion(inicial_viable)
            ),
            "clasificacion_viable_subasta": (
                cls.clasificar_variacion(viable_subasta)
            ),
            "clasificacion_subasta_adjudicacion": (
                cls.clasificar_variacion(
                    subasta_adjudicacion
                )
            ),
            "clasificacion_viable_adjudicacion": (
                cls.clasificar_variacion(
                    viable_adjudicacion
                )
            ),
        }

    @classmethod
    def contar_estados(cls, procedimientos):
        """Cuenta procedimientos por estado analítico."""
        conteos = {
            cls.ESTADO_SIN_PROPUESTAS: 0,
            cls.ESTADO_SOLO_OFERTA_INICIAL: 0,
            cls.ESTADO_SIN_APROBACION: 0,
            cls.ESTADO_CON_OFERTA_VIABLE: 0,
            cls.ESTADO_CON_SUBASTA: 0,
            cls.ESTADO_ADJUDICADO: 0,
        }

        for item in procedimientos or []:
            estado = (
                item.get("estado_analitico")
                or cls.clasificar_estado_procedimiento(item)
            )
            conteos[estado] = conteos.get(estado, 0) + 1

        return conteos

    @classmethod
    def construir_consolidado(cls, procedimientos):
        """Construye el bloque analítico consolidado."""
        precios = cls.calcular_precios_consolidados(procedimientos)
        variaciones = cls.calcular_variaciones_consolidadas(precios)
        estados = cls.contar_estados(procedimientos)

        return {
            "estado_analitico": (
                cls.clasificar_estado_consolidado(procedimientos)
            ),
            "precios": precios,
            "variaciones": variaciones,
            "procedimientos_por_estado": estados,
        }

    # ==========================================================
    # INDICADORES
    # ==========================================================

    @classmethod
    def completar_indicadores(
        cls,
        indicadores_base,
        procedimientos,
    ):
        """
        Completa los indicadores entregados por el Repository con
        porcentajes y resultados derivados.
        """
        resultado = dict(indicadores_base or {})

        campos_enteros = (
            "total_procedimientos",
            "total_proveedores_participantes",
            "total_propuestas_iniciales",
            "total_evaluaciones_positivas",
            "total_evaluaciones_negativas",
            "total_propuestas_subasta",
            "total_proveedores_adjudicados",
            "total_procedimientos_adjudicados",
        )

        for campo in campos_enteros:
            resultado[campo] = cls._entero(resultado.get(campo))

        resultado["cantidad_total_adjudicada"] = cls._decimal(
            resultado.get("cantidad_total_adjudicada"),
            cls.CERO,
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
        )
        resultado["porcentaje_procedimientos_adjudicados"] = (
            cls.calcular_porcentaje(
                resultado["total_procedimientos_adjudicados"],
                resultado["total_procedimientos"],
            )
        )
        resultado["promedio_propuestas_iniciales_por_procedimiento"] = (
            cls._promedio(
                [
                    item.get("total_propuestas_iniciales")
                    for item in procedimientos or []
                ],
                cls.CUANTIZADOR_PORCENTAJE,
            )
            or cls.CERO.quantize(cls.CUANTIZADOR_PORCENTAJE)
        )
        resultado["estado_analitico_consolidado"] = (
            cls.clasificar_estado_consolidado(procedimientos)
        )

        return resultado

    # ==========================================================
    # DETALLE DE PROVEEDORES
    # ==========================================================

    @classmethod
    def procesar_detalle_proveedores(cls, registros):
        """Normaliza el detalle por proveedor para la interfaz."""
        resultado = []

        for registro in registros or []:
            item = dict(registro)

            for campo in (
                "cantidad_inicial",
                "cantidad_subasta",
                "cantidad_adjudicada",
                "porcentaje_adjudicado",
            ):
                item[campo] = cls._decimal(item.get(campo))

            for campo in (
                "precio_inicial",
                "precio_subasta",
                "precio_adjudicado",
            ):
                item[campo] = cls.redondear_precio(item.get(campo))

            resultado_tecnico = item.get("resultado_tecnico")
            item["tiene_oferta_inicial"] = (
                item.get("id_propuesta_inicial") is not None
            )
            item["evaluado"] = (
                item.get("id_evaluacion") is not None
            )
            item["aprobado_tecnicamente"] = (
                resultado_tecnico
                == AnalisisClaveRepository.RESULTADO_POSITIVA
            )
            item["tiene_subasta"] = (
                item.get("id_propuesta_subasta") is not None
            )
            item["adjudicado"] = (
                item.get("id_adjudicacion") is not None
            )

            resultado.append(item)

        return resultado

    # ==========================================================
    # HISTORIAL
    # ==========================================================

    @classmethod
    def procesar_historial_precios(cls, registros):
        """Normaliza y enriquece el historial para gráficas."""
        resultado = []

        for registro in registros or []:
            item = dict(registro)

            for campo in (
                "mejor_precio_inicial",
                "mejor_precio_viable",
                "mejor_precio_subasta",
                "mejor_precio_adjudicado",
            ):
                item[campo] = cls.redondear_precio(item.get(campo))

            item["cantidad_total_adjudicada"] = cls._decimal(
                item.get("cantidad_total_adjudicada"),
                cls.CERO,
            )
            item["valor_total_adjudicado"] = cls.redondear_precio(
                item.get("valor_total_adjudicado")
            ) or cls.CERO.quantize(cls.CUANTIZADOR_PRECIO)

            item["precio_adjudicado_ponderado"] = (
                cls.calcular_precio_adjudicado_ponderado(
                    item["cantidad_total_adjudicada"],
                    item["valor_total_adjudicado"],
                )
            )

            item["variacion_viable_adjudicacion"] = (
                cls.calcular_variacion(
                    item.get("mejor_precio_viable"),
                    item.get("precio_adjudicado_ponderado"),
                )
            )
            item["clasificacion_viable_adjudicacion"] = (
                cls.clasificar_variacion(
                    item["variacion_viable_adjudicacion"]
                )
            )

            resultado.append(item)

        return resultado

    # ==========================================================
    # RESPUESTAS PARA STREAMLIT
    # ==========================================================

    def obtener_catalogos_filtros(self, id_clave=None, conn=None):
        """
        Obtiene los catálogos necesarios para construir filtros.

        Sin clave seleccionada devuelve únicamente el catálogo de claves.
        """
        respuesta = {
            "claves": (
                self.repository.obtener_claves_filtro(conn=conn)
                or []
            ),
            "procedimientos": [],
            "ejercicios": [],
        }

        if id_clave is not None:
            respuesta["procedimientos"] = (
                self.repository.obtener_procedimientos_filtro(
                    id_clave=id_clave,
                    conn=conn,
                )
                or []
            )
            respuesta["ejercicios"] = (
                self.repository.obtener_ejercicios_filtro(
                    id_clave=id_clave,
                    conn=conn,
                )
                or []
            )

        return respuesta

    def obtener_analisis_clave(
        self,
        id_clave,
        id_procedimiento=None,
        ejercicio=None,
        conn=None,
    ):
        """
        Construye la respuesta completa que consumirá Streamlit.
        """
        if id_clave is None:
            raise ValueError(
                "id_clave es obligatorio para obtener el análisis."
            )

        informacion_clave = (
            self.repository.obtener_informacion_clave(
                id_clave=id_clave,
                conn=conn,
            )
            or {}
        )

        indicadores_base = (
            self.repository.obtener_indicadores_clave(
                id_clave=id_clave,
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or {}
        )

        resumen_base = (
            self.repository.obtener_resumen_procedimientos(
                id_clave=id_clave,
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        detalle_base = (
            self.repository.obtener_detalle_proveedores(
                id_clave=id_clave,
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        historial_base = (
            self.repository.obtener_historial_precios(
                id_clave=id_clave,
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        procedimientos = self.procesar_resumen_procedimientos(
            resumen_base
        )
        detalle_proveedores = self.procesar_detalle_proveedores(
            detalle_base
        )
        historial_precios = self.procesar_historial_precios(
            historial_base
        )
        consolidado = self.construir_consolidado(procedimientos)
        indicadores = self.completar_indicadores(
            indicadores_base,
            procedimientos,
        )

        return {
            "filtros": {
                "id_clave": id_clave,
                "id_procedimiento": id_procedimiento,
                "ejercicio": ejercicio,
            },
            "clave": dict(informacion_clave),
            "indicadores": indicadores,
            "consolidado": consolidado,
            "graficas": {
                "historial_precios": historial_precios,
                "variaciones_por_procedimiento": procedimientos,
                "procedimientos_por_estado": [
                    {
                        "estado_analitico": estado,
                        "total_procedimientos": total,
                    }
                    for estado, total in consolidado[
                        "procedimientos_por_estado"
                    ].items()
                ],
            },
            "tablas": {
                "resumen_procedimientos": procedimientos,
                "detalle_proveedores": detalle_proveedores,
                "historial_precios": historial_precios,
            },
        }