# SIMI – Sistema Inteligente de Mercado e Investigaciones

# Sprint 0.3.2

## Modelo de Datos Relacional (Documentación)

---

# Objetivo del Sprint

Definir la estructura relacional inicial de SIMI tomando como base el flujo operativo real de una Investigación de Mercado, asegurando que la base de datos almacene únicamente información fuente y que todo el análisis sea calculado dinámicamente por el sistema.

---

# Principios de Arquitectura

## 1. SIMI almacenará únicamente datos fuente.

La base de datos conservará exclusivamente la información capturada o importada desde los archivos oficiales.

No se almacenarán resultados de análisis.

Toda la inteligencia será generada en tiempo real por el motor de análisis.

---

## 2. Los cálculos nunca se almacenan.

SIMI calculará dinámicamente:

* Mejor precio.
* Mejor precio viable.
* Precio promedio.
* Media preliminar.
* Media posterior a evaluación.
* Variaciones.
* Cobertura.
* Competencia.
* Claves desiertas.
* Rankings.
* Ahorros obtenidos en subasta.
* Indicadores históricos.

Con ello se evita duplicidad de información, inconsistencias y crecimiento innecesario de la base de datos.

---

## 3. SIMI analiza proveedores, no fabricantes.

El sistema tendrá como unidad de análisis al proveedor.

No se administrará información relacionada con fabricantes.

---

# Flujo General del Procedimiento

```text
Creación del procedimiento

↓

Carga 1
Universo del Procedimiento

↓

Carga 2
Propuestas Preliminares

↓

Carga 3
Evaluación Técnica

↓

Carga 4
Resultado de Subasta

↓

Carga 5
Adjudicación Final
```

Cada carga agrega información al procedimiento.

Ninguna sustituye a la anterior.

---

# Carga 1

## Universo del Procedimiento

### Captura manual por el administrador

* Nombre del procedimiento.
* Tipo de procedimiento.

### Información obtenida del archivo

* Clave.
* Descripción.
* Cantidad requerida.

### Información descartada

* Partida.
* CUCOP.
* Cualquier otra información administrativa.

### Resultado

SIMI crea automáticamente:

* El procedimiento.
* El universo completo de claves.

---

# Carga 2

## Propuestas Preliminares

Información almacenada:

* RFC.
* Razón Social.
* Clave.
* Cantidad ofertada.
* País de origen.
* Precio unitario.

La descripción únicamente se utiliza para validación.

No se almacena nuevamente.

---

## Objetivo

Registrar todas las propuestas económicas recibidas antes de la evaluación técnica.

---

# Carga 3

## Evaluación Técnica

Información almacenada:

* RFC.
* Clave.
* Opinión técnica.

La evaluación técnica no elimina propuestas.

Únicamente clasifica cada propuesta.

---

## Resultado

SIMI podrá generar dos escenarios de análisis:

### Escenario preliminar

Considera todas las propuestas recibidas.

Sirve para:

* Obtener el presupuesto preliminar.
* Calcular la media inicial.
* Analizar el interés del mercado.

---

### Escenario posterior a evaluación

Considera únicamente las propuestas con evaluación favorable.

Sirve como base para:

* La subasta.
* El análisis económico definitivo.

---

# Carga 4

## Resultado de Subasta

Información almacenada:

* RFC.
* Clave.
* Cantidad ofertada.
* Precio unitario.

La subasta no sustituye la propuesta preliminar.

Ambos momentos permanecen almacenados.

SIMI podrá comparar:

* Precio preliminar.
* Precio posterior a subasta.

---

## Reglas

Una propuesta de subasta podrá ser:

* Una propuesta extemporánea.

Obligatoriamente deberá:

* Pertenecer al procedimiento seleccionado por el administrador.
* Contar con evaluación técnica para participar en el análisis económico final.

---

# Carga 5

## Adjudicación Final

Información almacenada:

* RFC.
* Clave.
* Cantidad adjudicada.
* Porcentaje de adjudicación.
* Precio adjudicado.
* Monto adjudicado.

---

## Escenarios permitidos

### Un proveedor

100%

---

### Dos proveedores

60%

40%

---

### Tres proveedores

50%

30%

20%

SIMI deberá permitir cualquier distribución de adjudicación siempre que la suma corresponda al total adjudicado para la clave.

---

# Modelo Relacional Inicial

## procedimientos

Información general del procedimiento.

Campos principales:

* id_procedimiento
* nombre_procedimiento
* tipo_procedimiento
* fecha_creacion
* estado

Esta tabla se crea automáticamente durante la Carga 1.

---

## procedimiento_claves

Universo de claves pertenecientes a un procedimiento.

Campos principales:

* id_procedimiento_clave
* id_procedimiento
* clave
* descripcion
* cantidad_requerida

Esta tabla se crea automáticamente durante la Carga 1.

---

## proveedores

Catálogo maestro de proveedores.

Campos principales:

* id_proveedor
* rfc
* razon_social

---

## propuestas_preliminares

Información obtenida durante la Carga 2.

Campos principales:

* id_propuesta_preliminar
* id_procedimiento
* id_proveedor
* clave
* cantidad_ofertada
* pais_origen
* precio_unitario

---

## evaluaciones_tecnicas

Información obtenida durante la Carga 3.

Campos principales:

* id_evaluacion
* id_procedimiento
* id_proveedor
* clave
* opinion_tecnica

---

## propuestas_subasta

Información obtenida durante la Carga 4.

Campos principales:

* id_propuesta_subasta
* id_procedimiento
* id_proveedor
* clave
* cantidad_ofertada
* precio_unitario

---

## adjudicaciones

Información obtenida durante la Carga 5.

Campos principales:

* id_adjudicacion
* id_procedimiento
* id_proveedor
* clave
* cantidad_adjudicada
* porcentaje_adjudicacion
* precio_adjudicado
* monto_adjudicado

---

## cargas_archivos

Bitácora de importaciones.

Campos principales:

* id_carga
* id_procedimiento
* tipo_carga
* nombre_archivo
* fecha_carga
* usuario_carga
* registros_procesados
* registros_validos
* registros_error

---

# Conclusiones del Sprint

Con este sprint queda definido el modelo relacional inicial de SIMI, alineado al flujo operativo real de las Investigaciones de Mercado.

Se estableció que la base de datos almacenará únicamente datos fuente, mientras que todos los indicadores, estadísticas y análisis serán calculados dinámicamente por el motor de SIMI.

Asimismo, se definieron las cinco cargas oficiales de información, su propósito, las reglas de negocio asociadas y las entidades principales que conformarán la base de datos.

Este modelo constituye la base técnica para el desarrollo físico de la base de datos y la implementación del motor de análisis del sistema.
