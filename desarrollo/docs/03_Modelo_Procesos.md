# SIMI – Sistema Inteligente de Mercado e Investigaciones

# Documento 03

# Modelo de Procesos y Filosofía del Sistema

| Campo                | Valor                 |
| -------------------- | --------------------- |
| Documento            | 03_Modelo_Procesos.md |
| Versión              | 1.0                   |
| Estado               | Aprobado              |
| Proyecto             | SIMI                  |
| Sprint de creación   | Sprint 0.2.1          |
| Última actualización | Sprint 0.2.1          |

---

# 1. Objetivo

Definir el ciclo de vida de una Investigación de Mercado dentro de SIMI, estableciendo los estados del procedimiento, la trazabilidad, el manejo de versiones y los principios que regirán el desarrollo del sistema.

Este documento constituye la base funcional para el diseño del Modelo de Datos, la Arquitectura de Software y el Motor Inteligente de SIMI.

---

# 2. Filosofía del Sistema

SIMI no es un repositorio documental.

SIMI no es un sistema de gestión administrativa.

SIMI es una plataforma de inteligencia de mercado cuyo objetivo es transformar la información de las investigaciones de mercado en conocimiento útil para apoyar la toma de decisiones.

Toda la información almacenada dentro del sistema deberá aportar valor para el análisis, la comparación, la generación de indicadores o el funcionamiento del propio sistema.

---

# 3. Principios de Diseño

## 3.1 Almacenamiento con propósito

SIMI únicamente almacenará información que genere valor para:

* análisis históricos;
* comparaciones;
* indicadores;
* trazabilidad;
* operación del sistema.

Todo dato sin utilidad será descartado.

---

## 3.2 Información derivable

Toda información que pueda calcularse en tiempo de ejecución no deberá almacenarse permanentemente.

Ejemplos:

* precio promedio;
* mejor precio;
* peor precio;
* variaciones;
* rankings;
* estadísticas.

Estos valores serán calculados dinámicamente cuando sean solicitados.

---

## 3.3 Captura mínima de información

El sistema únicamente solicitará información que no pueda obtener automáticamente.

Toda la información contenida en el archivo cargado será procesada por SIMI sin intervención del usuario.

---

## 3.4 Historial relevante

La bitácora almacenará únicamente eventos que representen cambios importantes en la investigación.

No se registrarán acciones sin impacto funcional.

---

## 3.5 Inteligencia antes que documentación

SIMI no pretende sustituir expedientes administrativos, sistemas documentales o plataformas institucionales.

Su finalidad es analizar información y generar conocimiento.

---

# 4. Ciclo de Vida de una Investigación

Toda investigación seguirá el siguiente flujo principal.

```text
PROPUESTAS_RECIBIDAS

↓

EVALUADO

↓

MEJOR_OFERTA_RECIBIDA

↓

ADJUDICADO
```

Dependiendo del resultado, también podrá finalizar como:

* NO_ADJUDICADO
* CANCELADO
* SUSPENDIDO
* MODIFICADO
* DESIERTO

---

# 5. Estados del Procedimiento

## 5.1 PROPUESTAS_RECIBIDAS

Representa el registro oficial de una Investigación de Mercado dentro de SIMI.

### Información proporcionada por el administrador

* Nombre de la investigación.
* Tipo de procedimiento.

Ejemplos:

* Compra Consolidada
* Compra Emergente
* Patente y Fuente Única
* Faboterápicos
* Material de Curación
* Medicamentos
* Vacunas
* Dispositivos Médicos
* Otro

### Información registrada automáticamente por SIMI

* Fecha de carga.
* Usuario responsable.
* Estado = PROPUESTAS_RECIBIDAS.
* Número de propuestas.
* Número de proveedores.
* Número de claves.
* Cantidad total ofertada.
* Países participantes.

La carga de una investigación deberá realizarse mediante un único archivo Excel.

---

## 5.2 EVALUADO

Indica que concluyó la revisión documental y técnica de las propuestas.

El objetivo de este estado es conservar únicamente la información necesaria para alimentar el análisis histórico de SIMI.

Por cada proveedor se almacenará:

* RFC.
* Claves aprobadas.
* Resultado de evaluación (Aprobado / No aprobado).

No se almacenarán dictámenes completos, observaciones administrativas ni documentación asociada.

SIMI únicamente conservará la información indispensable para futuros análisis.

---

## 5.3 MEJOR_OFERTA_RECIBIDA

Representa que uno o varios proveedores presentaron una mejor propuesta económica posterior a la oferta inicial, normalmente derivada de una subasta privada o una etapa de mejora de ofertas.

Este estado no implica adjudicación.

Su finalidad es permitir que SIMI compare la evolución económica de las propuestas entre las distintas etapas del procedimiento.

SIMI podrá generar automáticamente indicadores como:

* Variación entre oferta inicial y mejor oferta.
* Ahorro obtenido por proveedor.
* Ahorro por clave.
* Reducción porcentual del precio.
* Mejor propuesta final por clave.
* Comparativos históricos entre investigaciones.

La información de este estado servirá como insumo para el motor de análisis y recomendaciones.

---

## 5.4 ADJUDICADO

Representa la conclusión de la investigación con uno o varios proveedores adjudicados.

La adjudicación será registrada por clave.

Por cada clave adjudicada se conservará únicamente:

* Clave.
* Proveedor adjudicado.
* Precio unitario adjudicado.
* Cantidad adjudicada.
* Monto adjudicado.

No se almacenará la fecha de adjudicación, ya que no aporta valor al análisis histórico ni a las comparaciones realizadas por SIMI.

---

## 5.5 NO_ADJUDICADO

La investigación concluyó sin adjudicar proveedor.

La información permanecerá disponible para análisis históricos y comparativos.

---

## 5.6 CANCELADO

La investigación fue cancelada.

Toda la información permanecerá almacenada.

No se eliminará ningún registro, permitiendo que SIMI utilice la información para comparaciones futuras.

---

## 5.7 SUSPENDIDO

La investigación se encuentra detenida temporalmente.

Toda la información permanecerá disponible para futuras reanudaciones y análisis.

---

## 5.8 MODIFICADO

Representa cambios relevantes dentro de la investigación.

Dependiendo de la decisión del administrador, estos cambios podrán generar una nueva versión de la investigación.

Los cambios menores únicamente serán registrados dentro de la bitácora.

---

## 5.9 DESIERTO

Representa que la investigación concluyó como desierta.

Únicamente se conservará este estado para fines estadísticos e históricos.

---

# 6. Trazabilidad

Todo cambio relevante deberá registrar:

* Qué cambió.
* Quién realizó el cambio.
* Cuándo ocurrió.
* Motivo del cambio (cuando aplique).

Dado que únicamente los administradores podrán modificar la información, la trazabilidad estará enfocada en eventos relevantes y no en cada acción realizada dentro del sistema.

---

# 7. Versionado

Las versiones de una investigación no serán generadas automáticamente.

La creación de una nueva versión será una decisión exclusiva del administrador cuando considere que un cambio afecta significativamente la información o el análisis histórico.

Los cambios menores quedarán registrados únicamente en la bitácora del sistema.

Con este enfoque se evita almacenar información redundante y se mantiene un historial de versiones útil y eficiente.

---

# 8. Alcance

Este documento constituye la base para el desarrollo de:

* Modelo de Datos.
* Arquitectura de Software.
* Base de Datos.
* Motor Analítico.
* Sistema de Recomendaciones.
* Dashboards.
* Inteligencia Artificial de SIMI.

Toda decisión futura deberá respetar los principios definidos en este documento.

---

# 9. Conclusión

SIMI nace como una plataforma de inteligencia de mercado enfocada en generar conocimiento a partir de investigaciones de mercado.

Su diseño prioriza el almacenamiento eficiente, la trazabilidad de la información y la capacidad analítica sobre la acumulación de datos administrativos.

Cada elemento almacenado dentro del sistema deberá justificar su existencia aportando valor al análisis, la comparación o la operación de la plataforma.

Este documento representa la base conceptual sobre la cual se desarrollarán todos los componentes futuros de SIMI.
