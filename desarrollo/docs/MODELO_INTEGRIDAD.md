# Sprint 0.4.3 – Modelo Relacional e Integridad Referencial

**Proyecto:** SIMI – Sistema Inteligente para Investigaciones de Mercado

**Estado:** ✅ Sprint Cerrado

**Versión:** 1.0

---

# Objetivo

Definir el modelo relacional completo de SIMI, estableciendo formalmente las relaciones entre las tablas del sistema, las reglas de integridad referencial, las restricciones de negocio y los lineamientos técnicos necesarios para garantizar la consistencia de la información antes de la implementación física de la base de datos.

Este sprint representa la transición entre el diseño lógico y la implementación física del modelo de datos.

---

# Alcance

Durante este sprint se documentó la estructura relacional del sistema sin incorporar nuevas entidades al modelo.

Se trabajó exclusivamente sobre las tablas aprobadas en los sprints anteriores, validando sus relaciones, dependencias y reglas de integridad.

---

# Tablas incluidas

## Catálogos

* cat_categorias_clave
* claves
* proveedores

## Operación

* procedimientos
* procedimiento_claves
* procedimiento_fases
* propuestas
* evaluaciones_tecnicas
* adjudicaciones

## Histórico

* adjudicaciones_historicas

---

# Actividades realizadas

## 1. Mapa completo de relaciones

Se documentó la arquitectura general del modelo relacional, identificando las relaciones existentes entre todas las tablas del sistema y clasificándolas en:

* Catálogos.
* Operación.
* Histórico.

---

## 2. Definición de llaves primarias (PK)

Se validó que todas las tablas cuenten con una llave primaria única que permita identificar cada registro de manera inequívoca.

---

## 3. Definición de llaves foráneas (FK)

Se establecieron todas las relaciones entre tablas operativas mediante llaves foráneas, garantizando la integridad referencial del modelo.

Se confirmó que:

* `cat_categorias_clave` se relaciona con `claves`.
* `procedimientos` es la entidad central del modelo operativo.
* `procedimiento_claves` resuelve la relación muchos a muchos entre procedimientos y claves.
* `propuestas`, `evaluaciones_tecnicas` y `adjudicaciones` dependen simultáneamente de procedimiento, clave y proveedor.

---

## 4. Cardinalidades

Se definieron todas las cardinalidades del modelo.

Entre ellas:

* 1:N
* N:M

La única relación muchos a muchos identificada corresponde a:

```text
procedimientos ↔ claves
```

resuelta mediante la tabla:

```text
procedimiento_claves
```

---

## 5. Reglas de negocio

Se documentaron las reglas que gobiernan cada relación del modelo.

Entre las principales:

* un procedimiento puede contener múltiples claves;
* una clave puede participar en múltiples procedimientos;
* un proveedor puede presentar múltiples propuestas;
* una clave puede adjudicarse a uno o varios proveedores;
* las fases del procedimiento se registran exclusivamente en `procedimiento_fases`.

---

## 6. Integridad referencial

Se estableció una política conservadora para proteger la trazabilidad del sistema.

Como regla general:

```text
ON DELETE RESTRICT
ON UPDATE CASCADE
```

Esta decisión evita la eliminación accidental de información relacionada con procedimientos, propuestas, evaluaciones y adjudicaciones.

---

## 7. Restricciones UNIQUE

Se identificaron las combinaciones que deben permanecer únicas dentro del sistema.

Entre ellas:

```text
procedimiento_claves
(id_procedimiento, id_clave)

propuestas
(id_procedimiento, id_clave, id_proveedor)

evaluaciones_tecnicas
(id_procedimiento, id_clave, id_proveedor)

adjudicaciones
(id_procedimiento, id_clave, id_proveedor)
```

Estas restricciones impiden la generación de registros duplicados durante la operación normal del sistema.

---

## 8. Restricciones CHECK

Se documentaron las validaciones mínimas que deberán implementarse en la base de datos.

Ejemplos:

* cantidades mayores que cero;
* precios unitarios positivos;
* porcentaje de adjudicación entre 0 y 100;
* campos obligatorios no vacíos.

Estas validaciones permitirán garantizar la calidad de la información desde el nivel de la base de datos.

---

## 9. Índices recomendados

Se definieron índices para optimizar las consultas más frecuentes del sistema.

Principalmente para búsquedas por:

* procedimiento;
* clave;
* proveedor;
* ejercicio;
* precio;
* evaluación técnica;
* adjudicación.

Asimismo, se propusieron índices compuestos para acelerar los análisis comparativos y las consultas de negocio.

---

## 10. Matriz de relaciones

Se consolidó una matriz técnica que resume:

* tablas relacionadas;
* cardinalidad;
* llave foránea;
* reglas `ON DELETE`;
* reglas `ON UPDATE`;
* observaciones de negocio.

Esta matriz servirá como referencia para la implementación física de la base de datos.

---

## 11. Modelo relacional consolidado

Se integró toda la información generada durante el sprint en un único modelo relacional que representa la estructura definitiva de la base de datos de SIMI.

Este modelo constituye la especificación oficial para la implementación física del sistema.

---

# Decisiones arquitectónicas relevantes

Durante el desarrollo del sprint se identificó una mejora importante en el diseño del modelo.

## Tabla `adjudicaciones_historicas`

Inicialmente se contempló relacionarla mediante llaves foráneas con las tablas operativas.

Después de revisar el diccionario de datos, se determinó que esto no representaba correctamente la naturaleza de la información histórica.

Se aprobó mantenerla como una tabla independiente:

* sin llaves foráneas obligatorias;
* alimentada mediante cargas históricas realizadas por el usuario;
* conservando la información exactamente como aparece en los archivos originales.

Esta decisión permite comparar procedimientos históricos aun cuando las claves, proveedores o procedimientos ya no existan en el modelo operativo actual.

Asimismo, se confirmó que:

```text
monto_adjudicado
```

no será almacenado, sino calculado dinámicamente mediante:

```text
cantidad_adjudicada × precio_unitario_adjudicado
```

---

# Resultado del Sprint

Con la conclusión de este sprint queda completamente definido el modelo relacional de SIMI.

La arquitectura de la base de datos cuenta con:

* entidades identificadas;
* relaciones documentadas;
* llaves primarias;
* llaves foráneas;
* cardinalidades;
* restricciones de negocio;
* reglas de integridad referencial;
* índices recomendados;
* matriz de relaciones;
* modelo relacional consolidado.

Todo ello constituye la especificación técnica necesaria para iniciar la implementación física de la base de datos.

---

# Entregables

* Modelo completo de relaciones.
* Definición de PK y FK.
* Cardinalidades.
* Reglas de negocio.
* Integridad referencial (`ON DELETE` y `ON UPDATE`).
* Restricciones `UNIQUE`.
* Restricciones `CHECK`.
* Índices recomendados.
* Matriz de relaciones.
* Modelo relacional consolidado.

---

# Cierre del Sprint

**Sprint:** 0.4.3 – Modelo Relacional e Integridad Referencial

**Estado:** ✅ CERRADO

El diseño lógico de la base de datos de SIMI queda oficialmente concluido.

La documentación generada durante los sprints 0.3, 0.4, 0.4.2 y 0.4.3 proporciona una especificación técnica completa, consistente y lista para su implementación.

El siguiente paso del proyecto será traducir este diseño a un modelo físico mediante la creación del script SQL, las restricciones, los índices y los objetos necesarios para su despliegue en el motor de base de datos seleccionado.

---

# Próximo Sprint

## Sprint 0.5 – Implementación Física de la Base de Datos

### Objetivo

Transformar el modelo lógico validado en una implementación física completamente funcional mediante la generación del script SQL oficial de SIMI.

### Alcance

* Creación de todas las tablas.
* Definición de tipos de datos finales.
* Implementación de llaves primarias y foráneas.
* Restricciones `UNIQUE` y `CHECK`.
* Índices (`CREATE INDEX`).
* Configuración de claves autoincrementales (`IDENTITY` o `SERIAL`).
* Convenciones de nomenclatura.
* Script maestro de creación de la base de datos.
* Validación del modelo para PostgreSQL y preparación para una posible portabilidad a otros motores compatibles.
