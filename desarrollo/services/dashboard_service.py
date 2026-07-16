"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

dashboard_service.py

Servicio analítico para el Dashboard Ejecutivo.

Responsabilidades:
- Coordinar las consultas de DashboardRepository.
- Calcular porcentajes derivados.
- Clasificar el nivel de competencia.
- Clasificar el estado analítico de cada clave.
- Calcular ahorro unitario y porcentual por subasta.
- Construir una respuesta única para la interfaz Streamlit.

Este Service:
- No ejecuta SQL.
- No abre conexiones.
- No contiene componentes de Streamlit.
- No modifica información en la base de datos.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Servicio de reglas analíticas para el Dashboard Ejecutivo."""

    ESTADO_DESIERTA = "DESIERTA"
    ESTADO_CON_OFERTAS = "CON OFERTAS"
    ESTADO_SIN_APROBACION = "SIN APROBACIÓN TÉCNICA"
    ESTADO_APROBADOS_SIN_ADJUDICACION = (
        "CON APROBADOS SIN ADJUDICACIÓN"
    )
    ESTADO_ADJUDICADA = "ADJUDICADA"

    NIVEL_SIN_PARTICIPACION = "SIN PARTICIPACIÓN"
    NIVEL_COMPETENCIA_NULA = "COMPETENCIA NULA"
    NIVEL_COMPETENCIA_BAJA = "COMPETENCIA BAJA"
    NIVEL_COMPETENCIA_MEDIA = "COMPETENCIA MEDIA"
    NIVEL_COMPETENCIA_ALTA = "COMPETENCIA ALTA"

    def __init__(self, repository=None):
        self.repository = repository or DashboardRepository()

    # ==========================================================
    # UTILIDADES NUMÉRICAS
    # ==========================================================

    @staticmethod
    def _decimal(valor, default="0"):
        """Convierte un valor numérico a Decimal de forma controlada."""
        if valor is None:
            return Decimal(default)

        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal(default)

    @classmethod
    def calcular_porcentaje(
        cls,
        numerador,
        denominador,
        decimales=2,
    ):
        """
        Calcula un porcentaje sin producir división entre cero.

        Devuelve Decimal para mantener precisión en reglas analíticas.
        """
        numero = cls._decimal(numerador)
        total = cls._decimal(denominador)

        if total <= 0:
            return Decimal("0")

        cuantizador = Decimal("1").scaleb(-decimales)

        return (
            (numero / total) * Decimal("100")
        ).quantize(
            cuantizador,
            rounding=ROUND_HALF_UP,
        )

    # ==========================================================
    # COMPETENCIA
    # ==========================================================

    @classmethod
    def clasificar_competencia_clave(cls, total_proveedores):
        """Clasifica la competencia de una clave."""
        total = int(total_proveedores or 0)

        if total <= 0:
            return cls.NIVEL_SIN_PARTICIPACION
        if total == 1:
            return cls.NIVEL_COMPETENCIA_NULA
        if total == 2:
            return cls.NIVEL_COMPETENCIA_BAJA
        if total <= 4:
            return cls.NIVEL_COMPETENCIA_MEDIA
        return cls.NIVEL_COMPETENCIA_ALTA

    @staticmethod
    def puntuacion_competencia(total_proveedores):
        """Convierte proveedores por clave en una puntuación de 0 a 4."""
        total = int(total_proveedores or 0)

        if total <= 0:
            return 0
        if total == 1:
            return 1
        if total == 2:
            return 2
        if total <= 4:
            return 3
        return 4

    @classmethod
    def clasificar_promedio_competencia(cls, puntuacion_promedio):
        """Convierte la puntuación promedio en nivel general."""
        promedio = cls._decimal(puntuacion_promedio)

        if promedio < Decimal("0.50"):
            return cls.NIVEL_SIN_PARTICIPACION
        if promedio < Decimal("1.50"):
            return cls.NIVEL_COMPETENCIA_NULA
        if promedio < Decimal("2.50"):
            return cls.NIVEL_COMPETENCIA_BAJA
        if promedio < Decimal("3.50"):
            return cls.NIVEL_COMPETENCIA_MEDIA
        return cls.NIVEL_COMPETENCIA_ALTA

    @classmethod
    def procesar_competencia_por_clave(cls, registros):
        """
        Agrega clasificación y puntuación a cada clave.

        Las claves sin propuestas permanecen en el resultado.
        """
        resultado = []

        for registro in registros or []:
            item = dict(registro)
            total = int(item.get("total_proveedores") or 0)

            item["total_proveedores"] = total
            item["nivel_competencia"] = (
                cls.clasificar_competencia_clave(total)
            )
            item["puntuacion_competencia"] = (
                cls.puntuacion_competencia(total)
            )
            resultado.append(item)

        return resultado

    @classmethod
    def calcular_resumen_competencia(cls, registros):
        """Calcula promedios generales usando todas las claves."""
        competencia = cls.procesar_competencia_por_clave(registros)

        if not competencia:
            return {
                "total_claves": 0,
                "promedio_proveedores_por_clave": Decimal("0"),
                "puntuacion_promedio_competencia": Decimal("0"),
                "nivel_competencia": cls.NIVEL_SIN_PARTICIPACION,
            }

        total_claves = len(competencia)
        suma_proveedores = sum(
            item["total_proveedores"]
            for item in competencia
        )
        suma_puntuaciones = sum(
            item["puntuacion_competencia"]
            for item in competencia
        )

        promedio_proveedores = (
            Decimal(suma_proveedores) / Decimal(total_claves)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        promedio_puntuacion = (
            Decimal(suma_puntuaciones) / Decimal(total_claves)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        return {
            "total_claves": total_claves,
            "promedio_proveedores_por_clave": promedio_proveedores,
            "puntuacion_promedio_competencia": promedio_puntuacion,
            "nivel_competencia": (
                cls.clasificar_promedio_competencia(
                    promedio_puntuacion
                )
            ),
        }

    # ==========================================================
    # ESTADO ANALÍTICO DE CLAVES
    # ==========================================================

    @classmethod
    def clasificar_estado_clave(cls, registro):
        """
        Clasifica una clave conforme al flujo analítico aprobado.

        Prioridad:
        1. Adjudicada.
        2. Desierta: no recibió oferta inicial.
        3. Sin aprobación técnica.
        4. Con aprobados sin adjudicación.
        5. Con ofertas.
        """
        proveedores = int(
            registro.get("proveedores_oferta_inicial") or 0
        )
        positivas = int(
            registro.get("evaluaciones_positivas") or 0
        )
        tiene_adjudicacion = bool(
            registro.get("tiene_adjudicacion")
        )

        if tiene_adjudicacion:
            return cls.ESTADO_ADJUDICADA

        if proveedores == 0:
            return cls.ESTADO_DESIERTA

        if positivas == 0:
            return cls.ESTADO_SIN_APROBACION

        if positivas > 0:
            return cls.ESTADO_APROBADOS_SIN_ADJUDICACION

        return cls.ESTADO_CON_OFERTAS

    @classmethod
    def procesar_estado_claves(cls, registros):
        """Agrega el estado analítico a los registros de claves."""
        resultado = []

        for registro in registros or []:
            item = dict(registro)
            item["estado_analitico"] = (
                cls.clasificar_estado_clave(item)
            )
            resultado.append(item)

        return resultado

    # ==========================================================
    # APROBACIÓN TÉCNICA POR PROVEEDOR
    # ==========================================================

    @classmethod
    def procesar_aprobacion_proveedores(cls, registros):
        """
        Calcula el porcentaje de aprobación técnica por proveedor.

        Distingue entre:
        - Proveedor evaluado con 0 %.
        - Proveedor sin evaluaciones.
        """
        resultado = []

        for registro in registros or []:
            item = dict(registro)
            total = int(item.get("total_evaluaciones") or 0)
            positivas = int(
                item.get("evaluaciones_positivas") or 0
            )
            negativas = int(
                item.get("evaluaciones_negativas") or 0
            )

            item["total_evaluaciones"] = total
            item["evaluaciones_positivas"] = positivas
            item["evaluaciones_negativas"] = negativas

            if total == 0:
                item["porcentaje_aprobacion"] = None
                item["estado_aprobacion"] = "SIN EVALUACIONES"
            else:
                item["porcentaje_aprobacion"] = (
                    cls.calcular_porcentaje(
                        positivas,
                        total,
                    )
                )
                item["estado_aprobacion"] = "EVALUADO"

            resultado.append(item)

        return resultado

    # ==========================================================
    # PRECIOS Y AHORRO POR SUBASTA
    # ==========================================================

    @classmethod
    def procesar_precios_por_clave(cls, registros):
        """
        Calcula ahorro unitario y porcentual por clave.

        El cálculo solo se realiza cuando existen:
        - Mejor precio viable inicial.
        - Mejor precio de subasta.
        """
        resultado = []

        for registro in registros or []:
            item = dict(registro)

            inicial = item.get("mejor_precio_inicial")
            viable = item.get("mejor_precio_viable")
            subasta = item.get("mejor_precio_subasta")

            item["mejor_precio_inicial"] = (
                None if inicial is None else cls._decimal(inicial)
            )
            item["mejor_precio_viable"] = (
                None if viable is None else cls._decimal(viable)
            )
            item["mejor_precio_subasta"] = (
                None if subasta is None else cls._decimal(subasta)
            )

            if viable is None or subasta is None:
                item["ahorro_unitario_subasta"] = None
                item["ahorro_porcentual_subasta"] = None
                item["estado_ahorro_subasta"] = (
                    "INFORMACIÓN INSUFICIENTE"
                )
                resultado.append(item)
                continue

            precio_viable = cls._decimal(viable)
            precio_subasta = cls._decimal(subasta)
            ahorro_unitario = (
                precio_viable - precio_subasta
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            item["ahorro_unitario_subasta"] = ahorro_unitario

            if precio_viable <= 0:
                item["ahorro_porcentual_subasta"] = None
                item["estado_ahorro_subasta"] = (
                    "PRECIO VIABLE INVÁLIDO"
                )
            else:
                item["ahorro_porcentual_subasta"] = (
                    cls.calcular_porcentaje(
                        ahorro_unitario,
                        precio_viable,
                    )
                )

                if ahorro_unitario > 0:
                    item["estado_ahorro_subasta"] = "AHORRO"
                elif ahorro_unitario < 0:
                    item["estado_ahorro_subasta"] = (
                        "INCREMENTO DE PRECIO"
                    )
                else:
                    item["estado_ahorro_subasta"] = "SIN VARIACIÓN"

            resultado.append(item)

        return resultado

    # ==========================================================
    # INDICADORES Y TABLAS
    # ==========================================================

    @classmethod
    def completar_indicadores(
        cls,
        indicadores,
        resumen_competencia,
    ):
        """Completa los indicadores derivados del Dashboard."""
        resultado = dict(indicadores or {})

        total_claves = int(resultado.get("total_claves") or 0)
        adjudicadas = int(
            resultado.get("total_claves_adjudicadas") or 0
        )

        resultado["porcentaje_claves_adjudicadas"] = (
            cls.calcular_porcentaje(
                adjudicadas,
                total_claves,
            )
        )
        resultado["promedio_proveedores_por_clave"] = (
            resumen_competencia[
                "promedio_proveedores_por_clave"
            ]
        )
        resultado["nivel_competencia"] = (
            resumen_competencia["nivel_competencia"]
        )
        resultado["puntuacion_promedio_competencia"] = (
            resumen_competencia[
                "puntuacion_promedio_competencia"
            ]
        )

        return resultado

    def obtener_dashboard(
        self,
        id_procedimiento=None,
        ejercicio=None,
        id_clave=None,
        conn=None,
    ):
        """
        Construye la respuesta completa consumida por Streamlit.

        La misma conexión opcional se transmite a todas las consultas.
        """
        indicadores_base = (
            self.repository.obtener_indicadores_principales(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or {}
        )

        competencia_base = (
            self.repository.obtener_competencia_por_clave(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )
        competencia_claves = (
            self.procesar_competencia_por_clave(
                competencia_base
            )
        )
        resumen_competencia = (
            self.calcular_resumen_competencia(
                competencia_base
            )
        )

        estado_claves = self.procesar_estado_claves(
            self.repository.obtener_estado_claves(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        aprobacion_proveedores = (
            self.procesar_aprobacion_proveedores(
                self.repository.obtener_aprobacion_por_proveedor(
                    id_procedimiento=id_procedimiento,
                    ejercicio=ejercicio,
                    conn=conn,
                )
                or []
            )
        )

        participacion_proveedores = (
            self.repository.obtener_participacion_proveedores(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        precios_claves = self.procesar_precios_por_clave(
            self.repository.obtener_precios_por_clave(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                id_clave=id_clave,
                conn=conn,
            )
            or []
        )

        resumen_procedimientos = (
            self.repository
            .obtener_resumen_competencia_procedimientos(
                id_procedimiento=id_procedimiento,
                ejercicio=ejercicio,
                conn=conn,
            )
            or []
        )

        indicadores = self.completar_indicadores(
            indicadores_base,
            resumen_competencia,
        )

        return {
            "filtros": {
                "id_procedimiento": id_procedimiento,
                "ejercicio": ejercicio,
                "id_clave": id_clave,
            },
            "indicadores": indicadores,
            "graficas": {
                "competencia_claves": competencia_claves,
                "aprobacion_proveedores": aprobacion_proveedores,
                "precios_claves": precios_claves,
            },
            "tablas": {
                "resumen_procedimientos": (
                    resumen_procedimientos
                ),
                "estado_claves": estado_claves,
                "participacion_proveedores": (
                    participacion_proveedores
                ),
                "aprobacion_proveedores": (
                    aprobacion_proveedores
                ),
                "precios_claves": precios_claves,
            },
        }

    def obtener_catalogos_filtros(self, conn=None):
        """Obtiene catálogos necesarios para construir los filtros."""
        return {
            "procedimientos": (
                self.repository.obtener_procedimientos_filtro(
                    conn=conn
                )
                or []
            ),
            "ejercicios": (
                self.repository.obtener_ejercicios_filtro(
                    conn=conn
                )
                or []
            ),
        }