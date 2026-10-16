-- =====================================================================
-- 02_funciones_triggers.sql — Triggers de EncuentraU v2.0
-- =====================================================================
--
-- Un TRIGGER es una función que PostgreSQL ejecuta sola cuando ocurre un
-- INSERT, UPDATE o DELETE. Aquí se usan para cuatro cosas:
--
--   1. Mantener updated_at al día.
--   2. Hacer cumplir reglas del negocio dentro de la base de datos
--      (estados válidos, límites de reclamaciones), aunque la aplicación
--      tenga un bug: defensa en profundidad.
--   3. Marcar automáticamente cuentas con demasiadas reclamaciones rechazadas.
--   4. Registrar en la tabla auditoria TODOS los cambios de las tablas
--      importantes: quién, cuándo, desde qué IP, qué valores había antes y
--      qué valores quedaron después.
--
-- Los mensajes de error de las reglas del negocio usan ERRCODE 'P0001' y
-- están escritos para el usuario final: la aplicación los muestra tal cual.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Utilidad: leer un parámetro del negocio
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_parametro(p_clave TEXT) RETURNS INTEGER
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_valor INTEGER;
BEGIN
    SELECT valor INTO v_valor FROM parametros WHERE clave = p_clave;
    IF v_valor IS NULL THEN
        RAISE EXCEPTION 'Parámetro de configuración inexistente: %', p_clave;
    END IF;
    RETURN v_valor;
END;
$$;


-- ---------------------------------------------------------------------
-- 1. updated_at automático
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_actualizar_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_categorias_updated_at BEFORE UPDATE ON categorias
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();
CREATE TRIGGER trg_ubicaciones_updated_at BEFORE UPDATE ON ubicaciones
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();
CREATE TRIGGER trg_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();
CREATE TRIGGER trg_objetos_updated_at BEFORE UPDATE ON objetos
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();
CREATE TRIGGER trg_solicitudes_updated_at BEFORE UPDATE ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();
CREATE TRIGGER trg_parametros_updated_at BEFORE UPDATE ON parametros
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();


-- ---------------------------------------------------------------------
-- 2a. Estados de un reporte: solo transiciones permitidas
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_validar_estado_objeto() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Todo reporte nace en el estado inicial de su tipo
        -- (perdido -> buscando, encontrado -> pendiente_entrega).
        IF NOT EXISTS (
            SELECT 1 FROM estados_objeto
            WHERE tipo = NEW.tipo AND codigo = NEW.estado AND es_inicial
        ) THEN
            RAISE EXCEPTION 'Un reporte nuevo no puede empezar en el estado "%"', NEW.estado
                USING ERRCODE = 'P0001';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.tipo <> OLD.tipo THEN
        RAISE EXCEPTION 'No se puede cambiar el tipo de un reporte' USING ERRCODE = 'P0001';
    END IF;
    IF NEW.usuario_id <> OLD.usuario_id THEN
        RAISE EXCEPTION 'No se puede cambiar quién hizo el reporte' USING ERRCODE = 'P0001';
    END IF;

    IF NEW.estado <> OLD.estado AND NOT EXISTS (
        SELECT 1 FROM transiciones_objeto
        WHERE tipo = NEW.tipo AND estado_origen = OLD.estado AND estado_destino = NEW.estado
    ) THEN
        RAISE EXCEPTION 'Cambio de estado no permitido: de "%" a "%"', OLD.estado, NEW.estado
            USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_objetos_validar_estado BEFORE INSERT OR UPDATE ON objetos
    FOR EACH ROW EXECUTE FUNCTION fn_validar_estado_objeto();


-- ---------------------------------------------------------------------
-- 2b. Nueva reclamación: reglas contra el abuso
-- ---------------------------------------------------------------------
-- Concurrencia: se bloquean las filas en un orden fijo (primero el objeto,
-- después el usuario). Todos los procedimientos de 03_procedimientos.sql
-- bloquean también primero el objeto, así nunca se forma un ciclo de
-- esperas entre transacciones (deadlock).
CREATE FUNCTION fn_validar_nueva_solicitud() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto   objetos%ROWTYPE;
    v_usuario  usuarios%ROWTYPE;
    v_reporte  objetos%ROWTYPE;
    v_abiertas INTEGER;
BEGIN
    SELECT * INTO v_objeto FROM objetos WHERE id = NEW.objeto_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El objeto no existe' USING ERRCODE = 'P0001';
    END IF;

    -- Bloquea la fila del estudiante: si envía dos reclamaciones al mismo
    -- tiempo, la segunda espera a la primera y cuenta bien el límite.
    SELECT * INTO v_usuario FROM usuarios WHERE id = NEW.solicitante_id FOR UPDATE;

    IF v_usuario.rol <> 'estudiante' THEN
        RAISE EXCEPTION 'Solo los estudiantes pueden reclamar objetos' USING ERRCODE = 'P0001';
    END IF;
    IF v_usuario.correo_verificado_en IS NULL THEN
        RAISE EXCEPTION 'Debes verificar tu correo institucional antes de reclamar' USING ERRCODE = 'P0001';
    END IF;
    IF v_usuario.marcado_revision THEN
        RAISE EXCEPTION 'Tu cuenta está en revisión por reclamaciones rechazadas. Comunícate con la oficina'
            USING ERRCODE = 'P0001';
    END IF;

    IF v_objeto.tipo <> 'encontrado' OR v_objeto.estado NOT IN ('en_oficina', 'reservado') THEN
        RAISE EXCEPTION 'Este objeto no está disponible para reclamar' USING ERRCODE = 'P0001';
    END IF;
    IF v_objeto.usuario_id = NEW.solicitante_id THEN
        RAISE EXCEPTION 'No puedes reclamar un objeto que tú mismo reportaste como encontrado'
            USING ERRCODE = 'P0001';
    END IF;

    SELECT count(*) INTO v_abiertas
    FROM solicitudes s
    JOIN estados_solicitud e ON e.codigo = s.estado
    WHERE s.solicitante_id = NEW.solicitante_id AND e.es_abierta;
    IF v_abiertas >= fn_parametro('max_solicitudes_abiertas') THEN
        RAISE EXCEPTION 'Ya tienes % reclamaciones abiertas, que es el máximo permitido', v_abiertas
            USING ERRCODE = 'P0001';
    END IF;

    IF NEW.reporte_perdida_id IS NOT NULL THEN
        SELECT * INTO v_reporte FROM objetos WHERE id = NEW.reporte_perdida_id;
        IF NOT FOUND OR v_reporte.tipo <> 'perdido' OR v_reporte.usuario_id <> NEW.solicitante_id THEN
            RAISE EXCEPTION 'El reporte de pérdida indicado no es tuyo' USING ERRCODE = 'P0001';
        END IF;
    END IF;

    -- Deny by default: el estado inicial lo decide la base de datos.
    NEW.estado := 'pendiente';
    NEW.revisado_por_id := NULL;
    NEW.revisado_en := NULL;
    NEW.preaprobada_en := NULL;
    NEW.vence_en := NULL;
    NEW.codigo_hash := NULL;
    NEW.codigo_generado_en := NULL;
    NEW.intentos_codigo := 0;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_solicitudes_validar_nueva BEFORE INSERT ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION fn_validar_nueva_solicitud();


-- ---------------------------------------------------------------------
-- 3. Marcar cuentas con demasiadas reclamaciones rechazadas
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_marcar_cuenta_por_rechazos() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_rechazos INTEGER;
BEGIN
    IF NEW.estado IS DISTINCT FROM OLD.estado AND EXISTS (
        SELECT 1 FROM estados_solicitud WHERE codigo = NEW.estado AND cuenta_como_rechazo
    ) THEN
        SELECT count(*) INTO v_rechazos
        FROM solicitudes s
        JOIN estados_solicitud e ON e.codigo = s.estado
        WHERE s.solicitante_id = NEW.solicitante_id AND e.cuenta_como_rechazo;

        IF v_rechazos >= fn_parametro('max_rechazos') THEN
            UPDATE usuarios
            SET marcado_revision = TRUE,
                motivo_revision = format('%s reclamaciones rechazadas', v_rechazos)
            WHERE id = NEW.solicitante_id AND NOT marcado_revision;
        END IF;
    END IF;
    RETURN NULL;  -- en un trigger AFTER el valor de retorno se ignora
END;
$$;

CREATE TRIGGER trg_solicitudes_marcar_rechazos AFTER UPDATE OF estado ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION fn_marcar_cuenta_por_rechazos();


-- ---------------------------------------------------------------------
-- 4. Auditoría de todos los cambios
-- ---------------------------------------------------------------------
-- SECURITY DEFINER: la función se ejecuta con los permisos de su dueño
-- (el usuario de migraciones), no con los de la aplicación. Así la
-- aplicación puede generar filas de auditoría sin tener permiso de INSERT
-- sobre la tabla auditoria (y mucho menos de UPDATE o DELETE).
-- "SET search_path" fijo es obligatorio en funciones SECURITY DEFINER para
-- que nadie pueda suplantar tablas creando objetos con el mismo nombre.
--
-- ¿Quién hizo el cambio? La aplicación ejecuta, al inicio de cada
-- transacción:  SELECT set_config('app.usuario_id', '<id>', true)
-- (ver app/auditoria_contexto.py). El "true" hace que el valor dure solo
-- esa transacción.
--
-- Nunca se copian a la auditoría los valores de columnas secretas
-- (hashes de contraseña, de tokens o de códigos de retiro). Si cambian,
-- sí queda registrado QUE cambiaron (en campos_modificados).
CREATE FUNCTION fn_auditoria() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    c_secretos   CONSTANT TEXT[] := ARRAY['password_hash', 'token_hash', 'codigo_hash'];
    c_tecnicos   CONSTANT TEXT[] := ARRAY['updated_at', 'version'];
    v_anterior   JSONB;
    v_nuevo      JSONB;
    v_campos     TEXT[];
    v_usuario_id INTEGER;
    v_ip         INET;
BEGIN
    v_usuario_id := NULLIF(current_setting('app.usuario_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.ip', true), '')::INET;

    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_anterior := to_jsonb(OLD);
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_nuevo := to_jsonb(NEW);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT array_agg(n.key ORDER BY n.key) INTO v_campos
        FROM jsonb_each(v_nuevo) AS n
        WHERE n.value IS DISTINCT FROM v_anterior -> n.key
          AND NOT (n.key = ANY (c_tecnicos));
        IF v_campos IS NULL THEN
            RETURN NULL;  -- no cambió nada relevante: no se registra
        END IF;
    END IF;

    INSERT INTO auditoria (tabla, registro_id, operacion, usuario_id, ip,
                           datos_anteriores, datos_nuevos, campos_modificados)
    VALUES (
        TG_TABLE_NAME,
        COALESCE(v_nuevo ->> 'id', v_anterior ->> 'id')::BIGINT,
        TG_OP,
        v_usuario_id,
        v_ip,
        v_anterior - c_secretos,
        v_nuevo - c_secretos,
        v_campos
    );
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_auditoria_usuarios AFTER INSERT OR UPDATE OR DELETE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_tokens_usuario AFTER INSERT OR UPDATE OR DELETE ON tokens_usuario
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_objetos AFTER INSERT OR UPDATE OR DELETE ON objetos
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_solicitudes AFTER INSERT OR UPDATE OR DELETE ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_entregas AFTER INSERT OR UPDATE OR DELETE ON entregas
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_categorias AFTER INSERT OR UPDATE OR DELETE ON categorias
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_ubicaciones AFTER INSERT OR UPDATE OR DELETE ON ubicaciones
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
CREATE TRIGGER trg_auditoria_parametros AFTER INSERT OR UPDATE OR DELETE ON parametros
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();


-- La auditoría es de SOLO INSERCIÓN: nadie la modifica ni la borra.
-- (Además, la aplicación ni siquiera tiene permiso; esto protege también
-- contra errores del propio dueño de la base de datos.)
CREATE FUNCTION fn_auditoria_inmutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'La auditoría es de solo inserción: no se permite %', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER trg_auditoria_sin_modificar BEFORE UPDATE OR DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_inmutable();
CREATE TRIGGER trg_auditoria_sin_vaciar BEFORE TRUNCATE ON auditoria
    FOR EACH STATEMENT EXECUTE FUNCTION fn_auditoria_inmutable();
