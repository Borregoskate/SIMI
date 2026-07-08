Sprint 0.5
Implementación de Base de Datos
Documento de Cierre

Versión: 0.5.0

Estado: FINALIZADO

Fecha: Julio 2026

Objetivo del Sprint

Preparar la base de datos de SIMI para producción.

En este sprint no se desarrolló ninguna funcionalidad del sistema.

El objetivo fue dejar completamente lista la infraestructura SQL para que posteriormente cualquier instalación (Supabase, PostgreSQL local o servidor dedicado) pueda realizarse simplemente ejecutando una serie ordenada de scripts.

Este sprint deja la base preparada para crecer durante muchos años sin tener que modificar su estructura principal.

Arquitectura elegida

Motor de Base de Datos

PostgreSQL

Compatible con

PostgreSQL Local
Supabase
Docker
AWS RDS
Azure PostgreSQL
Google Cloud SQL
Servidor dedicado propio

Por esta razón no existe ninguna dependencia con Supabase.

Supabase únicamente será utilizado como servidor durante la etapa inicial del proyecto.

Cuando SIMI migre a un servidor propio únicamente será necesario restaurar un backup de PostgreSQL.

No habrá que modificar una sola línea del sistema.

Organización de scripts

La instalación completa quedó organizada de forma secuencial.

001_create_schema.sql

Creación del esquema SIMI.

Define:

esquema
configuración inicial
comentarios generales
002_create_tables.sql

Creación de todas las tablas oficiales.

Incluye únicamente estructuras.

No contiene restricciones complejas.

003_create_indexes.sql

Optimización del rendimiento.

Se generaron índices para:

búsquedas
joins
consultas históricas
comparaciones
reportes
004_create_constraints.sql

Restricciones de integridad.

Incluye:

Primary Keys

Foreign Keys

Unique

Check

Restricciones de negocio

Integridad referencial

005_create_functions.sql

Funciones reutilizables.

Entre ellas:

Validaciones

Normalización

Cálculos

Funciones auxiliares

Permisos administrativos

006_create_views.sql

Vistas para análisis.

Se diseñaron vistas que permitirán alimentar directamente:

Dashboard

Indicadores

Análisis históricos

Comparativos

Estadísticas

Consultas administrativas

Sin necesidad de consultas SQL complejas.

007_create_triggers.sql

Automatización del sistema.

Los triggers permiten que la base de datos sea inteligente.

Incluyen reglas como:

registro automático de bitácoras

fechas automáticas

validaciones

bloqueo de modificaciones

protección de catálogos

control de eliminación

auditoría

protección de adjudicaciones

validaciones de seguridad

etc.

La filosofía adoptada fue:

El usuario nunca debe poder romper la integridad de la información.

008_create_security.sql

Implementación del modelo de seguridad.

Se definió un sistema de autenticación basado en roles.

Se preparó la base para trabajar con:

Administrador Maestro

Administrador

Capturista

Consulta

Auditor

La seguridad contempla:

Roles SQL

Permisos por tabla

Permisos por vista

Control mediante sesiones

Protección de escritura

Protección de eliminación

Separación entre lectura y administración

El único perfil autorizado para operaciones críticas será:

Administrador Maestro

Decisiones arquitectónicas importantes

Durante este sprint quedaron aprobadas varias reglas que afectan todo el proyecto.

Fechas

Todas las fechas serán automáticas.

El usuario nunca captura fechas.

Se utilizará:

CURRENT_TIMESTAMP

Eliminaciones

Solo el Administrador Maestro podrá eliminar registros.

Nunca un usuario operativo.

Auditoría

Todos los movimientos importantes quedarán registrados.

Esto permitirá conocer:

quién hizo un cambio

cuándo

qué modificó

desde qué proceso

Seguridad

La base de datos validará permisos.

No dependerá únicamente del sistema desarrollado en Python.

Aunque alguien acceda directamente mediante PostgreSQL seguirá existiendo control de permisos.

Integridad

La lógica crítica permanecerá dentro de PostgreSQL.

No únicamente en Streamlit.

Esto protege la información incluso si en el futuro cambia la aplicación.

Escalabilidad

Toda la estructura quedó preparada para crecer.

No será necesario rediseñar la base de datos para incorporar:

nuevos módulos

IA

Machine Learning

API

Portal de proveedores

Portal institucional

Servicios Web

Aplicación móvil

Servidor dedicado

Resultado obtenido

Al concluir este sprint SIMI cuenta con una base de datos completamente definida.

Se encuentran implementados:

Esquema
Tablas
Índices
Restricciones
Funciones
Vistas
Triggers
Seguridad

La base puede instalarse desde cero ejecutando los scripts en orden.

No depende de desarrollos futuros.

Estado del Proyecto
Sprints finalizados
✅ Sprint 0.1 — Definición del Proyecto
✅ Sprint 0.2 — Procesos de Negocio
✅ Sprint 0.2.1 — Estados y Flujo Operativo
✅ Sprint 0.3 — Modelo de Datos Conceptual
✅ Sprint 0.3.1 — Reglas de Negocio
✅ Sprint 0.4 — Diseño de Base de Datos
✅ Sprint 0.4.2 — Diccionario de Datos
✅ Sprint 0.4.3 — Modelo Relacional
✅ Sprint 0.5 — Implementación SQL
Versión alcanzada

SIMI v0.5.0

Estado:

Arquitectura completamente terminada.