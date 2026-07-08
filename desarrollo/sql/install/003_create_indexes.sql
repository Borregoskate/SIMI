-- ============================================================
-- SIMI
-- Sistema Inteligente de Mercado e Investigaciones
-- Sprint 0.5 - Implementación Base
--
-- Archivo:
-- 003_create_indexes.sql
--
-- Descripción:
-- Creación de índices para optimizar consultas frecuentes.
--
-- Este archivo NO contiene:
--   • Llaves foráneas
--   • Restricciones UNIQUE
--   • Restricciones CHECK
--   • Triggers
--   • Funciones
--   • Datos
-- ============================================================



-- ============================================================
-- ÍNDICES PARA PROCEDIMIENTOS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_procedimientos_numero
ON simi.procedimientos (numero_procedimiento);

CREATE INDEX IF NOT EXISTS idx_procedimientos_ejercicio
ON simi.procedimientos (ejercicio);

CREATE INDEX IF NOT EXISTS idx_procedimientos_activo
ON simi.procedimientos (activo);



-- ============================================================
-- ÍNDICES PARA CATÁLOGO DE CLAVES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_claves_clave
ON simi.claves (clave);

CREATE INDEX IF NOT EXISTS idx_claves_id_categoria
ON simi.claves (id_categoria);



-- ============================================================
-- ÍNDICES PARA CLAVES DEL PROCEDIMIENTO
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_procedimiento_claves_id_procedimiento
ON simi.procedimiento_claves (id_procedimiento);

CREATE INDEX IF NOT EXISTS idx_procedimiento_claves_id_clave
ON simi.procedimiento_claves (id_clave);

CREATE INDEX IF NOT EXISTS idx_procedimiento_claves_procedimiento_clave
ON simi.procedimiento_claves (id_procedimiento, id_clave);



-- ============================================================
-- ÍNDICES PARA PROVEEDORES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_proveedores_rfc
ON simi.proveedores (rfc);

CREATE INDEX IF NOT EXISTS idx_proveedores_razon_social
ON simi.proveedores (razon_social);



-- ============================================================
-- ÍNDICES PARA PROPUESTAS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_propuestas_id_procedimiento_clave
ON simi.propuestas (id_procedimiento_clave);

CREATE INDEX IF NOT EXISTS idx_propuestas_id_proveedor
ON simi.propuestas (id_proveedor);

CREATE INDEX IF NOT EXISTS idx_propuestas_tipo_propuesta
ON simi.propuestas (tipo_propuesta);

CREATE INDEX IF NOT EXISTS idx_propuestas_fecha_registro
ON simi.propuestas (fecha_registro);

CREATE INDEX IF NOT EXISTS idx_propuestas_proc_clave_proveedor
ON simi.propuestas (id_procedimiento_clave, id_proveedor);



-- ============================================================
-- ÍNDICES PARA EVALUACIONES TÉCNICAS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_evaluaciones_id_procedimiento
ON simi.evaluaciones_tecnicas (id_procedimiento);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_id_proveedor
ON simi.evaluaciones_tecnicas (id_proveedor);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_id_clave
ON simi.evaluaciones_tecnicas (id_clave);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_resultado
ON simi.evaluaciones_tecnicas (resultado);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_proc_clave_proveedor
ON simi.evaluaciones_tecnicas (id_procedimiento, id_clave, id_proveedor);



-- ============================================================
-- ÍNDICES PARA ADJUDICACIONES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_id_procedimiento
ON simi.adjudicaciones (id_procedimiento);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_id_clave
ON simi.adjudicaciones (id_clave);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_id_proveedor
ON simi.adjudicaciones (id_proveedor);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_proc_clave
ON simi.adjudicaciones (id_procedimiento, id_clave);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_proc_clave_proveedor
ON simi.adjudicaciones (id_procedimiento, id_clave, id_proveedor);



-- ============================================================
-- ÍNDICES PARA ADJUDICACIONES HISTÓRICAS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_hist_numero_procedimiento
ON simi.adjudicaciones_historicas (numero_procedimiento);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_hist_id_clave
ON simi.adjudicaciones_historicas (id_clave);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_hist_id_proveedor
ON simi.adjudicaciones_historicas (id_proveedor);

CREATE INDEX IF NOT EXISTS idx_adjudicaciones_hist_clave_proveedor
ON simi.adjudicaciones_historicas (id_clave, id_proveedor);



-- ============================================================
-- ÍNDICES PARA BITÁCORA DE FASES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_procedimiento_fases_id_procedimiento
ON simi.procedimiento_fases (id_procedimiento);

CREATE INDEX IF NOT EXISTS idx_procedimiento_fases_fase
ON simi.procedimiento_fases (fase);

CREATE INDEX IF NOT EXISTS idx_procedimiento_fases_fecha
ON simi.procedimiento_fases (fecha);

CREATE INDEX IF NOT EXISTS idx_procedimiento_fases_proc_fase
ON simi.procedimiento_fases (id_procedimiento, fase);