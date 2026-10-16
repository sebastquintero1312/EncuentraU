-- =====================================================================
-- 03_procedimientos.sql — Procedimientos almacenados de EncuentraU v2.0
-- =====================================================================
--
-- Las operaciones que modifican VARIAS tablas a la vez viven aquí, dentro
-- de la base de datos, para garantizar las propiedades ACID:
--
--   Atomicidad:   todo el procedimiento corre en la transacción de la
--                 petición. Si algo falla (RAISE EXCEPTION), PostgreSQL
--                 deshace TODOS sus cambios: nunca queda un objeto marcado
--                 "entregado" sin su acta de entrega, ni al revés.
--   Consistencia: las restricciones (CHECK, FK, índices únicos) y los
--                 triggers se validan en cada UPDATE/INSERT del procedimiento.
--   Aislamiento:  SELECT ... FOR UPDATE bloquea la fila del objeto hasta el
--                 final de la transacción. Si dos encargados intentan
--                 entregar el mismo objeto al mismo tiempo, el segundo espera
--                 a que el primero termine y luego ve el estado ya cambiado.
--                 (Control de concurrencia PESIMISTA; el OPTIMISTA está en la
--                 columna "version".)
--   Durabilidad:  al hacer COMMIT, PostgreSQL escribe el cambio en el WAL
--                 (registro de escritura anticipada) antes de confirmar.
--
-- ORDEN DE BLOQUEO (evita deadlocks): siempre primero el objeto, después
-- sus solicitudes, después el usuario.
--
-- Convención: los procedimientos (CALL sp_...) devuelven un texto con el
-- resultado en el parámetro INOUT p_resultado. Un error de regla de negocio
-- se informa con RAISE EXCEPTION ... ERRCODE 'P0001' y un mensaje en español
-- apto para mostrarse al usuario.
-- =====================================================================


-- Defensa en profundidad: aunque Flask ya verificó el rol, la base de datos
-- vuelve a comprobar que quien ejecuta la acción es un encargado activo.
CREATE FUNCTION fn_exigir_encargado(p_usuario_id INTEGER) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM usuarios WHERE id = p_usuario_id AND rol = 'encargado' AND activo
    ) THEN
        RAISE EXCEPTION 'Solo un encargado activo puede realizar esta acción' USING ERRCODE = 'P0001';
    END IF;
END;
$$;


-- ---------------------------------------------------------------------
-- Recepción: el estudiante que encontró el objeto lo lleva a la oficina
-- y el encargado confirma que lo tiene en custodia. Solo desde ese momento
-- el objeto aparece en la búsqueda y se puede reclamar.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_registrar_recepcion(
    p_objeto_id     INTEGER,
    p_encargado_id  INTEGER,
    p_observaciones TEXT,
    INOUT p_resultado TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto objetos%ROWTYPE;
BEGIN
    PERFORM fn_exigir_encargado(p_encargado_id);

    SELECT * INTO v_objeto FROM objetos WHERE id = p_objeto_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El objeto no existe' USING ERRCODE = 'P0001';
    END IF;
    IF v_objeto.tipo <> 'encontrado' OR v_objeto.estado <> 'pendiente_entrega' THEN
        RAISE EXCEPTION 'Este objeto no está pendiente de recepción (estado actual: %)', v_objeto.estado
            USING ERRCODE = 'P0001';
    END IF;

    UPDATE objetos
    SET estado = 'en_oficina',
        recibido_por_id = p_encargado_id,
        recibido_en = now(),
        observaciones_custodia = COALESCE(NULLIF(btrim(p_observaciones), ''), observaciones_custodia),
        version = version + 1
    WHERE id = p_objeto_id;

    p_resultado := 'recibido';
END;
$$;


-- ---------------------------------------------------------------------
-- Pre-aprobación: el encargado comparó la descripción del estudiante con
-- los detalles privados y la considera correcta. El objeto queda reservado
-- y el estudiante tiene una ventana de tiempo para retirarlo en persona.
-- Las demás reclamaciones del mismo objeto quedan en espera (no se
-- rechazan): si el estudiante no se presenta, se pueden revisar.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_preaprobar_solicitud(
    p_solicitud_id INTEGER,
    p_encargado_id INTEGER,
    p_respuesta    TEXT,
    INOUT p_resultado TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto_id INTEGER;
    v_objeto    objetos%ROWTYPE;
    v_solicitud solicitudes%ROWTYPE;
BEGIN
    PERFORM fn_exigir_encargado(p_encargado_id);

    SELECT objeto_id INTO v_objeto_id FROM solicitudes WHERE id = p_solicitud_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La reclamación no existe' USING ERRCODE = 'P0001';
    END IF;

    -- Orden de bloqueo: primero el objeto, después la solicitud
    SELECT * INTO v_objeto FROM objetos WHERE id = v_objeto_id FOR UPDATE;
    SELECT * INTO v_solicitud FROM solicitudes WHERE id = p_solicitud_id FOR UPDATE;

    IF v_solicitud.estado <> 'pendiente' THEN
        RAISE EXCEPTION 'Esta reclamación ya fue revisada (estado: %)', v_solicitud.estado
            USING ERRCODE = 'P0001';
    END IF;
    IF v_objeto.estado = 'reservado' THEN
        RAISE EXCEPTION 'Ya hay otra reclamación pre-aprobada para este objeto. Recházala o espera a que venza antes de aprobar otra'
            USING ERRCODE = 'P0001';
    END IF;
    IF v_objeto.estado <> 'en_oficina' THEN
        RAISE EXCEPTION 'El objeto no está en custodia de la oficina (estado: %)', v_objeto.estado
            USING ERRCODE = 'P0001';
    END IF;

    UPDATE solicitudes
    SET estado = 'preaprobada',
        revisado_por_id = p_encargado_id,
        revisado_en = now(),
        respuesta = COALESCE(btrim(p_respuesta), ''),
        preaprobada_en = now(),
        vence_en = now() + make_interval(hours => fn_parametro('horas_vigencia_retiro')),
        codigo_hash = NULL,
        codigo_generado_en = NULL,
        intentos_codigo = 0,
        version = version + 1
    WHERE id = p_solicitud_id;

    UPDATE objetos SET estado = 'reservado', version = version + 1 WHERE id = v_objeto.id;

    p_resultado := 'preaprobada';
END;
$$;


-- ---------------------------------------------------------------------
-- Rechazo: la descripción no coincide o la prueba no fue suficiente.
-- Si la reclamación estaba pre-aprobada, el objeto vuelve a estar
-- disponible en la oficina. (El trigger trg_solicitudes_marcar_rechazos
-- cuenta los rechazos del estudiante.)
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_rechazar_solicitud(
    p_solicitud_id INTEGER,
    p_encargado_id INTEGER,
    p_motivo       TEXT,
    INOUT p_resultado TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto_id INTEGER;
    v_solicitud solicitudes%ROWTYPE;
BEGIN
    PERFORM fn_exigir_encargado(p_encargado_id);

    IF char_length(btrim(COALESCE(p_motivo, ''))) < 5 THEN
        RAISE EXCEPTION 'Escribe el motivo del rechazo (mínimo 5 caracteres)' USING ERRCODE = 'P0001';
    END IF;

    SELECT objeto_id INTO v_objeto_id FROM solicitudes WHERE id = p_solicitud_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La reclamación no existe' USING ERRCODE = 'P0001';
    END IF;

    PERFORM 1 FROM objetos WHERE id = v_objeto_id FOR UPDATE;
    SELECT * INTO v_solicitud FROM solicitudes WHERE id = p_solicitud_id FOR UPDATE;

    IF v_solicitud.estado NOT IN ('pendiente', 'preaprobada') THEN
        RAISE EXCEPTION 'Esta reclamación ya está cerrada (estado: %)', v_solicitud.estado
            USING ERRCODE = 'P0001';
    END IF;

    UPDATE solicitudes
    SET estado = 'rechazada',
        revisado_por_id = p_encargado_id,
        revisado_en = now(),
        respuesta = btrim(p_motivo),
        codigo_hash = NULL,
        codigo_generado_en = NULL,
        version = version + 1
    WHERE id = p_solicitud_id;

    IF v_solicitud.estado = 'preaprobada' THEN
        UPDATE objetos SET estado = 'en_oficina', version = version + 1
        WHERE id = v_objeto_id AND estado = 'reservado';
    END IF;

    p_resultado := 'rechazada';
END;
$$;


-- ---------------------------------------------------------------------
-- Entrega presencial: el estudiante llega a la oficina con su carné y su
-- código de retiro. Recibe el HASH del código (el código en claro nunca
-- llega a la base de datos).
--
-- Resultados posibles (no son errores, se confirman con COMMIT):
--   'entregado'          todo correcto, acta de entrega creada
--   'codigo_incorrecto'  se suma un intento fallido
--   'codigo_bloqueado'   se agotaron los intentos: el código se invalida y
--                        el estudiante debe generar uno nuevo
--   'sin_codigo'         el estudiante todavía no generó su código
--   'vencida'            pasó la ventana de retiro: el objeto vuelve a la oficina
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_registrar_entrega(
    p_objeto_id        INTEGER,
    p_encargado_id     INTEGER,
    p_codigo_hash      TEXT,
    p_carne_verificado BOOLEAN,
    p_prueba           TEXT,
    p_observaciones    TEXT,
    INOUT p_resultado  TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto       objetos%ROWTYPE;
    v_solicitud    solicitudes%ROWTYPE;
    v_max_intentos INTEGER;
BEGIN
    PERFORM fn_exigir_encargado(p_encargado_id);
    v_max_intentos := fn_parametro('max_intentos_codigo');

    SELECT * INTO v_objeto FROM objetos WHERE id = p_objeto_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El objeto no existe' USING ERRCODE = 'P0001';
    END IF;
    IF v_objeto.estado <> 'reservado' THEN
        RAISE EXCEPTION 'Este objeto no tiene una reclamación pre-aprobada esperando entrega (estado: %)', v_objeto.estado
            USING ERRCODE = 'P0001';
    END IF;

    SELECT * INTO v_solicitud FROM solicitudes
    WHERE objeto_id = p_objeto_id AND estado = 'preaprobada'
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se encontró la reclamación pre-aprobada de este objeto' USING ERRCODE = 'P0001';
    END IF;

    IF v_solicitud.vence_en < now() THEN
        UPDATE solicitudes
        SET estado = 'vencida', codigo_hash = NULL, codigo_generado_en = NULL, version = version + 1
        WHERE id = v_solicitud.id;
        UPDATE objetos SET estado = 'en_oficina', version = version + 1 WHERE id = p_objeto_id;
        p_resultado := 'vencida';
        RETURN;
    END IF;

    IF v_solicitud.codigo_hash IS NULL THEN
        p_resultado := 'sin_codigo';
        RETURN;
    END IF;

    IF p_codigo_hash IS NULL OR v_solicitud.codigo_hash <> p_codigo_hash THEN
        IF v_solicitud.intentos_codigo + 1 >= v_max_intentos THEN
            UPDATE solicitudes
            SET codigo_hash = NULL, codigo_generado_en = NULL, intentos_codigo = 0, version = version + 1
            WHERE id = v_solicitud.id;
            p_resultado := 'codigo_bloqueado';
        ELSE
            UPDATE solicitudes
            SET intentos_codigo = intentos_codigo + 1, version = version + 1
            WHERE id = v_solicitud.id;
            p_resultado := 'codigo_incorrecto';
        END IF;
        RETURN;
    END IF;

    IF NOT COALESCE(p_carne_verificado, FALSE) THEN
        RAISE EXCEPTION 'Debes verificar el carné del estudiante antes de entregar el objeto' USING ERRCODE = 'P0001';
    END IF;
    IF char_length(btrim(COALESCE(p_prueba, ''))) < 5 THEN
        RAISE EXCEPTION 'Describe la prueba de propiedad que presentó el estudiante (mínimo 5 caracteres)'
            USING ERRCODE = 'P0001';
    END IF;
    IF v_solicitud.solicitante_id = p_encargado_id THEN
        RAISE EXCEPTION 'Un encargado no puede entregarse un objeto a sí mismo' USING ERRCODE = 'P0001';
    END IF;

    INSERT INTO entregas (objeto_id, solicitud_id, entregado_por_id, carne_verificado,
                          prueba_propiedad, observaciones)
    VALUES (p_objeto_id, v_solicitud.id, p_encargado_id, TRUE,
            btrim(p_prueba), COALESCE(btrim(p_observaciones), ''));

    UPDATE solicitudes
    SET estado = 'entregada', codigo_hash = NULL, codigo_generado_en = NULL, version = version + 1
    WHERE id = v_solicitud.id;

    UPDATE objetos SET estado = 'entregado', version = version + 1 WHERE id = p_objeto_id;

    -- Las demás reclamaciones de este objeto ya no pueden prosperar
    UPDATE solicitudes
    SET estado = 'descartada',
        respuesta = 'El objeto fue entregado a otra persona después de verificar su propiedad',
        version = version + 1
    WHERE objeto_id = p_objeto_id AND estado = 'pendiente';

    -- Si el estudiante había reportado la pérdida, ese reporte queda resuelto
    IF v_solicitud.reporte_perdida_id IS NOT NULL THEN
        UPDATE objetos SET estado = 'recuperado', version = version + 1
        WHERE id = v_solicitud.reporte_perdida_id AND estado = 'buscando';
    END IF;

    p_resultado := 'entregado';
END;
$$;


-- ---------------------------------------------------------------------
-- Cierre de un reporte por la oficina (el objeto nunca llegó, se donó
-- después del tiempo de custodia, o un reporte de pérdida ya no aplica).
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_cerrar_objeto(
    p_objeto_id    INTEGER,
    p_encargado_id INTEGER,
    p_motivo       TEXT,
    INOUT p_resultado TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_objeto objetos%ROWTYPE;
BEGIN
    PERFORM fn_exigir_encargado(p_encargado_id);

    IF char_length(btrim(COALESCE(p_motivo, ''))) < 5 THEN
        RAISE EXCEPTION 'Escribe el motivo del cierre (mínimo 5 caracteres)' USING ERRCODE = 'P0001';
    END IF;

    SELECT * INTO v_objeto FROM objetos WHERE id = p_objeto_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El objeto no existe' USING ERRCODE = 'P0001';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM transiciones_objeto
        WHERE tipo = v_objeto.tipo AND estado_origen = v_objeto.estado
          AND estado_destino = 'cerrado' AND actor = 'encargado'
    ) THEN
        RAISE EXCEPTION 'No se puede cerrar un reporte en estado "%"', v_objeto.estado
            USING ERRCODE = 'P0001';
    END IF;

    UPDATE solicitudes
    SET estado = 'descartada',
        respuesta = left('La oficina cerró este reporte: ' || btrim(p_motivo), 300),
        version = version + 1
    WHERE objeto_id = p_objeto_id AND estado = 'pendiente';

    UPDATE objetos
    SET estado = 'cerrado', motivo_cierre = left(btrim(p_motivo), 300), version = version + 1
    WHERE id = p_objeto_id;

    p_resultado := 'cerrado';
END;
$$;


-- ---------------------------------------------------------------------
-- Vencimiento de reservas: las reclamaciones pre-aprobadas cuyo plazo de
-- retiro pasó vuelven a dejar el objeto disponible. Es una FUNCIÓN (no un
-- procedimiento) porque devuelve las filas afectadas, para que la
-- aplicación pueda avisar a cada estudiante.
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_vencer_reservas()
RETURNS TABLE (solicitud_id INTEGER, solicitante_id INTEGER, objeto_id INTEGER)
LANGUAGE plpgsql AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT s.id AS sid, s.objeto_id AS oid
        FROM solicitudes s
        WHERE s.estado = 'preaprobada' AND s.vence_en < now()
        ORDER BY s.objeto_id
    LOOP
        PERFORM 1 FROM objetos o WHERE o.id = r.oid FOR UPDATE;

        UPDATE solicitudes s
        SET estado = 'vencida', codigo_hash = NULL, codigo_generado_en = NULL, version = s.version + 1
        WHERE s.id = r.sid AND s.estado = 'preaprobada' AND s.vence_en < now();

        IF FOUND THEN
            UPDATE objetos o SET estado = 'en_oficina', version = o.version + 1
            WHERE o.id = r.oid AND o.estado = 'reservado';

            solicitud_id := r.sid;
            objeto_id := r.oid;
            SELECT s.solicitante_id INTO solicitante_id FROM solicitudes s WHERE s.id = r.sid;
            RETURN NEXT;
        END IF;
    END LOOP;
END;
$$;
