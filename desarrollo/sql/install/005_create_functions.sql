-- ============================================================
-- SIMI
-- Sprint 0.5
-- Archivo: 005_create_functions.sql
-- Descripción: Funciones reutilizables para cálculos y consultas
-- ============================================================

-- ============================================================
-- 1. Calcular monto
-- ============================================================

CREATE OR REPLACE FUNCTION fn_calcular_monto(
    p_cantidad NUMERIC,
    p_precio_unitario NUMERIC
)
RETURNS NUMERIC AS $$
BEGIN
    RETURN COALESCE(p_cantidad, 0) * COALESCE(p_precio_unitario, 0);
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 2. Calcular porcentaje adjudicado
-- ============================================================

CREATE OR REPLACE FUNCTION fn_calcular_porcentaje(
    p_cantidad_adjudicada NUMERIC,
    p_cantidad_requerida NUMERIC
)
RETURNS NUMERIC AS $$
BEGIN
    IF p_cantidad_requerida IS NULL OR p_cantidad_requerida = 0 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND((p_cantidad_adjudicada / p_cantidad_requerida) * 100, 2);
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 3. Obtener mejor precio por procedimiento y clave
-- ============================================================

CREATE OR REPLACE FUNCTION fn_obtener_mejor_precio(
    p_id_procedimiento BIGINT,
    p_id_clave BIGINT
)
RETURNS NUMERIC AS $$
DECLARE
    v_mejor_precio NUMERIC;
BEGIN
    SELECT MIN(p.precio_unitario)
    INTO v_mejor_precio
    FROM propuestas p
    INNER JOIN procedimiento_claves pc
        ON pc.id_procedimiento_clave = p.id_procedimiento_clave
    WHERE pc.id_procedimiento = p_id_procedimiento
      AND pc.id_clave = p_id_clave;

    RETURN v_mejor_precio;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 4. Obtener peor precio por procedimiento y clave
-- ============================================================

CREATE OR REPLACE FUNCTION fn_obtener_peor_precio(
    p_id_procedimiento BIGINT,
    p_id_clave BIGINT
)
RETURNS NUMERIC AS $$
DECLARE
    v_peor_precio NUMERIC;
BEGIN
    SELECT MAX(p.precio_unitario)
    INTO v_peor_precio
    FROM propuestas p
    INNER JOIN procedimiento_claves pc
        ON pc.id_procedimiento_clave = p.id_procedimiento_clave
    WHERE pc.id_procedimiento = p_id_procedimiento
      AND pc.id_clave = p_id_clave;

    RETURN v_peor_precio;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 5. Obtener precio promedio por procedimiento y clave
-- ============================================================

CREATE OR REPLACE FUNCTION fn_obtener_precio_promedio(
    p_id_procedimiento BIGINT,
    p_id_clave BIGINT
)
RETURNS NUMERIC AS $$
DECLARE
    v_precio_promedio NUMERIC;
BEGIN
    SELECT ROUND(AVG(p.precio_unitario), 2)
    INTO v_precio_promedio
    FROM propuestas p
    INNER JOIN procedimiento_claves pc
        ON pc.id_procedimiento_clave = p.id_procedimiento_clave
    WHERE pc.id_procedimiento = p_id_procedimiento
      AND pc.id_clave = p_id_clave;

    RETURN v_precio_promedio;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 6. Contar proveedores participantes por procedimiento
-- ============================================================

CREATE OR REPLACE FUNCTION fn_contar_proveedores_procedimiento(
    p_id_procedimiento BIGINT
)
RETURNS BIGINT AS $$
DECLARE
    v_total BIGINT;
BEGIN
    SELECT COUNT(DISTINCT p.id_proveedor)
    INTO v_total
    FROM propuestas p
    INNER JOIN procedimiento_claves pc
        ON pc.id_procedimiento_clave = p.id_procedimiento_clave
    WHERE pc.id_procedimiento = p_id_procedimiento;

    RETURN COALESCE(v_total, 0);
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 7. Contar claves por procedimiento
-- ============================================================

CREATE OR REPLACE FUNCTION fn_contar_claves_procedimiento(
    p_id_procedimiento BIGINT
)
RETURNS BIGINT AS $$
DECLARE
    v_total BIGINT;
BEGIN
    SELECT COUNT(DISTINCT pc.id_clave)
    INTO v_total
    FROM procedimiento_claves pc
    WHERE pc.id_procedimiento = p_id_procedimiento;

    RETURN COALESCE(v_total, 0);
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 8. Calcular monto de adjudicación actual
-- ============================================================

CREATE OR REPLACE FUNCTION fn_monto_adjudicacion(
    p_id_adjudicacion BIGINT
)
RETURNS NUMERIC AS $$
DECLARE
    v_monto NUMERIC;
BEGIN
    SELECT fn_calcular_monto(
        a.cantidad_adjudicada,
        a.precio_unitario_adjudicado
    )
    INTO v_monto
    FROM adjudicaciones a
    WHERE a.id_adjudicacion = p_id_adjudicacion;

    RETURN v_monto;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 9. Calcular monto de adjudicación histórica
-- Estructura correcta:
-- adjudicaciones_historicas usa numero_procedimiento
-- NO usa id_procedimiento
-- ============================================================

CREATE OR REPLACE FUNCTION fn_monto_adjudicacion_historica(
    p_id_adjudicacion_historica BIGINT
)
RETURNS NUMERIC AS $$
DECLARE
    v_monto NUMERIC;
BEGIN
    SELECT fn_calcular_monto(
        ah.cantidad_adjudicada,
        ah.precio_unitario_adjudicado
    )
    INTO v_monto
    FROM adjudicaciones_historicas ah
    WHERE ah.id_adjudicacion_historica = p_id_adjudicacion_historica;

    RETURN v_monto;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- FIN DEL ARCHIVO 005_create_functions.sql
-- ============================================================