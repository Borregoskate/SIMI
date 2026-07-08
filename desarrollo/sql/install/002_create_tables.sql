-- ============================================================
-- SIMI
-- Sistema Inteligente de Mercado e Investigaciones
-- Sprint 0.5 - Implementación Base
--
-- Archivo:
-- 002_create_tables.sql
--
-- Descripción:
-- Creación física de las tablas del sistema.
--
-- Este archivo NO contiene:
--   • Llaves foráneas
--   • Índices
--   • Triggers
--   • Funciones
--   • Datos
--
-- Todos esos elementos se crean en archivos posteriores.
-- ============================================================



-- ============================================================
-- CATÁLOGO DE CATEGORÍAS
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.cat_categorias_clave (

    id_categoria BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre_categoria VARCHAR(100) NOT NULL,

    descripcion TEXT

);



-- ============================================================
-- PROCEDIMIENTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.procedimientos (

    id_procedimiento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    numero_procedimiento VARCHAR(150) NOT NULL,

    descripcion TEXT,

    ejercicio INTEGER NOT NULL,

    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    activo BOOLEAN NOT NULL DEFAULT TRUE

);



-- ============================================================
-- CATÁLOGO DE CLAVES
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.claves (

    id_clave BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    clave VARCHAR(50) NOT NULL,

    descripcion TEXT NOT NULL,

    id_categoria BIGINT

);



-- ============================================================
-- CLAVES DEL PROCEDIMIENTO
-- (Universo de claves de cada procedimiento)
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.procedimiento_claves (

    id_procedimiento_clave BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_procedimiento BIGINT NOT NULL,

    id_clave BIGINT NOT NULL,

    cantidad_requerida NUMERIC(18,2) NOT NULL

);



-- ============================================================
-- CATÁLOGO DE PROVEEDORES
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.proveedores (

    id_proveedor BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    rfc VARCHAR(13) NOT NULL,

    razon_social VARCHAR(255) NOT NULL

);



-- ============================================================
-- PROPUESTAS
--
-- Cada propuesta pertenece a una clave específica
-- dentro de un procedimiento.
--
-- Se relaciona con procedimiento_claves,
-- NO directamente con claves.
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.propuestas (

    id_propuesta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_procedimiento_clave BIGINT NOT NULL,

    id_proveedor BIGINT NOT NULL,

    tipo_propuesta VARCHAR(20) NOT NULL,

    cantidad_ofertada NUMERIC(18,2) NOT NULL,

    pais_origen VARCHAR(100),

    precio_unitario NUMERIC(18,2) NOT NULL,

    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

);



-- ============================================================
-- EVALUACIONES TÉCNICAS
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.evaluaciones_tecnicas (

    id_evaluacion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_procedimiento BIGINT NOT NULL,

    id_proveedor BIGINT NOT NULL,

    id_clave BIGINT NOT NULL,

    resultado VARCHAR(20) NOT NULL

);



-- ============================================================
-- ADJUDICACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.adjudicaciones (

    id_adjudicacion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_procedimiento BIGINT NOT NULL,

    id_clave BIGINT NOT NULL,

    id_proveedor BIGINT NOT NULL,

    cantidad_adjudicada NUMERIC(18,2) NOT NULL,

    porcentaje_adjudicado NUMERIC(5,2) NOT NULL,

    precio_unitario_adjudicado NUMERIC(18,2) NOT NULL

);



-- ============================================================
-- ADJUDICACIONES HISTÓRICAS
--
-- Tabla de consulta histórica.
--
-- Utiliza los catálogos de claves y proveedores
-- pero no depende de un procedimiento registrado
-- dentro de SIMI.
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.adjudicaciones_historicas (

    id_adjudicacion_historica BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    numero_procedimiento VARCHAR(150),

    id_clave BIGINT NOT NULL,

    id_proveedor BIGINT NOT NULL,

    cantidad_adjudicada NUMERIC(18,2),

    porcentaje_adjudicado NUMERIC(5,2),

    precio_unitario_adjudicado NUMERIC(18,2) NOT NULL

);



-- ============================================================
-- BITÁCORA DE FASES DEL PROCEDIMIENTO
-- ============================================================

CREATE TABLE IF NOT EXISTS simi.procedimiento_fases (

    id_procedimiento_fase BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_procedimiento BIGINT NOT NULL,

    fase VARCHAR(50) NOT NULL,

    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

);