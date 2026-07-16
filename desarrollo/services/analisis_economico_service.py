"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

analisis_economico_service.py

Servicio transversal de utilidades y reglas económicas.

Responsabilidades:
- Convertir valores numéricos de forma segura.
- Redondear precios y porcentajes.
- Calcular porcentajes y variaciones entre precios.
- Clasificar variaciones económicas.
- Calcular precios ponderados.
- Calcular importes y ahorros estimados.

Este Service:
- No ejecuta SQL.
- No utiliza Repositories.
- No abre conexiones.
- No administra transacciones.
- No contiene componentes de Streamlit.
- Puede ser reutilizado por cualquier módulo analítico.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class AnalisisEconomicoService:
    """Reglas económicas compartidas por los módulos analíticos."""

    CLASIFICACION_AHORRO = "AHORRO"
    CLASIFICACION_SIN_CAMBIO = "SIN CAMBIO"
    CLASIFICACION_INCREMENTO = "INCREMENTO"
    CLASIFICACION_INSUFICIENTE = "INFORMACIÓN INSUFICIENTE"

    CUANTIZADOR_PRECIO = Decimal("0.01")
    CUANTIZADOR_PORCENTAJE = Decimal("0.01")
    CUANTIZADOR_CANTIDAD = Decimal("0.01")
    CERO = Decimal("0")

    @classmethod
    def _decimal(cls, valor, default=None):
        """Convierte un valor a Decimal sin propagar errores."""
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
        """Redondea un precio o importe a dos decimales."""
        numero = cls._decimal(valor)
        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def redondear_porcentaje(cls, valor):
        """Redondea un porcentaje a dos decimales."""
        numero = cls._decimal(valor)
        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_PORCENTAJE,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def redondear_cantidad(cls, valor):
        """Redondea una cantidad a dos decimales."""
        numero = cls._decimal(valor)
        if numero is None:
            return None

        return numero.quantize(
            cls.CUANTIZADOR_CANTIDAD,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_porcentaje(cls, numerador, denominador):
        """Calcula numerador / denominador * 100."""
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
        """
        origen = cls._decimal(precio_origen)
        destino = cls._decimal(precio_destino)

        if origen is None or destino is None or origen <= cls.CERO:
            return None

        return (
            ((destino - origen) / origen) * Decimal("100")
        ).quantize(
            cls.CUANTIZADOR_PORCENTAJE,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def clasificar_variacion(cls, variacion):
        """Clasifica una variación como ahorro, incremento o sin cambio."""
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
        """Calcula valor total adjudicado / cantidad total adjudicada."""
        cantidad = cls._decimal(cantidad_total_adjudicada)
        valor = cls._decimal(valor_total_adjudicado)

        if cantidad is None or valor is None or cantidad <= cls.CERO:
            return None

        return (valor / cantidad).quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_importe(cls, precio_unitario, cantidad):
        """Calcula precio unitario por cantidad."""
        precio = cls._decimal(precio_unitario)
        cantidad_decimal = cls._decimal(cantidad)

        if precio is None or cantidad_decimal is None:
            return None

        if precio < cls.CERO or cantidad_decimal < cls.CERO:
            return None

        return (precio * cantidad_decimal).quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_ahorro_unitario(cls, precio_inicial, precio_destino):
        """Calcula precio inicial menos precio destino."""
        inicial = cls._decimal(precio_inicial)
        destino = cls._decimal(precio_destino)

        if inicial is None or destino is None:
            return None

        return (inicial - destino).quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def calcular_ahorro_estimado(
        cls,
        precio_inicial,
        precio_destino,
        cantidad_referencia,
    ):
        """Calcula (precio inicial - precio destino) por cantidad."""
        ahorro_unitario = cls.calcular_ahorro_unitario(
            precio_inicial,
            precio_destino,
        )
        cantidad = cls._decimal(cantidad_referencia)

        if ahorro_unitario is None or cantidad is None or cantidad < cls.CERO:
            return None

        return (ahorro_unitario * cantidad).quantize(
            cls.CUANTIZADOR_PRECIO,
            rounding=ROUND_HALF_UP,
        )