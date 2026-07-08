BEGIN;

CREATE SCHEMA IF NOT EXISTS simi;
CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

CREATE TABLE IF NOT EXISTS simi.simi_roles (
    id_rol BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rol VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO simi.simi_roles (rol, descripcion)
VALUES
('ADMINISTRADOR_MAESTRO', 'Control total del sistema. Único autorizado para eliminar datos.'),
('ADMINISTRADOR', 'Puede cargar, validar y actualizar información.'),
('ANALISTA', 'Puede consultar información y ejecutar análisis.'),
('CONSULTA', 'Usuario de solo lectura.')
ON CONFLICT (rol) DO NOTHING;

CREATE TABLE IF NOT EXISTS simi.usuarios (
    id_usuario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre_completo VARCHAR(150) NOT NULL,
    password_hash TEXT NOT NULL,
    rol VARCHAR(50) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultimo_login TIMESTAMP,

    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (rol)
        REFERENCES simi.simi_roles (rol),

    CONSTRAINT chk_usuarios_email_formato
        CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$')
);

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON simi.usuarios (username);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON simi.usuarios (email);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON simi.usuarios (rol);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON simi.usuarios (activo);

CREATE TABLE IF NOT EXISTS simi.bitacora_seguridad (
    id_bitacora_seguridad BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario BIGINT,
    evento VARCHAR(100) NOT NULL,
    detalle TEXT,
    fecha_evento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bitacora_seguridad_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES simi.usuarios (id_usuario)
);

CREATE OR REPLACE FUNCTION simi.fn_simi_hash_password(p_password TEXT)
RETURNS TEXT AS $$
BEGIN
    IF p_password IS NULL OR LENGTH(TRIM(p_password)) < 8 THEN
        RAISE EXCEPTION 'La contraseña debe tener al menos 8 caracteres.';
    END IF;

    RETURN extensions.crypt(p_password, extensions.gen_salt('bf'));
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION simi.fn_simi_password_valido(
    p_password TEXT,
    p_password_hash TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_password IS NULL OR p_password_hash IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN extensions.crypt(p_password, p_password_hash) = p_password_hash;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION simi.fn_simi_set_context(
    p_id_usuario BIGINT,
    p_rol VARCHAR
)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('simi.user_id', COALESCE(p_id_usuario::TEXT, ''), FALSE);
    PERFORM set_config('simi.user_role', COALESCE(p_rol, ''), FALSE);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION simi.fn_simi_usuario_actual_id()
RETURNS BIGINT AS $$
DECLARE
    v_id_usuario TEXT;
BEGIN
    v_id_usuario := current_setting('simi.user_id', TRUE);

    IF v_id_usuario IS NULL OR v_id_usuario = '' THEN
        RETURN NULL;
    END IF;

    RETURN v_id_usuario::BIGINT;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION simi.fn_es_administrador_maestro()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_setting('simi.user_role', TRUE) = 'ADMINISTRADOR_MAESTRO';
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION simi.fn_simi_puede_administrar()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_setting('simi.user_role', TRUE) IN (
        'ADMINISTRADOR_MAESTRO',
        'ADMINISTRADOR'
    );
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION simi.fn_simi_puede_consultar()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_setting('simi.user_role', TRUE) IN (
        'ADMINISTRADOR_MAESTRO',
        'ADMINISTRADOR',
        'ANALISTA',
        'CONSULTA'
    );
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION simi.fn_simi_usuario_activo()
RETURNS BOOLEAN AS $$
DECLARE
    v_id_usuario BIGINT;
BEGIN
    v_id_usuario := simi.fn_simi_usuario_actual_id();

    IF v_id_usuario IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM simi.usuarios u
        WHERE u.id_usuario = v_id_usuario
          AND u.activo = TRUE
    );
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION simi.fn_simi_login(
    p_email TEXT,
    p_password TEXT
)
RETURNS TABLE (
    id_usuario BIGINT,
    username VARCHAR,
    email VARCHAR,
    nombre_completo VARCHAR,
    rol VARCHAR,
    login_correcto BOOLEAN
) AS $$
DECLARE
    v_usuario RECORD;
BEGIN
    SELECT u.*
    INTO v_usuario
    FROM simi.usuarios u
    WHERE LOWER(u.email) = LOWER(TRIM(p_email))
      AND u.activo = TRUE;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, FALSE;
        RETURN;
    END IF;

    IF simi.fn_simi_password_valido(p_password, v_usuario.password_hash) THEN
        UPDATE simi.usuarios
        SET fecha_ultimo_login = CURRENT_TIMESTAMP,
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE usuarios.id_usuario = v_usuario.id_usuario;

        PERFORM simi.fn_simi_set_context(v_usuario.id_usuario, v_usuario.rol);

        INSERT INTO simi.bitacora_seguridad (id_usuario, evento, detalle)
        VALUES (v_usuario.id_usuario, 'LOGIN_CORRECTO', 'Inicio de sesión correcto.');

        RETURN QUERY
        SELECT
            v_usuario.id_usuario,
            v_usuario.username,
            v_usuario.email,
            v_usuario.nombre_completo,
            v_usuario.rol,
            TRUE;
    ELSE
        INSERT INTO simi.bitacora_seguridad (id_usuario, evento, detalle)
        VALUES (v_usuario.id_usuario, 'LOGIN_FALLIDO', 'Contraseña incorrecta.');

        RETURN QUERY
        SELECT NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION simi.fn_simi_crear_usuario(
    p_username VARCHAR,
    p_email VARCHAR,
    p_nombre_completo VARCHAR,
    p_password TEXT,
    p_rol VARCHAR
)
RETURNS BIGINT AS $$
DECLARE
    v_id_usuario BIGINT;
    v_total_usuarios BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_total_usuarios
    FROM simi.usuarios;

    IF v_total_usuarios > 0 AND NOT simi.fn_es_administrador_maestro() THEN
        RAISE EXCEPTION 'Solo el ADMINISTRADOR_MAESTRO puede crear usuarios.';
    END IF;

    IF p_rol NOT IN (
        'ADMINISTRADOR_MAESTRO',
        'ADMINISTRADOR',
        'ANALISTA',
        'CONSULTA'
    ) THEN
        RAISE EXCEPTION 'Rol no válido para SIMI.';
    END IF;

    INSERT INTO simi.usuarios (
        username,
        email,
        nombre_completo,
        password_hash,
        rol
    )
    VALUES (
        LOWER(TRIM(p_username)),
        LOWER(TRIM(p_email)),
        TRIM(p_nombre_completo),
        simi.fn_simi_hash_password(p_password),
        p_rol
    )
    RETURNING id_usuario INTO v_id_usuario;

    INSERT INTO simi.bitacora_seguridad (id_usuario, evento, detalle)
    VALUES (
        v_id_usuario,
        'USUARIO_CREADO',
        'Usuario creado en SIMI.'
    );

    RETURN v_id_usuario;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION simi.fn_usuarios_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_usuarios_fecha_actualizacion ON simi.usuarios;

CREATE TRIGGER trg_usuarios_fecha_actualizacion
BEFORE UPDATE ON simi.usuarios
FOR EACH ROW
EXECUTE FUNCTION simi.fn_usuarios_fecha_actualizacion();

ALTER TABLE simi.simi_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE simi.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE simi.bitacora_seguridad ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_simi_roles_select ON simi.simi_roles;
CREATE POLICY pol_simi_roles_select
ON simi.simi_roles
FOR SELECT
USING (simi.fn_simi_puede_consultar() OR simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_simi_roles_write ON simi.simi_roles;
CREATE POLICY pol_simi_roles_write
ON simi.simi_roles
FOR ALL
USING (simi.fn_es_administrador_maestro())
WITH CHECK (simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_usuarios_select ON simi.usuarios;
CREATE POLICY pol_usuarios_select
ON simi.usuarios
FOR SELECT
USING (
    simi.fn_es_administrador_maestro()
    OR id_usuario = simi.fn_simi_usuario_actual_id()
);

DROP POLICY IF EXISTS pol_usuarios_insert ON simi.usuarios;
CREATE POLICY pol_usuarios_insert
ON simi.usuarios
FOR INSERT
WITH CHECK (simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_usuarios_update ON simi.usuarios;
CREATE POLICY pol_usuarios_update
ON simi.usuarios
FOR UPDATE
USING (simi.fn_es_administrador_maestro())
WITH CHECK (simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_usuarios_delete ON simi.usuarios;
CREATE POLICY pol_usuarios_delete
ON simi.usuarios
FOR DELETE
USING (simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_bitacora_seguridad_select ON simi.bitacora_seguridad;
CREATE POLICY pol_bitacora_seguridad_select
ON simi.bitacora_seguridad
FOR SELECT
USING (simi.fn_es_administrador_maestro());

DROP POLICY IF EXISTS pol_bitacora_seguridad_insert ON simi.bitacora_seguridad;
CREATE POLICY pol_bitacora_seguridad_insert
ON simi.bitacora_seguridad
FOR INSERT
WITH CHECK (TRUE);

DROP POLICY IF EXISTS pol_bitacora_seguridad_delete ON simi.bitacora_seguridad;
CREATE POLICY pol_bitacora_seguridad_delete
ON simi.bitacora_seguridad
FOR DELETE
USING (simi.fn_es_administrador_maestro());

DO $$
DECLARE
    v_tabla TEXT;
    v_tablas TEXT[] := ARRAY[
        'procedimientos',
        'cat_categorias_clave',
        'claves',
        'procedimiento_claves',
        'proveedores',
        'paises_origen',
        'propuestas',
        'evaluaciones_tecnicas',
        'adjudicaciones',
        'adjudicaciones_historicas',
        'procedimiento_fases'
    ];
BEGIN
    FOREACH v_tabla IN ARRAY v_tablas LOOP
        IF EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'simi'
              AND table_name = v_tabla
        ) THEN
            EXECUTE FORMAT('ALTER TABLE simi.%I ENABLE ROW LEVEL SECURITY', v_tabla);

            EXECUTE FORMAT('DROP POLICY IF EXISTS pol_%I_select ON simi.%I', v_tabla, v_tabla);
            EXECUTE FORMAT(
                'CREATE POLICY pol_%I_select ON simi.%I FOR SELECT USING (simi.fn_simi_usuario_activo() AND simi.fn_simi_puede_consultar())',
                v_tabla,
                v_tabla
            );

            EXECUTE FORMAT('DROP POLICY IF EXISTS pol_%I_insert ON simi.%I', v_tabla, v_tabla);
            EXECUTE FORMAT(
                'CREATE POLICY pol_%I_insert ON simi.%I FOR INSERT WITH CHECK (simi.fn_simi_usuario_activo() AND simi.fn_simi_puede_administrar())',
                v_tabla,
                v_tabla
            );

            EXECUTE FORMAT('DROP POLICY IF EXISTS pol_%I_update ON simi.%I', v_tabla, v_tabla);
            EXECUTE FORMAT(
                'CREATE POLICY pol_%I_update ON simi.%I FOR UPDATE USING (simi.fn_simi_usuario_activo() AND simi.fn_simi_puede_administrar()) WITH CHECK (simi.fn_simi_usuario_activo() AND simi.fn_simi_puede_administrar())',
                v_tabla,
                v_tabla
            );

            EXECUTE FORMAT('DROP POLICY IF EXISTS pol_%I_delete ON simi.%I', v_tabla, v_tabla);
            EXECUTE FORMAT(
                'CREATE POLICY pol_%I_delete ON simi.%I FOR DELETE USING (simi.fn_simi_usuario_activo() AND simi.fn_es_administrador_maestro())',
                v_tabla,
                v_tabla
            );
        END IF;
    END LOOP;
END;
$$;

COMMIT;