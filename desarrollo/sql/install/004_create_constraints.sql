/*
===============================================================================
SIMI - Sistema Inteligente de Mercado e Investigaciones
Sprint 0.5
Archivo: 004_create_constraints.sql
Descripción:
    Creación de restricciones de integridad para la base de datos.
===============================================================================
*/

BEGIN;

-- ============================================================================
-- TABLA: cat_categorias_clave
-- ============================================================================

ALTER TABLE simi.cat_categorias_clave
ADD CONSTRAINT uq_categoria_nombre_categoria
UNIQUE (nombre_categoria);

-- ============================================================================
-- TABLA: claves
-- ============================================================================

ALTER TABLE simi.claves
ADD CONSTRAINT uq_clave
UNIQUE (clave);

-- ============================================================================
-- TABLA: proveedores
-- ============================================================================

ALTER TABLE simi.proveedores
ADD CONSTRAINT uq_proveedor_rfc
UNIQUE (rfc);

ALTER TABLE simi.proveedores
ADD CONSTRAINT uq_proveedor_razon_social
UNIQUE (razon_social);

ALTER TABLE simi.proveedores
ADD CONSTRAINT chk_rfc_formato
CHECK (
    rfc ~ '^([A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}|[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3})$'
);

-- ============================================================================
-- TABLA: procedimientos
-- ============================================================================

ALTER TABLE simi.procedimientos
ADD CONSTRAINT uq_numero_procedimiento
UNIQUE (numero_procedimiento);

-- ============================================================================
-- TABLA: procedimiento_claves
-- ============================================================================

ALTER TABLE simi.procedimiento_claves
ADD CONSTRAINT uq_procedimiento_clave
UNIQUE (
    id_procedimiento,
    id_clave
);

ALTER TABLE simi.procedimiento_claves
ADD CONSTRAINT chk_cantidad_requerida
CHECK (
    cantidad_requerida > 0
);

-- ============================================================================
-- TABLA: propuestas
-- ============================================================================

ALTER TABLE simi.propuestas
ADD CONSTRAINT uq_propuesta
UNIQUE (
    id_procedimiento_clave,
    id_proveedor,
    tipo_propuesta
);

ALTER TABLE simi.propuestas
ADD CONSTRAINT chk_tipo_propuesta
CHECK (
    tipo_propuesta IN (
        'INICIAL',
        'SUBASTA'
    )
);

ALTER TABLE simi.propuestas
ADD CONSTRAINT chk_cantidad_ofertada
CHECK (
    cantidad_ofertada > 0
);

ALTER TABLE simi.propuestas
ADD CONSTRAINT chk_precio_unitario
CHECK (
    precio_unitario > 0
);

-- ============================================================================
-- TABLA: evaluaciones_tecnicas
-- ============================================================================

ALTER TABLE simi.evaluaciones_tecnicas
ADD CONSTRAINT uq_evaluacion_tecnica
UNIQUE (
    id_procedimiento,
    id_clave,
    id_proveedor
);

ALTER TABLE simi.evaluaciones_tecnicas
ADD CONSTRAINT chk_resultado_evaluacion
CHECK (
    resultado IN (
        'POSITIVA',
        'NEGATIVA'
    )
);

-- ============================================================================
-- TABLA: adjudicaciones
-- ============================================================================

ALTER TABLE simi.adjudicaciones
ADD CONSTRAINT uq_adjudicacion
UNIQUE (
    id_procedimiento,
    id_clave,
    id_proveedor
);

ALTER TABLE simi.adjudicaciones
ADD CONSTRAINT chk_cantidad_adjudicada
CHECK (
    cantidad_adjudicada > 0
);

ALTER TABLE simi.adjudicaciones
ADD CONSTRAINT chk_porcentaje_adjudicado
CHECK (
    porcentaje_adjudicado > 0
    AND porcentaje_adjudicado <= 100
);

ALTER TABLE simi.adjudicaciones
ADD CONSTRAINT chk_precio_unitario_adjudicado
CHECK (
    precio_unitario_adjudicado > 0
);

-- ============================================================================
-- TABLA: adjudicaciones_historicas
-- Histórico externo de adjudicaciones.
-- No depende de la tabla procedimientos.
-- Conserva el número de procedimiento como texto histórico.
-- ============================================================================

ALTER TABLE simi.adjudicaciones_historicas
ADD CONSTRAINT uq_adjudicacion_historica
UNIQUE (
    numero_procedimiento,
    id_clave,
    id_proveedor
);

ALTER TABLE simi.adjudicaciones_historicas
ADD CONSTRAINT chk_hist_cantidad
CHECK (
    cantidad_adjudicada IS NULL
    OR cantidad_adjudicada > 0
);

ALTER TABLE simi.adjudicaciones_historicas
ADD CONSTRAINT chk_hist_porcentaje
CHECK (
    porcentaje_adjudicado IS NULL
    OR (
        porcentaje_adjudicado > 0
        AND porcentaje_adjudicado <= 100
    )
);

ALTER TABLE simi.adjudicaciones_historicas
ADD CONSTRAINT chk_hist_precio
CHECK (
    precio_unitario_adjudicado > 0
);

-- ============================================================================
-- TABLA: procedimiento_fases
-- ============================================================================

ALTER TABLE simi.procedimiento_fases
ADD CONSTRAINT chk_fase
CHECK (
    fase IN (
        'PROPUESTAS_RECIBIDAS',
        'EVALUADO',
        'MEJOR_OFERTA_RECIBIDA',
        'ADJUDICADO',
        'NO_ADJUDICADO',
        'CANCELADO',
        'SUSPENDIDO',
        'MODIFICADO',
        'DESIERTO'
    )
);

COMMIT;