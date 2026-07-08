# MODELO DE NEGOCIO

# SIMI

## Sistema Inteligente de Mercado e Investigaciones

Versión del documento: 1.0

Release del sistema: 0.2.0 (Desarrollo)

---

# Objetivo

SIMI no es únicamente un comparador de investigaciones de mercado.

SIMI es una plataforma de Inteligencia de Mercado diseñada para analizar el ciclo completo de un procedimiento de contratación pública, desde la invitación de claves hasta la adjudicación final, generando indicadores, diagnósticos y recomendaciones para apoyar la toma de decisiones.

---

# Filosofía del sistema

Los archivos Excel no representan el sistema.

Los archivos Excel únicamente son el medio de captura de información.

El verdadero valor de SIMI se encuentra en la información estructurada, los indicadores obtenidos y la inteligencia generada a partir de ellos.

---

# Objetivos principales

SIMI deberá permitir responder preguntas como:

- ¿Qué proveedor ofrece el mejor precio?
- ¿Qué proveedor participa más?
- ¿Qué proveedor gana más adjudicaciones?
- ¿Qué claves presentan mayor variación?
- ¿Qué investigaciones tienen menor competencia?
- ¿Qué claves quedaron desiertas?
- ¿Qué claves presentan riesgo de desabasto?
- ¿Qué claves dejaron de comercializarse?
- ¿Qué investigaciones muestran sobreprecio?
- ¿Cuál sería el ahorro potencial?

---

# Entidades principales

## Investigación

Es la entidad principal del sistema.

Representa un procedimiento de investigación de mercado.

Toda la información de SIMI deberá pertenecer a una investigación.

Una investigación podrá contener:

- Invitaciones
- Ofertas
- Claves
- Proveedores
- Adjudicaciones
- Indicadores
- Insights

---

## Invitación

La invitación define el universo esperado de productos.

No contiene ofertas.

Contiene únicamente las claves que fueron solicitadas.

Campos principales

- Investigación
- Clave
- Descripción
- Cantidad requerida

Una invitación permitirá conocer:

- Total de claves solicitadas
- Claves ofertadas
- Claves desiertas
- Porcentaje de respuesta
- Nivel de competencia

---

## Oferta

Una oferta representa la participación de un proveedor.

Cada oferta pertenece a:

- Una investigación
- Un proveedor
- Una clave

Campos principales

- RFC
- Razón Social
- Clave
- Descripción
- Cantidad ofertada
- País de origen
- Precio unitario

---

## Proveedor

El proveedor representa al participante del mercado.

Su identificador principal será siempre el RFC.

La razón social únicamente será un dato descriptivo.

SIMI deberá unificar automáticamente proveedores mediante RFC.

---

## Clave

La clave representa un producto, medicamento o insumo.

La clave tendrá un comportamiento histórico independiente de las investigaciones.

Será una de las entidades más importantes del sistema.

---

## Adjudicación

Representa el resultado final del procedimiento.

Será desarrollada en una versión posterior.

Permitirá conocer:

- Proveedor ganador
- Cantidad adjudicada
- Precio adjudicado
- Monto adjudicado

---

## Indicador

Resultado numérico obtenido por Analytics.

Ejemplos

- Precio promedio
- Variación
- Ranking
- Participaciones
- Porcentaje de competencia

---

## Insight

Conclusión generada por el Motor de Inteligencia.

Ejemplo

"La clave presenta alta volatilidad."

"No se recomienda utilizar el último precio como referencia."

---

# Reglas del negocio

---

## Regla 1

Los archivos Excel no representan el sistema.

Son únicamente un mecanismo de importación.

Toda la información deberá almacenarse posteriormente en una base de datos.

---

## Regla 2

La investigación es la entidad principal.

Todo registro debe pertenecer a una investigación.

---

## Regla 3

El RFC identifica al proveedor.

La razón social podrá variar.

Ejemplo

JAYOR SA DE CV

JAYOR S.A. DE C.V.

Jayor S.A. de C.V.

Todos representan al mismo proveedor si el RFC coincide.

---

## Regla 4

La invitación define las claves esperadas.

Las ofertas representan las claves recibidas.

---

## Regla 5

Una clave puede encontrarse en alguno de los siguientes estados

- Invitada
- Ofertada
- Desierta
- Adjudicada
- No adjudicada

---

## Regla 6

Las claves desiertas representan información estratégica.

Una clave desierta no debe interpretarse automáticamente como una falta de interés del mercado.

Podrá deberse a múltiples factores.

---

## Regla 7

Las posibles causas de una clave desierta incluyen:

- Baja competencia
- Precio poco competitivo
- Especificaciones restrictivas
- Cambio de presentación
- Cambio de concentración
- Producto descontinuado
- Clave sustituida
- Pérdida del registro sanitario
- Suspensión temporal
- Desabasto
- Fuente única
- Patente vigente
- Fin de patente
- Cambios regulatorios

SIMI deberá identificar estas posibles causas mediante reglas de negocio y, en el futuro, mediante Inteligencia Artificial.

---

## Regla 8

Analytics calcula.

Analytics nunca interpreta.

Su responsabilidad es obtener:

- KPIs
- Rankings
- Variaciones
- Comparativos
- Tendencias

---

## Regla 9

Intelligence interpreta.

Su responsabilidad será generar:

- Alertas
- Diagnósticos
- Recomendaciones
- Observaciones
- Conclusiones ejecutivas

---

## Regla 10

Toda funcionalidad nueva deberá desarrollarse mediante módulos independientes.

Ejemplos

excel_service.py

analytics_service.py

intelligence_service.py

adjudicaciones_service.py

database_service.py

---

## Regla 11

Producción y desarrollo estarán separados.

main

Versión estable.

develop

Nuevas funcionalidades.

---

## Regla 12

Toda nueva versión deberá actualizar

README

CHANGELOG

ROADMAP

MODELO_NEGOCIO

---

# Catálogo Maestro de Claves

Cada clave tendrá información histórica independiente de las investigaciones.

En futuras versiones deberá conocerse:

- ¿La clave sigue vigente?
- ¿Fue sustituida?
- ¿Cambió su presentación?
- ¿Cambió su concentración?
- ¿Es producto de patente?
- ¿Es fuente única?
- ¿Perdió la patente?
- ¿Finalizó el periodo de exclusividad?
- ¿Perdió el registro sanitario?
- ¿Está suspendida?
- ¿Tiene desabasto reportado?
- ¿Tiene observaciones regulatorias?

---

# Motor de Diagnóstico

SIMI clasificará automáticamente situaciones detectadas.

Ejemplos

D01

Baja competencia

D02

Precio poco competitivo

D03

Producto descontinuado

D04

Cambio de presentación

D05

Cambio de concentración

D06

Clave sustituida

D07

Pérdida de registro sanitario

D08

Patente o fuente única

D09

Fin de patente

D10

Desabasto reportado

D11

Riesgo de abastecimiento

D99

Diagnóstico no determinado

---

# Arquitectura funcional

Investigación

↓

Invitación

↓

Claves solicitadas

↓

Ofertas

↓

Claves ofertadas

↓

Claves desiertas

↓

Adjudicaciones

↓

Indicadores (Analytics)

↓

Diagnósticos (Intelligence)

↓

Reportes Ejecutivos

↓

Inteligencia Artificial

---

# Visión del proyecto

SIMI evolucionará desde un sistema de comparación de investigaciones hacia una plataforma integral de Inteligencia de Mercado.

En versiones futuras incorporará:

- Base de datos centralizada
- Histórico permanente
- Dashboard Ejecutivo
- Motor de Diagnóstico
- Adjudicaciones
- Riesgo de abastecimiento
- Predicción de precios
- Inteligencia Artificial
- Reportes automáticos
- API de integración
- Power BI
- Portal Institucional

---

# Principios de desarrollo

Todo nuevo desarrollo deberá cumplir los siguientes principios:

- Arquitectura modular
- Separación de responsabilidades
- Código reutilizable
- Alta escalabilidad
- Compatibilidad hacia atrás
- Documentación permanente
- Versionado semántico
- Preparación para Inteligencia Artificial

---

# Objetivo final

SIMI deberá convertirse en la plataforma institucional capaz de transformar información dispersa en conocimiento útil para apoyar decisiones estratégicas en procesos de contratación pública.

No será únicamente un sistema que muestre datos.

Será un sistema capaz de explicar qué ocurrió, por qué ocurrió y cuál es la mejor decisión con base en la información disponible.