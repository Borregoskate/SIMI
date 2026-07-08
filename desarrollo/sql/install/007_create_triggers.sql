-- ============================================================
-- SIMI
-- Archivo: 007_create_triggers.sql
-- Objetivo: Triggers y funciones automáticas de control
-- ============================================================

-- ============================================================
-- 1. FUNCIÓN: Validar Administrador Maestro
-- ============================================================

CREATE OR REPLACE FUNCTION fn_es_administrador_maestro()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN
        current_setting('simi.user_role', true) = 'ADMINISTRADOR_MAESTRO'
        OR pg_has_role(current_user, 'simi_admin', 'member');
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 2. FUNCIÓN: Bloquear eliminaciones no autorizadas
-- ============================================================

CREATE OR REPLACE FUNCTION fn_bloquear_delete_no_admin()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT fn_es_administrador_maestro() THEN
        RAISE EXCEPTION
        'Operación no autorizada. Solo el Administrador Maestro puede eliminar registros críticos.';
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 3. FUNCIÓN: Normalizar RFC de proveedores
-- ============================================================

CREATE OR REPLACE FUNCTION fn_normalizar_rfc_proveedor()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rfc IS NOT NULL THEN
        NEW.rfc := UPPER(TRIM(NEW.rfc));
    END IF;

    IF NEW.razon_social IS NOT NULL THEN
        NEW.razon_social := TRIM(NEW.razon_social);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_normalizar_rfc_proveedor ON proveedores;

CREATE TRIGGER trg_normalizar_rfc_proveedor
BEFORE INSERT OR UPDATE ON proveedores
FOR EACH ROW
EXECUTE FUNCTION fn_normalizar_rfc_proveedor();


-- ============================================================
-- 4. FUNCIÓN: Fecha automática en procedimientos
-- ============================================================

CREATE OR REPLACE FUNCTION fn_fecha_creacion_procedimiento()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fecha_creacion IS NULL THEN
        NEW.fecha_creacion := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_fecha_creacion_procedimiento ON procedimientos;

CREATE TRIGGER trg_fecha_creacion_procedimiento
BEFORE INSERT ON procedimientos
FOR EACH ROW
EXECUTE FUNCTION fn_fecha_creacion_procedimiento();


-- ============================================================
-- 5. FUNCIÓN: Fecha automática en propuestas
-- ============================================================

CREATE OR REPLACE FUNCTION fn_fecha_registro_propuesta()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fecha_registro IS NULL THEN
        NEW.fecha_registro := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_fecha_registro_propuesta ON propuestas;

CREATE TRIGGER trg_fecha_registro_propuesta
BEFORE INSERT ON propuestas
FOR EACH ROW
EXECUTE FUNCTION fn_fecha_registro_propuesta();


-- ============================================================
-- 6. FUNCIÓN: Fecha automática en procedimiento_fases
-- ============================================================

CREATE OR REPLACE FUNCTION fn_fecha_procedimiento_fase()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fecha IS NULL THEN
        NEW.fecha := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_fecha_procedimiento_fase ON procedimiento_fases;

CREATE TRIGGER trg_fecha_procedimiento_fase
BEFORE INSERT ON procedimiento_fases
FOR EACH ROW
EXECUTE FUNCTION fn_fecha_procedimiento_fase();


-- ============================================================
-- 7. FUNCIÓN AUXILIAR: Registrar fase si no existe
-- ============================================================

CREATE OR REPLACE FUNCTION fn_registrar_fase_si_no_existe(
    p_id_procedimiento BIGINT,
    p_fase VARCHAR
)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM procedimiento_fases
        WHERE id_procedimiento = p_id_procedimiento
          AND fase = p_fase
    ) THEN
        INSERT INTO procedimiento_fases (
            id_procedimiento,
            fase,
            fecha
        )
        VALUES (
            p_id_procedimiento,
            p_fase,
            CURRENT_TIMESTAMP
        );
    END IF;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 8. FUNCIÓN: Validar propuestas
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validar_propuesta()
RETURNS TRIGGER AS $$
DECLARE
    v_id_procedimiento BIGINT;
    v_id_clave BIGINT;
BEGIN
    SELECT
        pc.id_procedimiento,
        pc.id_clave
    INTO
        v_id_procedimiento,
        v_id_clave
    FROM procedimiento_claves pc
    WHERE pc.id_procedimiento_clave = NEW.id_procedimiento_clave;

    IF v_id_procedimiento IS NULL THEN
        RAISE EXCEPTION
        'La propuesta no pertenece a una clave válida del procedimiento.';
    END IF;

    IF NEW.tipo_propuesta NOT IN ('INICIAL', 'SUBASTA') THEN
        RAISE EXCEPTION
        'Tipo de propuesta inválido. Valores permitidos: INICIAL, SUBASTA.';
    END IF;

    IF NEW.cantidad_ofertada IS NULL OR NEW.cantidad_ofertada < 0 THEN
        RAISE EXCEPTION
        'La cantidad ofertada no puede ser negativa ni nula.';
    END IF;

    IF NEW.precio_unitario IS NULL OR NEW.precio_unitario <= 0 THEN
        RAISE EXCEPTION
        'El precio unitario debe ser mayor a cero.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM propuestas p
        WHERE p.id_procedimiento_clave = NEW.id_procedimiento_clave
          AND p.id_proveedor = NEW.id_proveedor
          AND p.tipo_propuesta = NEW.tipo_propuesta
          AND (
                TG_OP = 'INSERT'
                OR p.id_propuesta <> NEW.id_propuesta
              )
    ) THEN
        RAISE EXCEPTION
        'Ya existe una propuesta del mismo tipo para este proveedor y esta clave del procedimiento.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_validar_propuesta ON propuestas;

CREATE TRIGGER trg_validar_propuesta
BEFORE INSERT OR UPDATE ON propuestas
FOR EACH ROW
EXECUTE FUNCTION fn_validar_propuesta();


-- ============================================================
-- 9. FUNCIÓN: Registrar fase por propuesta
-- ============================================================

CREATE OR REPLACE FUNCTION fn_registrar_fase_por_propuesta()
RETURNS TRIGGER AS $$
DECLARE
    v_id_procedimiento BIGINT;
BEGIN
    SELECT pc.id_procedimiento
    INTO v_id_procedimiento
    FROM procedimiento_claves pc
    WHERE pc.id_procedimiento_clave = NEW.id_procedimiento_clave;

    IF NEW.tipo_propuesta = 'INICIAL' THEN
        PERFORM fn_registrar_fase_si_no_existe(
            v_id_procedimiento,
            'PROPUESTAS_RECIBIDAS'
        );
    END IF;

    IF NEW.tipo_propuesta = 'SUBASTA' THEN
        PERFORM fn_registrar_fase_si_no_existe(
            v_id_procedimiento,
            'MEJOR_OFERTA_RECIBIDA'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_registrar_fase_por_propuesta ON propuestas;

CREATE TRIGGER trg_registrar_fase_por_propuesta
AFTER INSERT ON propuestas
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_fase_por_propuesta();


-- ============================================================
-- 10. FUNCIÓN: Validar evaluación técnica
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validar_evaluacion_tecnica()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.resultado NOT IN ('POSITIVA', 'NEGATIVA') THEN
        RAISE EXCEPTION
        'Resultado técnico inválido. Valores permitidos: POSITIVA, NEGATIVA.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM procedimiento_claves pc
        WHERE pc.id_procedimiento = NEW.id_procedimiento
          AND pc.id_clave = NEW.id_clave
    ) THEN
        RAISE EXCEPTION
        'La clave evaluada no pertenece al procedimiento seleccionado.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_validar_evaluacion_tecnica ON evaluaciones_tecnicas;

CREATE TRIGGER trg_validar_evaluacion_tecnica
BEFORE INSERT OR UPDATE ON evaluaciones_tecnicas
FOR EACH ROW
EXECUTE FUNCTION fn_validar_evaluacion_tecnica();


-- ============================================================
-- 11. FUNCIÓN: Registrar fase por evaluación técnica
-- ============================================================

CREATE OR REPLACE FUNCTION fn_registrar_fase_por_evaluacion()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM fn_registrar_fase_si_no_existe(
        NEW.id_procedimiento,
        'EVALUADO'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_registrar_fase_por_evaluacion ON evaluaciones_tecnicas;

CREATE TRIGGER trg_registrar_fase_por_evaluacion
AFTER INSERT ON evaluaciones_tecnicas
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_fase_por_evaluacion();


-- ============================================================
-- 12. FUNCIÓN: Validar adjudicaciones
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validar_adjudicacion()
RETURNS TRIGGER AS $$
DECLARE
    v_porcentaje_total NUMERIC(5,2);
BEGIN
    IF NEW.cantidad_adjudicada IS NULL OR NEW.cantidad_adjudicada <= 0 THEN
        RAISE EXCEPTION
        'La cantidad adjudicada debe ser mayor a cero.';
    END IF;

    IF NEW.porcentaje_adjudicado IS NULL
       OR NEW.porcentaje_adjudicado <= 0
       OR NEW.porcentaje_adjudicado > 100 THEN
        RAISE EXCEPTION
        'El porcentaje adjudicado debe ser mayor a cero y menor o igual a 100.';
    END IF;

    IF NEW.precio_unitario_adjudicado IS NULL
       OR NEW.precio_unitario_adjudicado <= 0 THEN
        RAISE EXCEPTION
        'El precio unitario adjudicado debe ser mayor a cero.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM procedimiento_claves pc
        WHERE pc.id_procedimiento = NEW.id_procedimiento
          AND pc.id_clave = NEW.id_clave
    ) THEN
        RAISE EXCEPTION
        'La clave adjudicada no pertenece al procedimiento seleccionado.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM evaluaciones_tecnicas et
        WHERE et.id_procedimiento = NEW.id_procedimiento
          AND et.id_clave = NEW.id_clave
          AND et.id_proveedor = NEW.id_proveedor
          AND et.resultado = 'POSITIVA'
    ) THEN
        RAISE EXCEPTION
        'No se puede adjudicar. El proveedor no cuenta con evaluación técnica POSITIVA para esta clave.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM propuestas p
        INNER JOIN procedimiento_claves pc
            ON pc.id_procedimiento_clave = p.id_procedimiento_clave
        WHERE pc.id_procedimiento = NEW.id_procedimiento
          AND pc.id_clave = NEW.id_clave
          AND p.id_proveedor = NEW.id_proveedor
    ) THEN
        RAISE EXCEPTION
        'No se puede adjudicar. No existe propuesta registrada para este proveedor y esta clave.';
    END IF;

    SELECT COALESCE(SUM(a.porcentaje_adjudicado), 0)
    INTO v_porcentaje_total
    FROM adjudicaciones a
    WHERE a.id_procedimiento = NEW.id_procedimiento
      AND a.id_clave = NEW.id_clave
      AND (
            TG_OP = 'INSERT'
            OR a.id_adjudicacion <> NEW.id_adjudicacion
          );

    IF v_porcentaje_total + NEW.porcentaje_adjudicado > 100 THEN
        RAISE EXCEPTION
        'La suma de porcentajes adjudicados para esta clave no puede exceder el 100%%.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_validar_adjudicacion ON adjudicaciones;

CREATE TRIGGER trg_validar_adjudicacion
BEFORE INSERT OR UPDATE ON adjudicaciones
FOR EACH ROW
EXECUTE FUNCTION fn_validar_adjudicacion();


-- ============================================================
-- 13. FUNCIÓN: Registrar fase por adjudicación
-- ============================================================

CREATE OR REPLACE FUNCTION fn_registrar_fase_por_adjudicacion()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM fn_registrar_fase_si_no_existe(
        NEW.id_procedimiento,
        'ADJUDICADO'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_registrar_fase_por_adjudicacion ON adjudicaciones;

CREATE TRIGGER trg_registrar_fase_por_adjudicacion
AFTER INSERT ON adjudicaciones
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_fase_por_adjudicacion();


-- ============================================================
-- 14. FUNCIÓN: Validar adjudicaciones históricas
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validar_adjudicacion_historica()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.cantidad_adjudicada IS NULL OR NEW.cantidad_adjudicada <= 0 THEN
        RAISE EXCEPTION
        'La cantidad adjudicada histórica debe ser mayor a cero.';
    END IF;

    IF NEW.porcentaje_adjudicado IS NULL
       OR NEW.porcentaje_adjudicado <= 0
       OR NEW.porcentaje_adjudicado > 100 THEN
        RAISE EXCEPTION
        'El porcentaje adjudicado histórico debe ser mayor a cero y menor o igual a 100.';
    END IF;

    IF NEW.precio_unitario_adjudicado IS NULL
       OR NEW.precio_unitario_adjudicado <= 0 THEN
        RAISE EXCEPTION
        'El precio unitario adjudicado histórico debe ser mayor a cero.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_validar_adjudicacion_historica ON adjudicaciones_historicas;

CREATE TRIGGER trg_validar_adjudicacion_historica
BEFORE INSERT OR UPDATE ON adjudicaciones_historicas
FOR EACH ROW
EXECUTE FUNCTION fn_validar_adjudicacion_historica();


-- ============================================================
-- 15. TRIGGERS DE PROTECCIÓN CONTRA ELIMINACIÓN
-- ============================================================

DROP TRIGGER IF EXISTS trg_proteger_delete_propuestas ON propuestas;

CREATE TRIGGER trg_proteger_delete_propuestas
BEFORE DELETE ON propuestas
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_evaluaciones ON evaluaciones_tecnicas;

CREATE TRIGGER trg_proteger_delete_evaluaciones
BEFORE DELETE ON evaluaciones_tecnicas
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_adjudicaciones ON adjudicaciones;

CREATE TRIGGER trg_proteger_delete_adjudicaciones
BEFORE DELETE ON adjudicaciones
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_adjudicaciones_historicas ON adjudicaciones_historicas;

CREATE TRIGGER trg_proteger_delete_adjudicaciones_historicas
BEFORE DELETE ON adjudicaciones_historicas
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_procedimientos ON procedimientos;

CREATE TRIGGER trg_proteger_delete_procedimientos
BEFORE DELETE ON procedimientos
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_claves ON claves;

CREATE TRIGGER trg_proteger_delete_claves
BEFORE DELETE ON claves
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


DROP TRIGGER IF EXISTS trg_proteger_delete_proveedores ON proveedores;

CREATE TRIGGER trg_proteger_delete_proveedores
BEFORE DELETE ON proveedores
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_no_admin();


-- ============================================================
-- FIN DEL ARCHIVO 007_create_triggers.sql
-- ============================================================