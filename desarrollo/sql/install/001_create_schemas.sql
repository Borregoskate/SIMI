/*
=========================================================
SIMI - Sistema Inteligente de Mercado e Investigaciones
Sprint 0.5 - Implementación Física de Base de Datos
Archivo: 001_create_schemas.sql
Objetivo: Crear los esquemas base de la arquitectura de datos
Motor: PostgreSQL
=========================================================
*/

CREATE SCHEMA IF NOT EXISTS simi;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE SCHEMA IF NOT EXISTS auditoria;

CREATE SCHEMA IF NOT EXISTS catalogos;

/*
=========================================================
Comentarios de documentación
=========================================================
*/

COMMENT ON SCHEMA simi IS
'Esquema principal del sistema SIMI. Contiene las tablas operativas del modelo de negocio.';

COMMENT ON SCHEMA staging IS
'Esquema temporal para cargas provenientes de archivos Excel antes de su validación e inserción definitiva.';

COMMENT ON SCHEMA auditoria IS
'Esquema para bitácoras, registros de carga, errores, eventos y trazabilidad del sistema.';

COMMENT ON SCHEMA catalogos IS
'Esquema para catálogos generales reutilizables dentro del sistema SIMI.';