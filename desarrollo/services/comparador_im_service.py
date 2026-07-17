"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

comparador_im_service.py

Service analítico para el Comparador de Investigaciones
de Mercado (IM).

Bloques 014.2.1 y 014.2.2:
- Preparación de precios válidos.
- Estadística descriptiva con Decimal.
- Percentiles con interpolación lineal.
- Desviación estándar poblacional.
- Rango intercuartil.
- Límites para detección de valores atípicos.
- Construcción de fuentes de mercado.
- Selección de referencia y precio objetivo.
- Clasificación de desviaciones.
- Nivel de confianza y tendencia.
- Riesgo y recomendaciones determinísticas.
- Preparación y validación de la nueva IM.
- Resolución de claves contra el catálogo.
- Orquestación completa por clave.
- Contrato final para Streamlit.

Este Service:
- No ejecuta SQL.
- No abre conexiones.
- No administra transacciones.
- No persiste archivos ni resultados.
- No contiene componentes de Streamlit.
- No mezcla precios de claves diferentes.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, ROUND_HALF_UP, localcontext

from repositories.comparador_im_repository import (
    ComparadorIMRepository,
)
from services.analisis_economico_service import (
    AnalisisEconomicoService,
)
from services.normalizacion_service import (
    normalizar_clave,
    normalizar_decimal,
    normalizar_nombre_columna,
    normalizar_numero,
    normalizar_pais,
    normalizar_razon_social,
    normalizar_rfc,
    normalizar_texto,
)


class ComparadorIMService(AnalisisEconomicoService):
    """
    Motor analítico del Comparador de Investigaciones de Mercado.

    Concentra el núcleo estadístico y las reglas de inteligencia
    de mercado. La orquestación completa de la IM se incorporará
    en el bloque 014.2.3.
    """

    CUANTIZADOR_ESTADISTICO = Decimal("0.01")
    FACTOR_ATIPICO_IQR = Decimal("1.5")
    MINIMO_OBSERVACIONES_ATIPICOS = 4

    TIPO_ATIPICO_INFERIOR = "INFERIOR"
    TIPO_ATIPICO_SUPERIOR = "SUPERIOR"

    FUENTE_ADJUDICACIONES = "ADJUDICACIONES"
    FUENTE_SUBASTAS = "SUBASTAS"
    FUENTE_PROPUESTAS_VIABLES = "PROPUESTAS_VIABLES"
    FUENTE_PROPUESTAS_INICIALES = "PROPUESTAS_INICIALES"
    FUENTE_SIN_REFERENCIA = "SIN_REFERENCIA"

    DESVIACION_MUY_COMPETITIVO = "MUY COMPETITIVO"
    DESVIACION_COMPETITIVO = "COMPETITIVO"
    DESVIACION_EN_MERCADO = "EN MERCADO"
    DESVIACION_LIGERAMENTE_ELEVADO = "LIGERAMENTE ELEVADO"
    DESVIACION_ELEVADO = "ELEVADO"
    DESVIACION_MUY_ELEVADO = "MUY ELEVADO"
    DESVIACION_INSUFICIENTE = "INFORMACIÓN INSUFICIENTE"

    CONFIANZA_SIN_INFORMACION = "SIN INFORMACIÓN"
    CONFIANZA_MUY_BAJA = "MUY BAJA"
    CONFIANZA_BAJA = "BAJA"
    CONFIANZA_MEDIA = "MEDIA"
    CONFIANZA_ALTA = "ALTA"

    TENDENCIA_DESCENDENTE = "DESCENDENTE"
    TENDENCIA_ESTABLE = "ESTABLE"
    TENDENCIA_ASCENDENTE = "ASCENDENTE"
    TENDENCIA_VOLATIL = "VOLÁTIL"
    TENDENCIA_INSUFICIENTE = "INFORMACIÓN INSUFICIENTE"

    RIESGO_BAJO = "BAJO"
    RIESGO_MEDIO = "MEDIO"
    RIESGO_ALTO = "ALTO"
    RIESGO_INDETERMINADO = "INDETERMINADO"

    LIMITE_MUY_COMPETITIVO = Decimal("-10")
    LIMITE_COMPETITIVO = Decimal("-3")
    LIMITE_EN_MERCADO = Decimal("3")
    LIMITE_LIGERAMENTE_ELEVADO = Decimal("10")
    LIMITE_ELEVADO = Decimal("20")

    LIMITE_TENDENCIA = Decimal("5")
    LIMITE_CAMBIO_VOLATIL = Decimal("10")

    def __init__(self, repository=None):
        self.repository = repository or ComparadorIMRepository()

    # ==========================================================
    # UTILIDADES INTERNAS
    # ==========================================================

    @classmethod
    def _redondear_estadistico(cls, valor):
        """
        Redondea un resultado estadístico a dos decimales.

        Devuelve None cuando el valor no puede convertirse a
        Decimal finito.
        """
        numero = cls._decimal(valor)

        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_ESTADISTICO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def _raiz_cuadrada_decimal(cls, valor):
        """
        Calcula la raíz cuadrada de un Decimal no negativo.

        Utiliza el contexto decimal local para evitar conversiones
        a float y conservar precisión determinística.
        """
        numero = cls._decimal(valor)

        if numero is None or numero < cls.CERO:
            return None

        if numero == cls.CERO:
            return cls.CERO

        with localcontext() as contexto:
            contexto.prec = 32
            return numero.sqrt()

    # ==========================================================
    # PREPARACIÓN DE PRECIOS
    # ==========================================================

    @classmethod
    def extraer_precios_validos(
        cls,
        registros,
        campo_precio="precio_unitario",
    ):
        """
        Extrae precios positivos y finitos de una colección.

        Admite:
        - diccionarios, utilizando campo_precio;
        - valores numéricos directos.

        Se descartan:
        - None;
        - cadenas vacías;
        - texto no numérico;
        - NaN e infinitos;
        - cero;
        - valores negativos.

        Conserva observaciones repetidas porque cada una representa
        una participación real del mercado.
        """
        if registros is None:
            return []

        precios = []

        for registro in registros:
            if isinstance(registro, dict):
                valor = registro.get(campo_precio)
            else:
                valor = registro

            precio = cls._decimal(valor)

            if precio is None or precio <= cls.CERO:
                continue

            precios.append(precio)

        return precios

    # ==========================================================
    # ESTADÍSTICA DESCRIPTIVA
    # ==========================================================

    @classmethod
    def calcular_promedio(cls, valores):
        """
        Calcula el promedio aritmético de valores positivos válidos.
        """
        precios = cls.extraer_precios_validos(valores)

        if not precios:
            return None

        promedio = sum(precios, cls.CERO) / Decimal(len(precios))

        return cls._redondear_estadistico(promedio)

    @classmethod
    def calcular_mediana(cls, valores):
        """
        Calcula la mediana de valores positivos válidos.
        """
        precios = sorted(cls.extraer_precios_validos(valores))

        total = len(precios)

        if total == 0:
            return None

        indice_medio = total // 2

        if total % 2 == 1:
            mediana = precios[indice_medio]
        else:
            mediana = (
                precios[indice_medio - 1]
                + precios[indice_medio]
            ) / Decimal("2")

        return cls._redondear_estadistico(mediana)

    @classmethod
    def calcular_percentil(cls, valores, percentil):
        """
        Calcula un percentil mediante interpolación lineal.

        Fórmula de posición:
            (n - 1) * p

        donde p se expresa entre 0 y 1.

        Ejemplos:
            percentil=25
            percentil=Decimal("75")
        """
        precios = sorted(cls.extraer_precios_validos(valores))
        porcentaje = cls._decimal(percentil)

        if not precios or porcentaje is None:
            return None

        if porcentaje < cls.CERO or porcentaje > Decimal("100"):
            raise ValueError(
                "El percentil debe estar entre 0 y 100."
            )

        if len(precios) == 1:
            return cls._redondear_estadistico(precios[0])

        proporcion = porcentaje / Decimal("100")
        posicion = Decimal(len(precios) - 1) * proporcion

        indice_inferior = int(posicion)
        indice_superior = min(
            indice_inferior + 1,
            len(precios) - 1,
        )

        fraccion = posicion - Decimal(indice_inferior)

        valor_inferior = precios[indice_inferior]
        valor_superior = precios[indice_superior]

        resultado = (
            valor_inferior
            + ((valor_superior - valor_inferior) * fraccion)
        )

        return cls._redondear_estadistico(resultado)

    @classmethod
    def calcular_desviacion_estandar(cls, valores):
        """
        Calcula la desviación estándar poblacional.

        Se utiliza la versión poblacional porque las observaciones
        disponibles constituyen el universo conocido en SIMI para
        la fuente y clave analizadas.
        """
        precios = cls.extraer_precios_validos(valores)

        if not precios:
            return None

        if len(precios) == 1:
            return cls.CERO.quantize(
                cls.CUANTIZADOR_ESTADISTICO
            )

        promedio = (
            sum(precios, cls.CERO)
            / Decimal(len(precios))
        )

        suma_cuadrados = sum(
            (
                (precio - promedio)
                * (precio - promedio)
            )
            for precio in precios
        )

        varianza = suma_cuadrados / Decimal(len(precios))
        desviacion = cls._raiz_cuadrada_decimal(varianza)

        return cls._redondear_estadistico(desviacion)

    @classmethod
    def calcular_estadisticas(cls, valores):
        """
        Construye el resumen estadístico completo de una colección.

        Todos los resultados se calculan exclusivamente sobre
        precios positivos y finitos.
        """
        precios = cls.extraer_precios_validos(valores)

        if not precios:
            return {
                "total_observaciones": 0,
                "precio_minimo": None,
                "precio_maximo": None,
                "precio_promedio": None,
                "precio_mediana": None,
                "desviacion_estandar": None,
                "percentil_25": None,
                "percentil_75": None,
                "rango_intercuartil": None,
            }

        minimo = min(precios)
        maximo = max(precios)
        percentil_25 = cls.calcular_percentil(
            precios,
            Decimal("25"),
        )
        percentil_75 = cls.calcular_percentil(
            precios,
            Decimal("75"),
        )

        rango_intercuartil = None

        if percentil_25 is not None and percentil_75 is not None:
            rango_intercuartil = cls._redondear_estadistico(
                percentil_75 - percentil_25
            )

        return {
            "total_observaciones": len(precios),
            "precio_minimo": cls._redondear_estadistico(minimo),
            "precio_maximo": cls._redondear_estadistico(maximo),
            "precio_promedio": cls.calcular_promedio(precios),
            "precio_mediana": cls.calcular_mediana(precios),
            "desviacion_estandar": (
                cls.calcular_desviacion_estandar(precios)
            ),
            "percentil_25": percentil_25,
            "percentil_75": percentil_75,
            "rango_intercuartil": rango_intercuartil,
        }

    # ==========================================================
    # DETECCIÓN DE VALORES ATÍPICOS
    # ==========================================================

    @classmethod
    def calcular_limites_atipicos(cls, valores):
        """
        Calcula límites inferior y superior mediante la regla IQR.

        La detección solo se habilita cuando existen al menos cuatro
        observaciones válidas.
        """
        estadisticas = cls.calcular_estadisticas(valores)
        total = estadisticas["total_observaciones"]

        if total < cls.MINIMO_OBSERVACIONES_ATIPICOS:
            return {
                "deteccion_disponible": False,
                "total_observaciones": total,
                "limite_inferior": None,
                "limite_superior": None,
                "percentil_25": estadisticas["percentil_25"],
                "percentil_75": estadisticas["percentil_75"],
                "rango_intercuartil": (
                    estadisticas["rango_intercuartil"]
                ),
            }

        percentil_25 = estadisticas["percentil_25"]
        percentil_75 = estadisticas["percentil_75"]
        rango_intercuartil = estadisticas["rango_intercuartil"]

        limite_inferior = (
            percentil_25
            - (
                cls.FACTOR_ATIPICO_IQR
                * rango_intercuartil
            )
        )
        limite_superior = (
            percentil_75
            + (
                cls.FACTOR_ATIPICO_IQR
                * rango_intercuartil
            )
        )

        return {
            "deteccion_disponible": True,
            "total_observaciones": total,
            "limite_inferior": cls._redondear_estadistico(
                limite_inferior
            ),
            "limite_superior": cls._redondear_estadistico(
                limite_superior
            ),
            "percentil_25": percentil_25,
            "percentil_75": percentil_75,
            "rango_intercuartil": rango_intercuartil,
        }

    @classmethod
    def evaluar_valor_atipico(cls, valor, valores_referencia):
        """
        Evalúa si un valor es atípico respecto de una distribución.

        No clasifica como atípico cuando:
        - el valor es inválido;
        - hay menos de cuatro observaciones válidas;
        - el valor permanece dentro de los límites IQR.
        """
        precio = cls._decimal(valor)
        limites = cls.calcular_limites_atipicos(
            valores_referencia
        )

        resultado_base = {
            "valor": cls._redondear_estadistico(precio),
            "deteccion_disponible": (
                limites["deteccion_disponible"]
            ),
            "es_valor_atipico": False,
            "tipo_atipico": None,
            "limite_inferior": limites["limite_inferior"],
            "limite_superior": limites["limite_superior"],
        }

        if precio is None or precio <= cls.CERO:
            return resultado_base

        if not limites["deteccion_disponible"]:
            return resultado_base

        if precio < limites["limite_inferior"]:
            resultado_base["es_valor_atipico"] = True
            resultado_base["tipo_atipico"] = (
                cls.TIPO_ATIPICO_INFERIOR
            )

        elif precio > limites["limite_superior"]:
            resultado_base["es_valor_atipico"] = True
            resultado_base["tipo_atipico"] = (
                cls.TIPO_ATIPICO_SUPERIOR
            )

        return resultado_base

    # ==========================================================
    # FUENTES DE MERCADO
    # ==========================================================

    @classmethod
    def construir_fuentes_mercado(
        cls,
        propuestas=None,
        adjudicaciones_operativas=None,
        adjudicaciones_historicas=None,
    ):
        """
        Separa las observaciones de una clave por fuente económica.
        """
        propuestas = propuestas or []
        adjudicaciones_operativas = adjudicaciones_operativas or []
        adjudicaciones_historicas = adjudicaciones_historicas or []

        iniciales = []
        viables = []
        subastas = []

        for registro in propuestas:
            if not isinstance(registro, dict):
                continue

            tipo = str(
                registro.get("tipo_propuesta") or ""
            ).strip().upper()

            precio = cls._decimal(
                registro.get("precio_unitario")
            )

            if precio is None or precio <= cls.CERO:
                continue

            if tipo == "INICIAL":
                iniciales.append(precio)

                resultado_tecnico = str(
                    registro.get("resultado_tecnico") or ""
                ).strip().upper()

                if resultado_tecnico == "POSITIVA":
                    viables.append(precio)

            elif tipo == "SUBASTA":
                subastas.append(precio)

        operativas = cls.extraer_precios_validos(
            adjudicaciones_operativas,
            campo_precio="precio_unitario_adjudicado",
        )
        historicas = cls.extraer_precios_validos(
            adjudicaciones_historicas,
            campo_precio="precio_unitario_adjudicado",
        )

        return {
            "propuestas_iniciales": iniciales,
            "propuestas_viables": viables,
            "subastas": subastas,
            "adjudicaciones_operativas": operativas,
            "adjudicaciones_historicas": historicas,
            "adjudicaciones": operativas + historicas,
        }

    @classmethod
    def calcular_estadisticas_fuentes(cls, fuentes):
        """
        Calcula estadísticas descriptivas para cada fuente.
        """
        fuentes = fuentes or {}

        return {
            nombre: cls.calcular_estadisticas(valores)
            for nombre, valores in fuentes.items()
        }

    # ==========================================================
    # REFERENCIA Y PRECIO OBJETIVO
    # ==========================================================

    @classmethod
    def seleccionar_referencia_mercado(cls, fuentes):
        """
        Selecciona la mediana de la fuente disponible con mayor
        prioridad.
        """
        fuentes = fuentes or {}

        prioridades = (
            (
                cls.FUENTE_ADJUDICACIONES,
                fuentes.get("adjudicaciones", []),
            ),
            (
                cls.FUENTE_SUBASTAS,
                fuentes.get("subastas", []),
            ),
            (
                cls.FUENTE_PROPUESTAS_VIABLES,
                fuentes.get("propuestas_viables", []),
            ),
            (
                cls.FUENTE_PROPUESTAS_INICIALES,
                fuentes.get("propuestas_iniciales", []),
            ),
        )

        for nombre_fuente, valores in prioridades:
            estadisticas = cls.calcular_estadisticas(valores)

            if estadisticas["total_observaciones"] > 0:
                return {
                    "precio_referencia": (
                        estadisticas["precio_mediana"]
                    ),
                    "fuente_referencia": nombre_fuente,
                    "total_observaciones": (
                        estadisticas["total_observaciones"]
                    ),
                    "estadisticas_referencia": estadisticas,
                }

        return {
            "precio_referencia": None,
            "fuente_referencia": cls.FUENTE_SIN_REFERENCIA,
            "total_observaciones": 0,
            "estadisticas_referencia": cls.calcular_estadisticas([]),
        }

    @classmethod
    def calcular_precio_objetivo(cls, referencia):
        """
        Usa la mediana como precio objetivo y, con al menos cuatro
        observaciones, el rango P25-mediana.
        """
        referencia = referencia or {}
        estadisticas = referencia.get(
            "estadisticas_referencia"
        ) or {}
        precio_referencia = cls._decimal(
            referencia.get("precio_referencia")
        )
        total = int(
            referencia.get("total_observaciones") or 0
        )

        if precio_referencia is None:
            return {
                "precio_objetivo": None,
                "rango_objetivo_minimo": None,
                "rango_objetivo_maximo": None,
                "rango_disponible": False,
            }

        rango_disponible = total >= 4
        minimo = None

        if rango_disponible:
            minimo = cls._decimal(
                estadisticas.get("percentil_25")
            )

        return {
            "precio_objetivo": cls._redondear_estadistico(
                precio_referencia
            ),
            "rango_objetivo_minimo": (
                cls._redondear_estadistico(minimo)
                if minimo is not None
                else None
            ),
            "rango_objetivo_maximo": (
                cls._redondear_estadistico(precio_referencia)
                if rango_disponible
                else None
            ),
            "rango_disponible": rango_disponible,
        }

    # ==========================================================
    # DESVIACIÓN Y CONFIANZA
    # ==========================================================

    @classmethod
    def clasificar_desviacion(cls, variacion):
        """
        Clasifica la variación porcentual contra la referencia.
        """
        valor = cls._decimal(variacion)

        if valor is None:
            return cls.DESVIACION_INSUFICIENTE

        if valor < cls.LIMITE_MUY_COMPETITIVO:
            return cls.DESVIACION_MUY_COMPETITIVO

        if valor < cls.LIMITE_COMPETITIVO:
            return cls.DESVIACION_COMPETITIVO

        if valor <= cls.LIMITE_EN_MERCADO:
            return cls.DESVIACION_EN_MERCADO

        if valor <= cls.LIMITE_LIGERAMENTE_ELEVADO:
            return cls.DESVIACION_LIGERAMENTE_ELEVADO

        if valor <= cls.LIMITE_ELEVADO:
            return cls.DESVIACION_ELEVADO

        return cls.DESVIACION_MUY_ELEVADO

    @classmethod
    def calcular_nivel_confianza(cls, total_observaciones):
        """
        Clasifica el respaldo estadístico de la referencia.
        """
        try:
            total = int(total_observaciones or 0)
        except (TypeError, ValueError, OverflowError):
            total = 0

        if total <= 0:
            return cls.CONFIANZA_SIN_INFORMACION
        if total <= 2:
            return cls.CONFIANZA_MUY_BAJA
        if total <= 4:
            return cls.CONFIANZA_BAJA
        if total <= 9:
            return cls.CONFIANZA_MEDIA
        return cls.CONFIANZA_ALTA

    # ==========================================================
    # TENDENCIA
    # ==========================================================

    @classmethod
    def _clave_temporal_adjudicacion(cls, registro):
        """
        Construye una clave estable por procedimiento.
        """
        origen = str(
            registro.get("origen_dato") or ""
        ).strip().upper()
        ejercicio = registro.get("ejercicio")
        numero = str(
            registro.get("numero_procedimiento") or ""
        ).strip()
        id_procedimiento = registro.get("id_procedimiento")

        return (
            origen,
            ejercicio,
            numero,
            id_procedimiento,
        )

    @classmethod
    def construir_serie_temporal_adjudicada(
        cls,
        adjudicaciones,
    ):
        """
        Agrupa adjudicaciones por procedimiento y calcula una
        mediana por periodo.
        """
        grupos = {}

        for registro in adjudicaciones or []:
            if not isinstance(registro, dict):
                continue

            precio = cls._decimal(
                registro.get("precio_unitario_adjudicado")
            )

            if precio is None or precio <= cls.CERO:
                continue

            clave = cls._clave_temporal_adjudicacion(registro)
            grupos.setdefault(clave, []).append(precio)

        serie = []

        for clave, precios in grupos.items():
            origen, ejercicio, numero, id_procedimiento = clave

            try:
                ejercicio_orden = int(ejercicio)
            except (TypeError, ValueError, OverflowError):
                ejercicio_orden = 9999

            serie.append(
                {
                    "origen_dato": origen or None,
                    "ejercicio": (
                        None
                        if ejercicio_orden == 9999
                        else ejercicio_orden
                    ),
                    "numero_procedimiento": numero or None,
                    "id_procedimiento": id_procedimiento,
                    "precio_mediana": cls.calcular_mediana(
                        precios
                    ),
                    "total_observaciones": len(precios),
                    "_orden": (
                        ejercicio_orden,
                        numero,
                        (
                            id_procedimiento
                            if id_procedimiento is not None
                            else 0
                        ),
                        origen,
                    ),
                }
            )

        serie.sort(key=lambda item: item["_orden"])

        for item in serie:
            item.pop("_orden", None)

        return serie

    @classmethod
    def calcular_tendencia(cls, adjudicaciones):
        """
        Clasifica la tendencia adjudicada.
        """
        serie = cls.construir_serie_temporal_adjudicada(
            adjudicaciones
        )

        if len(serie) < 3:
            return {
                "tendencia": cls.TENDENCIA_INSUFICIENTE,
                "variacion_tendencia": None,
                "total_periodos": len(serie),
                "serie": serie,
            }

        precios = [
            item["precio_mediana"]
            for item in serie
        ]

        cambios = [
            cls.calcular_variacion(
                precios[indice - 1],
                precios[indice],
            )
            for indice in range(1, len(precios))
        ]
        cambios_validos = [
            cambio
            for cambio in cambios
            if cambio is not None
        ]

        tiene_alza_fuerte = any(
            cambio > cls.LIMITE_CAMBIO_VOLATIL
            for cambio in cambios_validos
        )
        tiene_baja_fuerte = any(
            cambio < -cls.LIMITE_CAMBIO_VOLATIL
            for cambio in cambios_validos
        )

        if tiene_alza_fuerte and tiene_baja_fuerte:
            tendencia = cls.TENDENCIA_VOLATIL
        else:
            punto_corte = len(precios) // 2
            mitad_inicial = precios[:punto_corte]
            mitad_reciente = precios[punto_corte:]

            mediana_inicial = cls.calcular_mediana(
                mitad_inicial
            )
            mediana_reciente = cls.calcular_mediana(
                mitad_reciente
            )
            variacion = cls.calcular_variacion(
                mediana_inicial,
                mediana_reciente,
            )

            if variacion is None:
                tendencia = cls.TENDENCIA_INSUFICIENTE
            elif variacion < -cls.LIMITE_TENDENCIA:
                tendencia = cls.TENDENCIA_DESCENDENTE
            elif variacion > cls.LIMITE_TENDENCIA:
                tendencia = cls.TENDENCIA_ASCENDENTE
            else:
                tendencia = cls.TENDENCIA_ESTABLE

        return {
            "tendencia": tendencia,
            "variacion_tendencia": cls.calcular_variacion(
                precios[0],
                precios[-1],
            ),
            "total_periodos": len(serie),
            "serie": serie,
        }

    # ==========================================================
    # RIESGO Y RECOMENDACIONES
    # ==========================================================

    @classmethod
    def calcular_riesgo(
        cls,
        clasificacion_desviacion,
        nivel_confianza,
        evaluacion_atipico=None,
        tendencia=None,
    ):
        """
        Calcula riesgo mediante reglas determinísticas.
        """
        evaluacion_atipico = evaluacion_atipico or {}
        tendencia = tendencia or cls.TENDENCIA_INSUFICIENTE

        if (
            clasificacion_desviacion
            == cls.DESVIACION_INSUFICIENTE
        ):
            return cls.RIESGO_INDETERMINADO

        if (
            evaluacion_atipico.get("es_valor_atipico")
            and evaluacion_atipico.get("tipo_atipico")
            == cls.TIPO_ATIPICO_SUPERIOR
        ):
            return cls.RIESGO_ALTO

        if clasificacion_desviacion in {
            cls.DESVIACION_ELEVADO,
            cls.DESVIACION_MUY_ELEVADO,
        }:
            return cls.RIESGO_ALTO

        if (
            evaluacion_atipico.get("es_valor_atipico")
            or clasificacion_desviacion
            == cls.DESVIACION_LIGERAMENTE_ELEVADO
            or nivel_confianza
            in {
                cls.CONFIANZA_MUY_BAJA,
                cls.CONFIANZA_BAJA,
            }
            or tendencia == cls.TENDENCIA_VOLATIL
        ):
            return cls.RIESGO_MEDIO

        return cls.RIESGO_BAJO

    @classmethod
    def generar_recomendaciones(cls, comparacion):
        """
        Genera recomendaciones estructuradas y explicables.
        """
        comparacion = comparacion or {}
        recomendaciones = []

        clasificacion = comparacion.get(
            "clasificacion_desviacion"
        )
        confianza = comparacion.get("nivel_confianza")
        atipico = comparacion.get("evaluacion_atipico") or {}
        tendencia = (
            comparacion.get("tendencia") or {}
        ).get("tendencia")
        objetivo = comparacion.get("precio_objetivo") or {}

        if clasificacion == cls.DESVIACION_INSUFICIENTE:
            return [
                {
                    "codigo": "AMPLIAR_INVESTIGACION",
                    "nivel": "ADVERTENCIA",
                    "titulo": "Ampliar investigación",
                    "mensaje": (
                        "No existe información suficiente para "
                        "establecer una referencia de mercado."
                    ),
                }
            ]

        if confianza in {
            cls.CONFIANZA_MUY_BAJA,
            cls.CONFIANZA_BAJA,
        }:
            recomendaciones.append(
                {
                    "codigo": "BAJA_CONFIANZA",
                    "nivel": "ADVERTENCIA",
                    "titulo": "Validar muestra disponible",
                    "mensaje": (
                        "La referencia se sustenta en pocas "
                        "observaciones; complemente la investigación."
                    ),
                }
            )

        if clasificacion in {
            cls.DESVIACION_MUY_COMPETITIVO,
            cls.DESVIACION_COMPETITIVO,
        }:
            recomendaciones.append(
                {
                    "codigo": "PRECIO_COMPETITIVO",
                    "nivel": "FAVORABLE",
                    "titulo": "Precio competitivo",
                    "mensaje": (
                        "La cotización está por debajo de la "
                        "referencia. Valide equivalencia técnica."
                    ),
                }
            )
        elif clasificacion == cls.DESVIACION_EN_MERCADO:
            recomendaciones.append(
                {
                    "codigo": "PRECIO_EN_MERCADO",
                    "nivel": "FAVORABLE",
                    "titulo": "Precio dentro del mercado",
                    "mensaje": (
                        "La cotización está dentro del margen "
                        "de ±3% respecto de la referencia."
                    ),
                }
            )
        elif clasificacion == cls.DESVIACION_LIGERAMENTE_ELEVADO:
            recomendaciones.append(
                {
                    "codigo": "VALIDAR_PRECIO",
                    "nivel": "PRECAUCION",
                    "titulo": "Validar precio",
                    "mensaje": (
                        "La cotización está ligeramente por encima "
                        "de la referencia."
                    ),
                }
            )
        elif clasificacion in {
            cls.DESVIACION_ELEVADO,
            cls.DESVIACION_MUY_ELEVADO,
        }:
            recomendaciones.append(
                {
                    "codigo": "SOLICITAR_JUSTIFICACION",
                    "nivel": "CRITICO",
                    "titulo": "Solicitar justificación",
                    "mensaje": (
                        "La cotización supera de forma relevante "
                        "la referencia de mercado."
                    ),
                }
            )

        if atipico.get("es_valor_atipico"):
            recomendaciones.append(
                {
                    "codigo": "REVISAR_VALOR_ATIPICO",
                    "nivel": "CRITICO",
                    "titulo": "Revisar valor atípico",
                    "mensaje": (
                        "Valide captura, unidad, presentación y "
                        "condiciones comerciales del precio."
                    ),
                }
            )

        if tendencia == cls.TENDENCIA_VOLATIL:
            recomendaciones.append(
                {
                    "codigo": "REVISAR_CONDICIONES_MERCADO",
                    "nivel": "PRECAUCION",
                    "titulo": "Revisar condiciones de mercado",
                    "mensaje": (
                        "Los precios presentan cambios relevantes "
                        "en ambas direcciones."
                    ),
                }
            )
        elif tendencia == cls.TENDENCIA_ASCENDENTE:
            recomendaciones.append(
                {
                    "codigo": "MERCADO_ASCENDENTE",
                    "nivel": "INFORMATIVO",
                    "titulo": "Considerar tendencia ascendente",
                    "mensaje": (
                        "El mercado adjudicado muestra incrementos "
                        "en los periodos recientes."
                    ),
                }
            )

        if objetivo.get("rango_disponible"):
            recomendaciones.append(
                {
                    "codigo": "CONSIDERAR_PRECIO_OBJETIVO",
                    "nivel": "INFORMATIVO",
                    "titulo": "Considerar precio objetivo",
                    "mensaje": (
                        "Use el rango P25-mediana como referencia "
                        "de negociación."
                    ),
                }
            )

        return recomendaciones

    # ==========================================================
    # COMPARACIÓN INDIVIDUAL
    # ==========================================================

    @classmethod
    def comparar_cotizacion(
        cls,
        precio_im,
        cantidad,
        referencia,
        valores_referencia,
        tendencia=None,
    ):
        """
        Compara una cotización individual contra su referencia.
        """
        precio = cls._decimal(precio_im)
        cantidad_decimal = cls._decimal(cantidad)
        referencia = referencia or {}
        precio_referencia = cls._decimal(
            referencia.get("precio_referencia")
        )

        variacion = cls.calcular_variacion(
            precio_referencia,
            precio,
        )
        clasificacion = cls.clasificar_desviacion(
            variacion
        )
        nivel_confianza = cls.calcular_nivel_confianza(
            referencia.get("total_observaciones")
        )
        evaluacion_atipico = cls.evaluar_valor_atipico(
            precio,
            valores_referencia,
        )
        precio_objetivo = cls.calcular_precio_objetivo(
            referencia
        )

        diferencia_unitaria = None

        if precio is not None and precio_referencia is not None:
            diferencia_unitaria = cls.redondear_precio(
                precio - precio_referencia
            )

        importe_im = cls.calcular_importe(
            precio,
            cantidad_decimal,
        )
        importe_referencia = cls.calcular_importe(
            precio_referencia,
            cantidad_decimal,
        )

        impacto_estimado = None

        if (
            importe_im is not None
            and importe_referencia is not None
        ):
            impacto_estimado = cls.redondear_precio(
                importe_im - importe_referencia
            )

        tendencia_resultado = tendencia or {
            "tendencia": cls.TENDENCIA_INSUFICIENTE,
            "variacion_tendencia": None,
            "total_periodos": 0,
            "serie": [],
        }

        riesgo = cls.calcular_riesgo(
            clasificacion_desviacion=clasificacion,
            nivel_confianza=nivel_confianza,
            evaluacion_atipico=evaluacion_atipico,
            tendencia=tendencia_resultado.get("tendencia"),
        )

        resultado = {
            "precio_im": cls.redondear_precio(precio),
            "cantidad": cls.redondear_cantidad(
                cantidad_decimal
            ),
            "precio_referencia": cls.redondear_precio(
                precio_referencia
            ),
            "fuente_referencia": referencia.get(
                "fuente_referencia",
                cls.FUENTE_SIN_REFERENCIA,
            ),
            "total_observaciones_referencia": referencia.get(
                "total_observaciones",
                0,
            ),
            "diferencia_unitaria": diferencia_unitaria,
            "variacion_porcentual": variacion,
            "clasificacion_desviacion": clasificacion,
            "nivel_confianza": nivel_confianza,
            "importe_im": importe_im,
            "importe_referencia": importe_referencia,
            "impacto_estimado": impacto_estimado,
            "evaluacion_atipico": evaluacion_atipico,
            "precio_objetivo": precio_objetivo,
            "tendencia": tendencia_resultado,
            "nivel_riesgo": riesgo,
        }

        resultado["recomendaciones"] = (
            cls.generar_recomendaciones(resultado)
        )

        return resultado

    # ==========================================================
    # PREPARACIÓN DE LA NUEVA IM
    # ==========================================================

    ALIASES_COLUMNAS_IM = {
        "rfc": "rfc",
        "razon_social": "razon_social",
        "clave": "clave",
        "descripcion": "descripcion",
        "cantidad": "cantidad_ofertada",
        "cantidad_ofertada": "cantidad_ofertada",
        "pais_origen": "pais_origen",
        "pais_de_origen": "pais_origen",
        "precio": "precio_unitario",
        "precio_unitario": "precio_unitario",
    }

    @classmethod
    def _convertir_registros(cls, registros_im):
        """
        Convierte la entrada a una lista de diccionarios.

        Admite:
        - lista o tupla de diccionarios;
        - objetos con to_dict(orient="records"), como DataFrame.
        """
        if registros_im is None:
            return []

        if hasattr(registros_im, "to_dict"):
            try:
                registros = registros_im.to_dict(
                    orient="records"
                )
            except TypeError:
                registros = registros_im.to_dict()
        else:
            registros = list(registros_im)

        if isinstance(registros, dict):
            registros = [registros]

        return registros

    @classmethod
    def _normalizar_claves_registro(cls, registro):
        """
        Normaliza nombres de columnas y aplica aliases oficiales.
        """
        resultado = {}

        for columna, valor in (registro or {}).items():
            nombre = normalizar_nombre_columna(columna)
            nombre = cls.ALIASES_COLUMNAS_IM.get(
                nombre,
                nombre,
            )

            if nombre and nombre not in resultado:
                resultado[nombre] = valor

        return resultado

    @classmethod
    def normalizar_registro_im(cls, registro, numero_fila):
        """
        Normaliza una fila de la nueva IM sin consultar la BD.
        """
        if not isinstance(registro, dict):
            return {
                "registro": None,
                "incidencias": [
                    "La fila no tiene una estructura válida."
                ],
                "numero_fila": numero_fila,
            }

        origen = cls._normalizar_claves_registro(registro)

        normalizado = {
            "numero_fila": numero_fila,
            "rfc": normalizar_rfc(origen.get("rfc")),
            "razon_social": normalizar_razon_social(
                origen.get("razon_social")
            ),
            "clave": normalizar_clave(
                origen.get("clave")
            ),
            "descripcion": normalizar_texto(
                origen.get("descripcion")
            ),
            "cantidad_ofertada": normalizar_numero(
                origen.get("cantidad_ofertada")
            ),
            "pais_origen": normalizar_pais(
                origen.get("pais_origen")
            ),
            "precio_unitario": normalizar_decimal(
                origen.get("precio_unitario")
            ),
        }

        incidencias = []

        if not normalizado["rfc"]:
            incidencias.append("RFC requerido.")

        if not normalizado["razon_social"]:
            incidencias.append("Razón social requerida.")

        if not normalizado["clave"]:
            incidencias.append("Clave requerida.")

        cantidad = cls._decimal(
            normalizado["cantidad_ofertada"]
        )
        precio = cls._decimal(
            normalizado["precio_unitario"]
        )

        if cantidad is None or cantidad <= cls.CERO:
            incidencias.append(
                "Cantidad ofertada debe ser mayor que cero."
            )

        if precio is None or precio <= cls.CERO:
            incidencias.append(
                "Precio unitario debe ser mayor que cero."
            )

        normalizado["cantidad_ofertada"] = cantidad
        normalizado["precio_unitario"] = precio

        return {
            "registro": normalizado,
            "incidencias": incidencias,
            "numero_fila": numero_fila,
        }

    @classmethod
    def preparar_registros_im(cls, registros_im):
        """
        Normaliza y valida estructuralmente todos los registros.
        """
        registros = cls._convertir_registros(registros_im)

        validos = []
        invalidos = []

        for indice, registro in enumerate(
            registros,
            start=2,
        ):
            resultado = cls.normalizar_registro_im(
                registro=registro,
                numero_fila=indice,
            )

            if resultado["incidencias"]:
                invalidos.append(
                    {
                        "numero_fila": indice,
                        "registro": resultado["registro"],
                        "errores": resultado["incidencias"],
                    }
                )
            else:
                validos.append(resultado["registro"])

        return {
            "total_filas_recibidas": len(registros),
            "registros_validos": validos,
            "registros_invalidos": invalidos,
        }

    # ==========================================================
    # RESOLUCIÓN DE CLAVES
    # ==========================================================

    def resolver_claves_im(self, registros, conn=None):
        """
        Resuelve las claves normalizadas contra simi.claves.
        """
        registros = registros or []
        codigos = list(
            dict.fromkeys(
                registro["clave"]
                for registro in registros
                if registro.get("clave")
            )
        )

        claves_catalogo = (
            self.repository.obtener_claves_por_codigos(
                claves=codigos,
                conn=conn,
            )
            if codigos
            else []
        )

        mapa_claves = {
            registro["clave"]: registro
            for registro in claves_catalogo
        }

        encontrados = []
        no_encontrados = []

        for registro in registros:
            clave_catalogo = mapa_claves.get(
                registro.get("clave")
            )

            if clave_catalogo is None:
                no_encontrados.append(
                    {
                        "numero_fila": registro.get(
                            "numero_fila"
                        ),
                        "clave": registro.get("clave"),
                        "rfc": registro.get("rfc"),
                        "razon_social": registro.get(
                            "razon_social"
                        ),
                        "error": (
                            "La clave no existe en el catálogo "
                            "oficial de SIMI."
                        ),
                    }
                )
                continue

            registro_resuelto = dict(registro)
            registro_resuelto.update(
                {
                    "id_clave": clave_catalogo[
                        "id_clave"
                    ],
                    "descripcion_catalogo": (
                        clave_catalogo.get("descripcion")
                    ),
                    "id_categoria": clave_catalogo.get(
                        "id_categoria"
                    ),
                    "categoria": clave_catalogo.get(
                        "categoria"
                    ),
                }
            )
            encontrados.append(registro_resuelto)

        return {
            "registros_resueltos": encontrados,
            "claves_no_encontradas": no_encontrados,
            "claves_catalogo": claves_catalogo,
        }

    # ==========================================================
    # AGRUPACIÓN DEL CONTEXTO
    # ==========================================================

    @staticmethod
    def _agrupar_por_id_clave(registros):
        """
        Agrupa registros planos por id_clave.
        """
        grupos = {}

        for registro in registros or []:
            if not isinstance(registro, dict):
                continue

            id_clave = registro.get("id_clave")

            if id_clave is None:
                continue

            grupos.setdefault(id_clave, []).append(
                registro
            )

        return grupos

    @classmethod
    def agrupar_contexto_por_clave(cls, contexto):
        """
        Agrupa el contrato del Repository por id_clave.
        """
        contexto = contexto or {}

        claves = {
            registro["id_clave"]: registro
            for registro in contexto.get("claves", [])
            if registro.get("id_clave") is not None
        }

        propuestas = cls._agrupar_por_id_clave(
            contexto.get("propuestas", [])
        )
        operativas = cls._agrupar_por_id_clave(
            contexto.get(
                "adjudicaciones_operativas",
                [],
            )
        )
        historicas = cls._agrupar_por_id_clave(
            contexto.get(
                "adjudicaciones_historicas",
                [],
            )
        )

        ids = set(claves)
        ids.update(propuestas)
        ids.update(operativas)
        ids.update(historicas)

        return {
            id_clave: {
                "clave": claves.get(id_clave, {}),
                "propuestas": propuestas.get(
                    id_clave,
                    [],
                ),
                "adjudicaciones_operativas": (
                    operativas.get(id_clave, [])
                ),
                "adjudicaciones_historicas": (
                    historicas.get(id_clave, [])
                ),
            }
            for id_clave in ids
        }

    # ==========================================================
    # ANÁLISIS POR CLAVE
    # ==========================================================

    @classmethod
    def construir_resumen_cotizaciones_clave(
        cls,
        cotizaciones,
    ):
        """
        Resume las cotizaciones nuevas de una misma clave.
        """
        precios = [
            registro.get("precio_unitario")
            for registro in cotizaciones or []
        ]
        estadisticas = cls.calcular_estadisticas(precios)

        conteos = {
            cls.DESVIACION_MUY_COMPETITIVO: 0,
            cls.DESVIACION_COMPETITIVO: 0,
            cls.DESVIACION_EN_MERCADO: 0,
            cls.DESVIACION_LIGERAMENTE_ELEVADO: 0,
            cls.DESVIACION_ELEVADO: 0,
            cls.DESVIACION_MUY_ELEVADO: 0,
            cls.DESVIACION_INSUFICIENTE: 0,
        }

        for registro in cotizaciones or []:
            clasificacion = registro.get(
                "clasificacion_desviacion"
            )

            if clasificacion in conteos:
                conteos[clasificacion] += 1

        mejor = None

        if cotizaciones:
            mejor = min(
                cotizaciones,
                key=lambda item: (
                    item.get("precio_im")
                    if item.get("precio_im") is not None
                    else Decimal("Infinity")
                ),
            )

        riesgos = [
            registro.get("nivel_riesgo")
            for registro in cotizaciones or []
        ]

        if cls.RIESGO_ALTO in riesgos:
            riesgo_clave = cls.RIESGO_ALTO
        elif cls.RIESGO_MEDIO in riesgos:
            riesgo_clave = cls.RIESGO_MEDIO
        elif cls.RIESGO_BAJO in riesgos:
            riesgo_clave = cls.RIESGO_BAJO
        else:
            riesgo_clave = cls.RIESGO_INDETERMINADO

        return {
            "total_cotizaciones_im": len(cotizaciones or []),
            "precio_minimo_im": estadisticas["precio_minimo"],
            "precio_maximo_im": estadisticas["precio_maximo"],
            "precio_promedio_im": estadisticas[
                "precio_promedio"
            ],
            "precio_mediana_im": estadisticas[
                "precio_mediana"
            ],
            "mejor_cotizacion_im": mejor,
            "cotizaciones_muy_competitivas": conteos[
                cls.DESVIACION_MUY_COMPETITIVO
            ],
            "cotizaciones_competitivas": conteos[
                cls.DESVIACION_COMPETITIVO
            ],
            "cotizaciones_en_mercado": conteos[
                cls.DESVIACION_EN_MERCADO
            ],
            "cotizaciones_ligeramente_elevadas": conteos[
                cls.DESVIACION_LIGERAMENTE_ELEVADO
            ],
            "cotizaciones_elevadas": conteos[
                cls.DESVIACION_ELEVADO
            ],
            "cotizaciones_muy_elevadas": conteos[
                cls.DESVIACION_MUY_ELEVADO
            ],
            "cotizaciones_sin_referencia": conteos[
                cls.DESVIACION_INSUFICIENTE
            ],
            "riesgo_clave": riesgo_clave,
        }

    @classmethod
    def construir_analisis_clave(
        cls,
        clave_catalogo,
        cotizaciones_im,
        contexto_clave,
    ):
        """
        Construye el análisis completo de una clave.
        """
        contexto_clave = contexto_clave or {}
        operativas = contexto_clave.get(
            "adjudicaciones_operativas",
            [],
        )
        historicas = contexto_clave.get(
            "adjudicaciones_historicas",
            [],
        )

        fuentes = cls.construir_fuentes_mercado(
            propuestas=contexto_clave.get(
                "propuestas",
                [],
            ),
            adjudicaciones_operativas=operativas,
            adjudicaciones_historicas=historicas,
        )
        estadisticas_fuentes = (
            cls.calcular_estadisticas_fuentes(fuentes)
        )
        referencia = cls.seleccionar_referencia_mercado(
            fuentes
        )
        tendencia = cls.calcular_tendencia(
            operativas + historicas
        )

        valores_referencia = []

        mapa_fuente = {
            cls.FUENTE_ADJUDICACIONES: "adjudicaciones",
            cls.FUENTE_SUBASTAS: "subastas",
            cls.FUENTE_PROPUESTAS_VIABLES: (
                "propuestas_viables"
            ),
            cls.FUENTE_PROPUESTAS_INICIALES: (
                "propuestas_iniciales"
            ),
        }

        nombre_fuente = mapa_fuente.get(
            referencia.get("fuente_referencia")
        )

        if nombre_fuente:
            valores_referencia = fuentes.get(
                nombre_fuente,
                [],
            )

        comparaciones = []

        for cotizacion in cotizaciones_im or []:
            comparacion = cls.comparar_cotizacion(
                precio_im=cotizacion.get(
                    "precio_unitario"
                ),
                cantidad=cotizacion.get(
                    "cantidad_ofertada"
                ),
                referencia=referencia,
                valores_referencia=valores_referencia,
                tendencia=tendencia,
            )

            comparaciones.append(
                {
                    **cotizacion,
                    **comparacion,
                }
            )

        resumen = cls.construir_resumen_cotizaciones_clave(
            comparaciones
        )

        precio_objetivo = cls.calcular_precio_objetivo(
            referencia
        )
        nivel_confianza = cls.calcular_nivel_confianza(
            referencia.get("total_observaciones")
        )

        return {
            "id_clave": clave_catalogo.get("id_clave"),
            "clave": clave_catalogo.get("clave"),
            "descripcion": clave_catalogo.get(
                "descripcion"
            ),
            "id_categoria": clave_catalogo.get(
                "id_categoria"
            ),
            "categoria": clave_catalogo.get("categoria"),
            "fuentes_mercado": fuentes,
            "estadisticas_fuentes": estadisticas_fuentes,
            "referencia": referencia,
            "precio_objetivo": precio_objetivo,
            "nivel_confianza": nivel_confianza,
            "tendencia": tendencia,
            "cotizaciones": comparaciones,
            "resumen": resumen,
        }

    # ==========================================================
    # CONSOLIDADO GENERAL
    # ==========================================================

    @classmethod
    def construir_resumen_general(
        cls,
        preparacion,
        resolucion,
        analisis_claves,
    ):
        """
        Construye indicadores generales sin promediar precios entre
        claves diferentes.
        """
        cotizaciones = [
            cotizacion
            for analisis in analisis_claves
            for cotizacion in analisis.get(
                "cotizaciones",
                [],
            )
        ]

        clasificaciones_competitivas = {
            cls.DESVIACION_MUY_COMPETITIVO,
            cls.DESVIACION_COMPETITIVO,
        }
        clasificaciones_elevadas = {
            cls.DESVIACION_LIGERAMENTE_ELEVADO,
            cls.DESVIACION_ELEVADO,
            cls.DESVIACION_MUY_ELEVADO,
        }

        return {
            "total_filas_recibidas": preparacion.get(
                "total_filas_recibidas",
                0,
            ),
            "total_filas_validas": len(
                preparacion.get("registros_validos", [])
            ),
            "total_filas_invalidas": len(
                preparacion.get("registros_invalidos", [])
            ),
            "total_claves_im": len(
                {
                    registro.get("clave")
                    for registro in preparacion.get(
                        "registros_validos",
                        [],
                    )
                    if registro.get("clave")
                }
            ),
            "claves_encontradas": len(analisis_claves),
            "claves_no_encontradas": len(
                {
                    registro.get("clave")
                    for registro in resolucion.get(
                        "claves_no_encontradas",
                        [],
                    )
                    if registro.get("clave")
                }
            ),
            "claves_con_referencia": sum(
                1
                for analisis in analisis_claves
                if analisis["referencia"][
                    "precio_referencia"
                ] is not None
            ),
            "claves_sin_referencia": sum(
                1
                for analisis in analisis_claves
                if analisis["referencia"][
                    "precio_referencia"
                ] is None
            ),
            "total_cotizaciones_analizadas": len(
                cotizaciones
            ),
            "cotizaciones_competitivas": sum(
                1
                for registro in cotizaciones
                if registro.get(
                    "clasificacion_desviacion"
                ) in clasificaciones_competitivas
            ),
            "cotizaciones_en_mercado": sum(
                1
                for registro in cotizaciones
                if registro.get(
                    "clasificacion_desviacion"
                ) == cls.DESVIACION_EN_MERCADO
            ),
            "cotizaciones_elevadas": sum(
                1
                for registro in cotizaciones
                if registro.get(
                    "clasificacion_desviacion"
                ) in clasificaciones_elevadas
            ),
            "cotizaciones_atipicas": sum(
                1
                for registro in cotizaciones
                if (
                    registro.get("evaluacion_atipico")
                    or {}
                ).get("es_valor_atipico")
            ),
            "claves_riesgo_alto": sum(
                1
                for analisis in analisis_claves
                if analisis["resumen"]["riesgo_clave"]
                == cls.RIESGO_ALTO
            ),
        }

    @staticmethod
    def construir_tablas_salida(analisis_claves):
        """
        Prepara tablas planas para Streamlit y exportación temporal.
        """
        comparacion_cotizaciones = []
        resumen_claves = []
        estadisticas_mercado = []
        recomendaciones = []

        for analisis in analisis_claves:
            resumen_claves.append(
                {
                    "id_clave": analisis["id_clave"],
                    "clave": analisis["clave"],
                    "descripcion": analisis["descripcion"],
                    "categoria": analisis["categoria"],
                    "precio_referencia": analisis[
                        "referencia"
                    ]["precio_referencia"],
                    "fuente_referencia": analisis[
                        "referencia"
                    ]["fuente_referencia"],
                    "nivel_confianza": analisis[
                        "nivel_confianza"
                    ],
                    "tendencia": analisis["tendencia"][
                        "tendencia"
                    ],
                    **analisis["resumen"],
                }
            )

            for nombre, estadisticas in analisis[
                "estadisticas_fuentes"
            ].items():
                estadisticas_mercado.append(
                    {
                        "id_clave": analisis["id_clave"],
                        "clave": analisis["clave"],
                        "fuente": nombre,
                        **estadisticas,
                    }
                )

            for cotizacion in analisis["cotizaciones"]:
                comparacion_cotizaciones.append(
                    {
                        "id_clave": analisis["id_clave"],
                        "clave": analisis["clave"],
                        "descripcion": analisis[
                            "descripcion"
                        ],
                        "categoria": analisis["categoria"],
                        **cotizacion,
                    }
                )

                for recomendacion in cotizacion.get(
                    "recomendaciones",
                    [],
                ):
                    recomendaciones.append(
                        {
                            "id_clave": analisis[
                                "id_clave"
                            ],
                            "clave": analisis["clave"],
                            "numero_fila": cotizacion.get(
                                "numero_fila"
                            ),
                            "rfc": cotizacion.get("rfc"),
                            "razon_social": cotizacion.get(
                                "razon_social"
                            ),
                            **recomendacion,
                        }
                    )

        return {
            "comparacion_cotizaciones": (
                comparacion_cotizaciones
            ),
            "resumen_claves": resumen_claves,
            "estadisticas_mercado": estadisticas_mercado,
            "recomendaciones": recomendaciones,
        }

    @staticmethod
    def construir_datos_graficas(analisis_claves):
        """
        Entrega series planas; la UI decide su representación.
        """
        evolucion = []
        distribucion = []
        clasificaciones = []
        riesgos = []

        for analisis in analisis_claves:
            for periodo in analisis["tendencia"]["serie"]:
                evolucion.append(
                    {
                        "id_clave": analisis["id_clave"],
                        "clave": analisis["clave"],
                        **periodo,
                    }
                )

            for fuente, valores in analisis[
                "fuentes_mercado"
            ].items():
                for precio in valores:
                    distribucion.append(
                        {
                            "id_clave": analisis[
                                "id_clave"
                            ],
                            "clave": analisis["clave"],
                            "fuente": fuente,
                            "precio": precio,
                        }
                    )

            for cotizacion in analisis["cotizaciones"]:
                clasificaciones.append(
                    {
                        "id_clave": analisis[
                            "id_clave"
                        ],
                        "clave": analisis["clave"],
                        "rfc": cotizacion.get("rfc"),
                        "razon_social": cotizacion.get(
                            "razon_social"
                        ),
                        "precio_im": cotizacion.get(
                            "precio_im"
                        ),
                        "clasificacion": cotizacion.get(
                            "clasificacion_desviacion"
                        ),
                    }
                )

            riesgos.append(
                {
                    "id_clave": analisis["id_clave"],
                    "clave": analisis["clave"],
                    "nivel_riesgo": analisis[
                        "resumen"
                    ]["riesgo_clave"],
                }
            )

        return {
            "evolucion_precios": evolucion,
            "distribucion_precios": distribucion,
            "clasificacion_cotizaciones": clasificaciones,
            "riesgo_por_clave": riesgos,
        }

    # ==========================================================
    # ORQUESTADOR PRINCIPAL
    # ==========================================================

    def comparar_investigacion(
        self,
        registros_im,
        conn=None,
    ):
        """
        Ejecuta la comparación completa de una nueva IM.

        Toda la información y los resultados permanecen en memoria.
        """
        preparacion = self.preparar_registros_im(
            registros_im
        )
        resolucion = self.resolver_claves_im(
            registros=preparacion["registros_validos"],
            conn=conn,
        )

        registros_resueltos = resolucion[
            "registros_resueltos"
        ]
        ids_clave = list(
            dict.fromkeys(
                registro["id_clave"]
                for registro in registros_resueltos
            )
        )

        contexto = (
            self.repository.obtener_contexto_comparacion(
                ids_clave=ids_clave,
                conn=conn,
            )
            if ids_clave
            else {
                "claves": [],
                "propuestas": [],
                "adjudicaciones_operativas": [],
                "adjudicaciones_historicas": [],
            }
        )

        contexto_por_clave = self.agrupar_contexto_por_clave(
            contexto
        )
        cotizaciones_por_clave = self._agrupar_por_id_clave(
            registros_resueltos
        )
        mapa_catalogo = {
            registro["id_clave"]: registro
            for registro in resolucion["claves_catalogo"]
        }

        analisis_claves = []

        for id_clave in ids_clave:
            clave_catalogo = mapa_catalogo.get(
                id_clave,
                contexto_por_clave.get(
                    id_clave,
                    {},
                ).get("clave", {}),
            )

            analisis_claves.append(
                self.construir_analisis_clave(
                    clave_catalogo=clave_catalogo,
                    cotizaciones_im=(
                        cotizaciones_por_clave.get(
                            id_clave,
                            [],
                        )
                    ),
                    contexto_clave=(
                        contexto_por_clave.get(
                            id_clave,
                            {},
                        )
                    ),
                )
            )

        resumen = self.construir_resumen_general(
            preparacion=preparacion,
            resolucion=resolucion,
            analisis_claves=analisis_claves,
        )
        tablas = self.construir_tablas_salida(
            analisis_claves
        )
        graficas = self.construir_datos_graficas(
            analisis_claves
        )

        return {
            "resumen": resumen,
            "incidencias": {
                "filas_invalidas": preparacion[
                    "registros_invalidos"
                ],
                "claves_no_encontradas": resolucion[
                    "claves_no_encontradas"
                ],
            },
            "claves": analisis_claves,
            "tablas": tablas,
            "graficas": graficas,
        }

    # ==========================================================
    # COMPARADOR POR PROCEDIMIENTO
    # ==========================================================

    TIPO_INICIAL = "INICIAL"
    TIPO_SUBASTA = "SUBASTA"
    RESULTADO_POSITIVA = "POSITIVA"

    ETAPA_ADJUDICACION = "ADJUDICACION"
    ETAPA_SUBASTA = "SUBASTA"
    ETAPA_VIABLE = "VIABLE"
    ETAPA_INICIAL = "INICIAL"
    ETAPA_SIN_PRECIO = "SIN_PRECIO"

    def obtener_procedimientos_disponibles(self, conn=None):
        """
        Devuelve los procedimientos disponibles para selección.
        """
        return self.repository.obtener_procedimientos_disponibles(
            conn=conn
        )

    @classmethod
    def construir_etapas_procedimiento(
        cls,
        propuestas,
        adjudicaciones,
    ):
        """
        Construye los precios representativos del procedimiento
        seleccionado por clave.

        Reglas:
        - Inicial: menor propuesta INICIAL.
        - Viable: menor propuesta INICIAL con evaluación POSITIVA.
        - Subasta: menor propuesta SUBASTA.
        - Adjudicación: precio ponderado por cantidad cuando existen
          varias adjudicaciones; si no es posible, usa la mediana.
        """
        propuestas = propuestas or []
        adjudicaciones = adjudicaciones or []

        iniciales = []
        viables = []
        subastas = []

        for registro in propuestas:
            if not isinstance(registro, dict):
                continue

            tipo = str(
                registro.get("tipo_propuesta") or ""
            ).strip().upper()
            precio = cls._decimal(
                registro.get("precio_unitario")
            )

            if precio is None or precio <= cls.CERO:
                continue

            if tipo == cls.TIPO_INICIAL:
                iniciales.append(precio)

                resultado = str(
                    registro.get("resultado_tecnico") or ""
                ).strip().upper()

                if resultado == cls.RESULTADO_POSITIVA:
                    viables.append(precio)

            elif tipo == cls.TIPO_SUBASTA:
                subastas.append(precio)

        precios_adjudicados = cls.extraer_precios_validos(
            adjudicaciones,
            campo_precio="precio_unitario_adjudicado",
        )

        precio_adjudicado = None

        if adjudicaciones:
            suma_importes = cls.CERO
            suma_cantidades = cls.CERO

            for registro in adjudicaciones:
                if not isinstance(registro, dict):
                    continue

                precio = cls._decimal(
                    registro.get(
                        "precio_unitario_adjudicado"
                    )
                )
                cantidad = cls._decimal(
                    registro.get("cantidad_adjudicada")
                )

                if (
                    precio is None
                    or cantidad is None
                    or precio <= cls.CERO
                    or cantidad <= cls.CERO
                ):
                    continue

                suma_importes += precio * cantidad
                suma_cantidades += cantidad

            if suma_cantidades > cls.CERO:
                precio_adjudicado = (
                    suma_importes / suma_cantidades
                )

        if precio_adjudicado is None and precios_adjudicados:
            precio_adjudicado = cls.calcular_mediana(
                precios_adjudicados
            )

        return {
            "mejor_precio_inicial": (
                cls.redondear_precio(min(iniciales))
                if iniciales
                else None
            ),
            "mejor_precio_viable": (
                cls.redondear_precio(min(viables))
                if viables
                else None
            ),
            "mejor_precio_subasta": (
                cls.redondear_precio(min(subastas))
                if subastas
                else None
            ),
            "precio_adjudicado": cls.redondear_precio(
                precio_adjudicado
            ),
            "total_propuestas_iniciales": len(iniciales),
            "total_propuestas_viables": len(viables),
            "total_subastas": len(subastas),
            "total_adjudicaciones": len(
                precios_adjudicados
            ),
        }

    @classmethod
    def seleccionar_precio_actual_procedimiento(
        cls,
        etapas,
    ):
        """
        Selecciona la etapa más avanzada disponible para comparar
        el procedimiento contra el mercado.
        """
        etapas = etapas or {}

        prioridades = (
            (
                cls.ETAPA_ADJUDICACION,
                etapas.get("precio_adjudicado"),
            ),
            (
                cls.ETAPA_SUBASTA,
                etapas.get("mejor_precio_subasta"),
            ),
            (
                cls.ETAPA_VIABLE,
                etapas.get("mejor_precio_viable"),
            ),
            (
                cls.ETAPA_INICIAL,
                etapas.get("mejor_precio_inicial"),
            ),
        )

        for etapa, precio in prioridades:
            precio_decimal = cls._decimal(precio)

            if (
                precio_decimal is not None
                and precio_decimal > cls.CERO
            ):
                return {
                    "etapa_actual": etapa,
                    "precio_actual": cls.redondear_precio(
                        precio_decimal
                    ),
                }

        return {
            "etapa_actual": cls.ETAPA_SIN_PRECIO,
            "precio_actual": None,
        }

    @classmethod
    def construir_referencia_mercado_procedimiento(
        cls,
        mercado_operativo,
        mercado_historico,
    ):
        """
        Construye la referencia externa del procedimiento.

        Se conservan separadas:
        - adjudicaciones de otros procedimientos;
        - adjudicaciones históricas.

        La referencia consolidada usa ambas fuentes.
        """
        precios_operativos = cls.extraer_precios_validos(
            mercado_operativo,
            campo_precio="precio_unitario_adjudicado",
        )
        precios_historicos = cls.extraer_precios_validos(
            mercado_historico,
            campo_precio="precio_unitario_adjudicado",
        )
        precios_consolidados = (
            precios_operativos + precios_historicos
        )

        fuentes = {
            "mercado_operativo": precios_operativos,
            "mercado_historico": precios_historicos,
            "mercado_consolidado": precios_consolidados,
        }

        estadisticas = cls.calcular_estadisticas_fuentes(
            fuentes
        )

        referencia = {
            "precio_referencia": (
                estadisticas["mercado_consolidado"][
                    "precio_mediana"
                ]
            ),
            "fuente_referencia": (
                "MERCADO_OPERATIVO_E_HISTORICO"
                if precios_consolidados
                else cls.FUENTE_SIN_REFERENCIA
            ),
            "total_observaciones": (
                estadisticas["mercado_consolidado"][
                    "total_observaciones"
                ]
            ),
            "estadisticas_referencia": (
                estadisticas["mercado_consolidado"]
            ),
        }

        return {
            "fuentes": fuentes,
            "estadisticas": estadisticas,
            "referencia": referencia,
        }

    @classmethod
    def construir_analisis_procedimiento_clave(
        cls,
        universo_clave,
        propuestas,
        adjudicaciones_procedimiento,
        mercado_operativo,
        mercado_historico,
    ):
        """
        Analiza una clave del procedimiento seleccionado contra el
        mercado externo operativo e histórico.
        """
        etapas = cls.construir_etapas_procedimiento(
            propuestas=propuestas,
            adjudicaciones=adjudicaciones_procedimiento,
        )
        precio_actual = (
            cls.seleccionar_precio_actual_procedimiento(
                etapas
            )
        )
        mercado = (
            cls.construir_referencia_mercado_procedimiento(
                mercado_operativo=mercado_operativo,
                mercado_historico=mercado_historico,
            )
        )

        tendencia = cls.calcular_tendencia(
            (mercado_operativo or [])
            + (mercado_historico or [])
        )

        comparacion = cls.comparar_cotizacion(
            precio_im=precio_actual["precio_actual"],
            cantidad=universo_clave.get(
                "cantidad_requerida"
            ),
            referencia=mercado["referencia"],
            valores_referencia=mercado["fuentes"][
                "mercado_consolidado"
            ],
            tendencia=tendencia,
        )

        return {
            "id_clave": universo_clave.get("id_clave"),
            "clave": universo_clave.get("clave"),
            "descripcion": universo_clave.get(
                "descripcion"
            ),
            "id_categoria": universo_clave.get(
                "id_categoria"
            ),
            "categoria": universo_clave.get("categoria"),
            "cantidad_requerida": universo_clave.get(
                "cantidad_requerida"
            ),
            "etapas_procedimiento": etapas,
            "etapa_actual": precio_actual["etapa_actual"],
            "precio_actual": precio_actual["precio_actual"],
            "mercado_operativo": mercado_operativo or [],
            "mercado_historico": mercado_historico or [],
            "estadisticas_mercado": mercado["estadisticas"],
            "referencia": mercado["referencia"],
            "tendencia": tendencia,
            "comparacion": comparacion,
            "nivel_confianza": comparacion[
                "nivel_confianza"
            ],
            "nivel_riesgo": comparacion["nivel_riesgo"],
            "recomendaciones": comparacion[
                "recomendaciones"
            ],
        }

    @classmethod
    def construir_resumen_procedimiento(
        cls,
        procedimiento,
        analisis_claves,
    ):
        """
        Construye indicadores generales del procedimiento.
        """
        analisis_claves = analisis_claves or []

        return {
            "id_procedimiento": procedimiento.get(
                "id_procedimiento"
            ),
            "numero_procedimiento": procedimiento.get(
                "numero_procedimiento"
            ),
            "descripcion": procedimiento.get("descripcion"),
            "ejercicio": procedimiento.get("ejercicio"),
            "total_claves": len(analisis_claves),
            "claves_con_precio_actual": sum(
                1
                for item in analisis_claves
                if item["precio_actual"] is not None
            ),
            "claves_sin_precio_actual": sum(
                1
                for item in analisis_claves
                if item["precio_actual"] is None
            ),
            "claves_con_referencia": sum(
                1
                for item in analisis_claves
                if item["referencia"][
                    "precio_referencia"
                ] is not None
            ),
            "claves_sin_referencia": sum(
                1
                for item in analisis_claves
                if item["referencia"][
                    "precio_referencia"
                ] is None
            ),
            "claves_competitivas": sum(
                1
                for item in analisis_claves
                if item["comparacion"][
                    "clasificacion_desviacion"
                ]
                in {
                    cls.DESVIACION_MUY_COMPETITIVO,
                    cls.DESVIACION_COMPETITIVO,
                }
            ),
            "claves_en_mercado": sum(
                1
                for item in analisis_claves
                if item["comparacion"][
                    "clasificacion_desviacion"
                ] == cls.DESVIACION_EN_MERCADO
            ),
            "claves_elevadas": sum(
                1
                for item in analisis_claves
                if item["comparacion"][
                    "clasificacion_desviacion"
                ]
                in {
                    cls.DESVIACION_LIGERAMENTE_ELEVADO,
                    cls.DESVIACION_ELEVADO,
                    cls.DESVIACION_MUY_ELEVADO,
                }
            ),
            "claves_riesgo_alto": sum(
                1
                for item in analisis_claves
                if item["nivel_riesgo"]
                == cls.RIESGO_ALTO
            ),
            "claves_con_historico": sum(
                1
                for item in analisis_claves
                if item["mercado_historico"]
            ),
        }

    @staticmethod
    def construir_tablas_procedimiento(
        procedimiento,
        analisis_claves,
    ):
        """
        Prepara tablas planas para Streamlit.
        """
        resumen_claves = []
        etapas = []
        recomendaciones = []
        evolucion = []
        distribucion = []

        for item in analisis_claves or []:
            comparacion = item["comparacion"]
            referencia = item["referencia"]

            resumen_claves.append(
                {
                    "id_procedimiento": procedimiento.get(
                        "id_procedimiento"
                    ),
                    "numero_procedimiento": procedimiento.get(
                        "numero_procedimiento"
                    ),
                    "id_clave": item["id_clave"],
                    "clave": item["clave"],
                    "descripcion": item["descripcion"],
                    "categoria": item["categoria"],
                    "etapa_actual": item["etapa_actual"],
                    "precio_actual": item["precio_actual"],
                    "precio_referencia": referencia[
                        "precio_referencia"
                    ],
                    "total_observaciones": referencia[
                        "total_observaciones"
                    ],
                    "variacion_porcentual": comparacion[
                        "variacion_porcentual"
                    ],
                    "clasificacion": comparacion[
                        "clasificacion_desviacion"
                    ],
                    "tendencia": item["tendencia"][
                        "tendencia"
                    ],
                    "confianza": item["nivel_confianza"],
                    "riesgo": item["nivel_riesgo"],
                }
            )

            etapas.append(
                {
                    "id_clave": item["id_clave"],
                    "clave": item["clave"],
                    **item["etapas_procedimiento"],
                }
            )

            for recomendacion in item["recomendaciones"]:
                recomendaciones.append(
                    {
                        "id_clave": item["id_clave"],
                        "clave": item["clave"],
                        **recomendacion,
                    }
                )

            for periodo in item["tendencia"]["serie"]:
                evolucion.append(
                    {
                        "id_clave": item["id_clave"],
                        "clave": item["clave"],
                        **periodo,
                    }
                )

            for fuente, valores in item[
                "estadisticas_mercado"
            ].items():
                if fuente == "mercado_consolidado":
                    continue

                precios = (
                    item["mercado_operativo"]
                    if fuente == "mercado_operativo"
                    else item["mercado_historico"]
                )

                for registro in precios:
                    distribucion.append(
                        {
                            "id_clave": item["id_clave"],
                            "clave": item["clave"],
                            "fuente": fuente,
                            "precio": registro.get(
                                "precio_unitario_adjudicado"
                            ),
                        }
                    )

        return {
            "resumen_claves": resumen_claves,
            "etapas_procedimiento": etapas,
            "recomendaciones": recomendaciones,
            "evolucion_precios": evolucion,
            "distribucion_mercado": distribucion,
        }

    def comparar_procedimiento(
        self,
        id_procedimiento,
        conn=None,
    ):
        """
        Ejecuta el análisis inteligente del procedimiento contra
        otros procedimientos operativos y el histórico.
        """
        contexto = (
            self.repository.obtener_contexto_procedimiento(
                id_procedimiento=id_procedimiento,
                conn=conn,
            )
        )

        if contexto is None:
            raise ValueError(
                "El procedimiento seleccionado no existe."
            )

        procedimiento = contexto["procedimiento"]
        universo = contexto.get("universo", [])

        propuestas_por_clave = self._agrupar_por_id_clave(
            contexto.get("propuestas_procedimiento", [])
        )
        adjudicaciones_por_clave = (
            self._agrupar_por_id_clave(
                contexto.get(
                    "adjudicaciones_procedimiento",
                    [],
                )
            )
        )
        operativo_por_clave = self._agrupar_por_id_clave(
            contexto.get("mercado_operativo", [])
        )
        historico_por_clave = self._agrupar_por_id_clave(
            contexto.get("mercado_historico", [])
        )

        analisis_claves = []

        for clave in universo:
            id_clave = clave["id_clave"]

            analisis_claves.append(
                self.construir_analisis_procedimiento_clave(
                    universo_clave=clave,
                    propuestas=propuestas_por_clave.get(
                        id_clave,
                        [],
                    ),
                    adjudicaciones_procedimiento=(
                        adjudicaciones_por_clave.get(
                            id_clave,
                            [],
                        )
                    ),
                    mercado_operativo=operativo_por_clave.get(
                        id_clave,
                        [],
                    ),
                    mercado_historico=historico_por_clave.get(
                        id_clave,
                        [],
                    ),
                )
            )

        resumen = self.construir_resumen_procedimiento(
            procedimiento=procedimiento,
            analisis_claves=analisis_claves,
        )
        tablas = self.construir_tablas_procedimiento(
            procedimiento=procedimiento,
            analisis_claves=analisis_claves,
        )

        return {
            "procedimiento": procedimiento,
            "resumen": resumen,
            "claves": analisis_claves,
            "tablas": tablas,
        }
