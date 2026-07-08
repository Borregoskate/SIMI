# Sprint 0.4.2 – Diccionario de Datos

## SIMI – Sistema Inteligente de Mercado e Investigaciones

## Objetivo

Documentar el diccionario de datos de SIMI con base en las tablas autorizadas en el sprint anterior, evitando campos duplicados, derivados o que no correspondan al alcance aprobado.

Este documento servirá como base para el siguiente sprint, donde se definirán relaciones, llaves foráneas, restricciones e implementación SQL.

---

# Tablas autorizadas

Las tablas consideradas para este diccionario son:

1. procedimientos
2. procedimiento_fases
3. cat_categorias_clave
4. claves
5. procedimiento_claves
6. proveedores
7. propuestas
8. evaluaciones_tecnicas
9. adjudicaciones
10. adjudicaciones_historicas

---

# 1. Tabla: procedimientos

## Propósito

Almacenar la información base de cada procedimiento cargado al sistema.

No debe almacenar el estado actual del procedimiento, ya que la evolución del procedimiento se registra en la tabla `procedimiento_fases`.

## Origen

Carga de archivo o proceso iniciado por el usuario.

## Campos

| Campo                     | Tipo sugerido   | Obligatorio | Descripción                                        |
| ------------------------- | --------------- | ----------- | -------------------------------------------------- |
| id_procedimiento          | BIGINT / SERIAL | Sí          | Identificador interno del procedimiento.           |
| numero_procedimiento      | VARCHAR(100)    | Sí          | Número o identificador del procedimiento.          |
| ejercicio                 | INTEGER         | Sí          | Ejercicio o año correspondiente al procedimiento.  |
| descripcion_procedimiento | TEXT            | No          | Descripción general del procedimiento.             |
| fecha_carga               | TIMESTAMP       | Sí          | Fecha en que el procedimiento fue cargado en SIMI. |

## Notas

No se incluye `estado_procedimiento`.

El estado se obtiene consultando la última fase registrada en `procedimiento_fases`.

---

# 2. Tabla: procedimiento_fases

## Propósito

Registrar el avance del procedimiento a través de sus fases.

Esta tabla funciona como la bitácora operativa autorizada para conocer en qué etapa se encuentra un procedimiento y cómo ha avanzado en el tiempo.

## Origen

Registro generado por el sistema a partir de acciones del usuario o procesos del procedimiento.

## Campos

| Campo                 | Tipo sugerido   | Obligatorio | Descripción                                     |
| --------------------- | --------------- | ----------- | ----------------------------------------------- |
| id_procedimiento_fase | BIGINT / SERIAL | Sí          | Identificador interno del registro de fase.     |
| id_procedimiento      | BIGINT          | Sí          | Procedimiento al que pertenece la fase.         |
| fase                  | VARCHAR(100)    | Sí          | Fase o estado registrado para el procedimiento. |
| fecha                 | TIMESTAMP       | Sí          | Fecha en que se registró la fase.               |

## Fases autorizadas

* PROPUESTAS_RECIBIDAS
* EVALUADO
* MEJOR_OFERTA_RECIBIDA
* ADJUDICADO
* NO_ADJUDICADO
* CANCELADO
* SUSPENDIDO
* MODIFICADO
* DESIERTO

## Notas

Para conocer el estado actual de un procedimiento, se debe consultar la última fase registrada por fecha.

No se requiere una tabla adicional de bitácora.

---

# 3. Tabla: cat_categorias_clave

## Propósito

Catálogo para clasificar claves por categoría.

Permite agrupar claves para facilitar análisis, filtros y reportes.

## Origen

Catálogo alimentado por el usuario.

## Campos

| Campo                 | Tipo sugerido   | Obligatorio | Descripción                            |
| --------------------- | --------------- | ----------- | -------------------------------------- |
| id_categoria_clave    | BIGINT / SERIAL | Sí          | Identificador interno de la categoría. |
| categoria             | VARCHAR(150)    | Sí          | Nombre de la categoría.                |
| descripcion_categoria | TEXT            | No          | Descripción de la categoría.           |

---

# 4. Tabla: claves

## Propósito

Catálogo maestro de claves.

Solo se agregarán claves nuevas o futuras cuando el sistema no las encuentre previamente.

## Origen

Carga de archivo por parte del usuario y ampliación del catálogo cuando se detecten claves nuevas.

## Campos

| Campo              | Tipo sugerido   | Obligatorio | Descripción                               |
| ------------------ | --------------- | ----------- | ----------------------------------------- |
| id_clave           | BIGINT / SERIAL | Sí          | Identificador interno de la clave.        |
| clave              | VARCHAR(50)     | Sí          | Clave del insumo, medicamento o material. |
| descripcion        | TEXT            | Sí          | Descripción de la clave.                  |
| id_categoria_clave | BIGINT          | No          | Categoría a la que pertenece la clave.    |

---

# 5. Tabla: procedimiento_claves

## Propósito

Relacionar los procedimientos con las claves incluidas en cada uno.

Permite identificar qué claves forman parte de cada procedimiento.

## Origen

Carga de archivo por parte del usuario.

## Campos

| Campo                  | Tipo sugerido   | Obligatorio | Descripción                                                |
| ---------------------- | --------------- | ----------- | ---------------------------------------------------------- |
| id_procedimiento_clave | BIGINT / SERIAL | Sí          | Identificador interno de la relación.                      |
| id_procedimiento       | BIGINT          | Sí          | Procedimiento relacionado.                                 |
| id_clave               | BIGINT          | Sí          | Clave incluida en el procedimiento.                        |
| cantidad_requerida     | NUMERIC(18,2)   | No          | Cantidad requerida para la clave dentro del procedimiento. |

---

# 6. Tabla: proveedores

## Propósito

Catálogo maestro de proveedores.

Solo se agregarán proveedores nuevos cuando el sistema no los encuentre previamente.

## Origen

Carga de archivo por parte del usuario y ampliación automática del catálogo cuando se detecten proveedores nuevos.

## Campos

| Campo        | Tipo sugerido   | Obligatorio | Descripción                          |
| ------------ | --------------- | ----------- | ------------------------------------ |
| id_proveedor | BIGINT / SERIAL | Sí          | Identificador interno del proveedor. |
| rfc          | VARCHAR(20)     | Sí          | RFC del proveedor.                   |
| razon_social | VARCHAR(255)    | Sí          | Razón social del proveedor.          |

---

# 7. Tabla: propuestas

## Propósito

Registrar las propuestas presentadas por los proveedores para cada clave dentro de un procedimiento.

Cada propuesta debe pertenecer obligatoriamente a:

* un procedimiento;
* una clave;
* un proveedor.

## Origen

Carga de archivo por parte del usuario.

Puede representar:

* propuesta inicial;
* propuesta de subasta;
* propuesta extemporánea.

## Campos

| Campo             | Tipo sugerido   | Obligatorio | Descripción                                  |
| ----------------- | --------------- | ----------- | -------------------------------------------- |
| id_propuesta      | BIGINT / SERIAL | Sí          | Identificador interno de la propuesta.       |
| id_procedimiento  | BIGINT          | Sí          | Procedimiento al que pertenece la propuesta. |
| id_clave          | BIGINT          | Sí          | Clave ofertada.                              |
| id_proveedor      | BIGINT          | Sí          | Proveedor que presenta la propuesta.         |
| cantidad_ofertada | NUMERIC(18,2)   | Sí          | Cantidad ofertada por el proveedor.          |
| pais_origen       | VARCHAR(100)    | No          | País de origen reportado para la propuesta.  |
| precio_unitario   | NUMERIC(18,6)   | Sí          | Precio unitario ofertado.                    |
| tipo_propuesta    | VARCHAR(50)     | Sí          | Tipo de propuesta registrada.                |
| fecha_carga       | TIMESTAMP       | Sí          | Fecha en que se cargó la propuesta.          |

## Valores sugeridos para `tipo_propuesta`

* INICIAL
* SUBASTA
* EXTEMPORANEA

## Regla autorizada

Una propuesta de subasta no debe actualizar ni sobrescribir una propuesta existente.

Si durante la subasta aparece una propuesta que no existía previamente, se registra como propuesta extemporánea.

---

# 8. Tabla: evaluaciones_tecnicas

## Propósito

Registrar si una propuesta cumple técnicamente antes de participar en el análisis económico final.

## Origen

Carga de archivo o proceso iniciado por el usuario.

## Campos

| Campo                 | Tipo sugerido   | Obligatorio | Descripción                                     |
| --------------------- | --------------- | ----------- | ----------------------------------------------- |
| id_evaluacion_tecnica | BIGINT / SERIAL | Sí          | Identificador interno de la evaluación técnica. |
| id_propuesta          | BIGINT          | Sí          | Propuesta evaluada.                             |
| cumple_tecnicamente   | BOOLEAN         | Sí          | Indica si la propuesta cumple técnicamente.     |
| fecha_evaluacion      | TIMESTAMP       | No          | Fecha en que se registró la evaluación técnica. |

## Regla autorizada

Solo las propuestas que cumplen técnicamente podrán participar en el análisis económico final.

---

# 9. Tabla: adjudicaciones

## Propósito

Registrar las adjudicaciones finales por procedimiento, clave y proveedor.

Una clave puede adjudicarse a uno o varios proveedores.

## Origen

Carga de archivo por parte del usuario o resultado del análisis final.

## Campos

| Campo                      | Tipo sugerido   | Obligatorio | Descripción                                  |
| -------------------------- | --------------- | ----------- | -------------------------------------------- |
| id_adjudicacion            | BIGINT / SERIAL | Sí          | Identificador interno de la adjudicación.    |
| id_procedimiento           | BIGINT          | Sí          | Procedimiento adjudicado.                    |
| id_clave                   | BIGINT          | Sí          | Clave adjudicada.                            |
| id_proveedor               | BIGINT          | Sí          | Proveedor adjudicado.                        |
| cantidad_adjudicada        | NUMERIC(18,2)   | Sí          | Cantidad adjudicada al proveedor.            |
| precio_unitario_adjudicado | NUMERIC(18,6)   | Sí          | Precio unitario adjudicado.                  |
| porcentaje_entrega         | NUMERIC(5,2)    | No          | Porcentaje de entrega asignado al proveedor. |

## Notas

No se incluye `monto_adjudicado`.

El monto se calcula como:

`cantidad_adjudicada * precio_unitario_adjudicado`

Tampoco se incluye fecha de adjudicación, ya que se acordó que no era relevante para esta etapa.

## Escenarios autorizados

* Un proveedor adjudicado al 100%.
* Dos proveedores con distribución, por ejemplo 60% / 40%.
* Varios proveedores con distribución proporcional.

---

# 10. Tabla: adjudicaciones_historicas

## Propósito

Almacenar adjudicaciones de procedimientos anteriores para análisis comparativo.

Permitirá revisar:

* adjudicaciones pasadas;
* precios históricos;
* comportamiento por proveedor;
* comportamiento por clave;
* variaciones entre ejercicios o procedimientos.

## Origen

Carga de archivos históricos por parte del usuario.

## Campos

| Campo                      | Tipo sugerido   | Obligatorio | Descripción                                   |
| -------------------------- | --------------- | ----------- | --------------------------------------------- |
| id_adjudicacion_historica  | BIGINT / SERIAL | Sí          | Identificador interno del registro histórico. |
| ejercicio                  | INTEGER         | Sí          | Año o ejercicio del registro histórico.       |
| numero_procedimiento       | VARCHAR(100)    | No          | Número del procedimiento histórico.           |
| clave                      | VARCHAR(50)     | Sí          | Clave adjudicada históricamente.              |
| descripcion                | TEXT            | No          | Descripción de la clave histórica.            |
| rfc                        | VARCHAR(20)     | No          | RFC del proveedor adjudicado históricamente.  |
| razon_social               | VARCHAR(255)    | Sí          | Razón social del proveedor adjudicado.        |
| cantidad_adjudicada        | NUMERIC(18,2)   | No          | Cantidad adjudicada históricamente.           |
| precio_unitario_adjudicado | NUMERIC(18,6)   | Sí          | Precio unitario adjudicado históricamente.    |
| fuente_archivo             | VARCHAR(255)    | No          | Archivo origen de la información histórica.   |
| fecha_carga                | TIMESTAMP       | Sí          | Fecha en que se cargó el archivo histórico.   |

## Notas

No se incluye `monto_adjudicado`.

El monto histórico se calcula como:

`cantidad_adjudicada * precio_unitario_adjudicado`

---

# Reglas generales del diccionario

## 1. Tablas alimentadas por usuario

Las siguientes tablas dependen de carga de archivos o procesos iniciados por el usuario:

* procedimientos;
* cat_categorias_clave;
* claves;
* procedimiento_claves;
* proveedores;
* propuestas;
* evaluaciones_tecnicas;
* adjudicaciones;
* adjudicaciones_historicas.

## 2. Tabla generada por avance operativo

La tabla `procedimiento_fases` registra el avance del procedimiento.

No sustituye a `procedimientos`; complementa su trazabilidad.

## 3. Catálogos

Las tablas `claves`, `proveedores` y `cat_categorias_clave` funcionan como catálogos.

El sistema no debe duplicar registros existentes.

Si durante una carga se detecta una clave, proveedor o categoría no registrada, podrá agregarse al catálogo correspondiente.

## 4. Estados y fases

El estado actual del procedimiento no se almacena en `procedimientos`.

Debe obtenerse desde `procedimiento_fases`, consultando el último registro de fase del procedimiento.

## 5. Propuestas

Toda propuesta debe pertenecer al procedimiento seleccionado.

Toda propuesta debe estar asociada con una clave y un proveedor.

Las propuestas de subasta no deben sobrescribir propuestas existentes.

Si aparece una propuesta que no existía previamente, se considera propuesta extemporánea.

## 6. Evaluación técnica

Toda propuesta debe ser evaluada técnicamente antes de participar en el análisis económico final.

Las propuestas que no cumplen técnicamente quedan fuera del análisis económico final.

## 7. Mejor oferta recibida

La fase `MEJOR_OFERTA_RECIBIDA` no implica adjudicación.

Representa únicamente la mejor alternativa detectada por SIMI con base en los criterios definidos para el análisis.

## 8. Adjudicaciones

La adjudicación representa el resultado final por clave y proveedor.

Una clave puede tener uno o varios proveedores adjudicados.

## 9. Datos calculables

No deben almacenarse campos que puedan calcularse directamente.

Por esta razón no se almacenan:

* monto adjudicado;
* monto adjudicado histórico;
* estado actual del procedimiento.

## 10. Históricos

Las adjudicaciones históricas se conservan como referencia comparativa.

No sustituyen las adjudicaciones actuales del procedimiento.

---

# Cierre del Sprint 0.4.2

Con este diccionario de datos queda documentada la estructura autorizada para SIMI.

El documento respeta las tablas aprobadas, elimina campos redundantes y deja claro que la evolución del procedimiento se controla mediante `procedimiento_fases`.

## Siguiente sprint sugerido

**Sprint 0.4.3 – Relaciones, llaves foráneas y reglas de integridad**

En el siguiente sprint se deberán definir:

* llaves primarias;
* llaves foráneas;
* restricciones únicas;
* relaciones entre tablas;
* reglas de integridad;
* validaciones mínimas;
* base para generar el script SQL inicial.
