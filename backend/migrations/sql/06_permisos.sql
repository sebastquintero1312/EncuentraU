-- =====================================================================
-- 06_permisos.sql — Permisos mínimos (least privilege) y Row Level Security
-- =====================================================================
--
-- La aplicación web se conecta con el usuario "encuentrau_app", que solo
-- recibe los permisos que necesita (GRANT). Lo que no se concede aquí está
-- prohibido (deny by default). En particular, encuentrau_app NO puede:
--
--   * borrar filas de ninguna tabla (no hay borrado físico en el sistema);
--   * insertar, modificar o borrar filas de la auditoría (solo leerla);
--   * modificar un acta de entrega una vez creada;
--   * cambiar el texto de una reclamación ya enviada, el autor de un
--     reporte, ni el correo de un usuario (permisos por COLUMNA);
--   * crear o borrar tablas, ni desactivar triggers (no es dueño).
--
-- Si encuentrau_app no existe (por ejemplo, en un despliegue que usa un
-- solo usuario), este archivo no falla: simplemente no concede nada.
-- Se puede volver a ejecutar sin problema (es idempotente):
--   psql "<url del dueño>" -f backend/migrations/sql/06_permisos.sql
-- =====================================================================

DO $$
DECLARE
    v_tabla TEXT;
    v_tablas CONSTANT TEXT[] := ARRAY[
        'roles', 'estados_objeto', 'transiciones_objeto', 'estados_solicitud', 'parametros',
        'categorias', 'ubicaciones', 'usuarios', 'tokens_usuario', 'objetos',
        'solicitudes', 'entregas', 'notificaciones', 'auditoria'
    ];
    v_hay_app BOOLEAN := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'encuentrau_app');
BEGIN
    -- Los procedimientos y funciones del negocio no se pueden ejecutar por
    -- defecto (PostgreSQL concede EXECUTE a PUBLIC); solo la aplicación.
    REVOKE EXECUTE ON FUNCTION fn_parametro(TEXT) FROM PUBLIC;
    REVOKE EXECUTE ON FUNCTION fn_exigir_encargado(INTEGER) FROM PUBLIC;
    REVOKE EXECUTE ON FUNCTION fn_vencer_reservas() FROM PUBLIC;
    REVOKE EXECUTE ON PROCEDURE sp_registrar_recepcion(INTEGER, INTEGER, TEXT, TEXT) FROM PUBLIC;
    REVOKE EXECUTE ON PROCEDURE sp_preaprobar_solicitud(INTEGER, INTEGER, TEXT, TEXT) FROM PUBLIC;
    REVOKE EXECUTE ON PROCEDURE sp_rechazar_solicitud(INTEGER, INTEGER, TEXT, TEXT) FROM PUBLIC;
    REVOKE EXECUTE ON PROCEDURE sp_registrar_entrega(INTEGER, INTEGER, TEXT, BOOLEAN, TEXT, TEXT, TEXT) FROM PUBLIC;
    REVOKE EXECUTE ON PROCEDURE sp_cerrar_objeto(INTEGER, INTEGER, TEXT, TEXT) FROM PUBLIC;

    IF v_hay_app THEN
        GRANT USAGE ON SCHEMA public TO encuentrau_app;

        -- Catálogos fijos: solo lectura
        GRANT SELECT ON roles, estados_objeto, transiciones_objeto, estados_solicitud TO encuentrau_app;

        -- Parámetros: el administrador solo puede cambiar el VALOR
        GRANT SELECT ON parametros TO encuentrau_app;
        GRANT UPDATE (valor) ON parametros TO encuentrau_app;

        -- Catálogos editables
        GRANT SELECT, INSERT ON categorias, ubicaciones TO encuentrau_app;
        GRANT UPDATE (nombre, activa) ON categorias TO encuentrau_app;
        GRANT UPDATE (nombre, descripcion, activa) ON ubicaciones TO encuentrau_app;

        -- Usuarios: nunca se cambia el correo ni la fecha de creación
        GRANT SELECT, INSERT ON usuarios TO encuentrau_app;
        GRANT UPDATE (password_hash, rol, activo, correo_verificado_en,
                      marcado_revision, motivo_revision) ON usuarios TO encuentrau_app;

        GRANT SELECT, INSERT ON tokens_usuario TO encuentrau_app;
        GRANT UPDATE (usado_en) ON tokens_usuario TO encuentrau_app;

        -- Reportes: nunca se cambia el tipo ni quién lo reportó
        GRANT SELECT, INSERT ON objetos TO encuentrau_app;
        GRANT UPDATE (nombre, categoria_id, ubicacion_id, fecha_evento, descripcion, detalle_ubicacion,
                      estado, recibido_por_id, recibido_en, observaciones_custodia, motivo_cierre,
                      version) ON objetos TO encuentrau_app;

        -- Reclamaciones: lo que escribió el estudiante no se puede cambiar
        -- después de enviarlo (evita que ajuste su descripción a escondidas)
        GRANT SELECT, INSERT ON solicitudes TO encuentrau_app;
        GRANT UPDATE (estado, revisado_por_id, revisado_en, respuesta, preaprobada_en, vence_en,
                      codigo_hash, codigo_generado_en, intentos_codigo, version) ON solicitudes TO encuentrau_app;

        -- Actas de entrega: se crean, nunca se modifican
        GRANT SELECT, INSERT ON entregas TO encuentrau_app;

        GRANT SELECT, INSERT ON notificaciones TO encuentrau_app;
        GRANT UPDATE (leida_en, correo_enviado_en) ON notificaciones TO encuentrau_app;

        -- Auditoría: SOLO lectura. Las filas las inserta fn_auditoria()
        -- (SECURITY DEFINER), no la aplicación.
        GRANT SELECT ON auditoria TO encuentrau_app;

        GRANT SELECT ON v_objetos_disponibles, v_estadisticas_generales, v_estadisticas_mensuales,
                        v_desempeno_encargados, v_auditoria_detallada TO encuentrau_app;

        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO encuentrau_app;

        GRANT EXECUTE ON FUNCTION fn_parametro(TEXT) TO encuentrau_app;
        GRANT EXECUTE ON FUNCTION fn_exigir_encargado(INTEGER) TO encuentrau_app;
        GRANT EXECUTE ON FUNCTION fn_vencer_reservas() TO encuentrau_app;
        GRANT EXECUTE ON PROCEDURE sp_registrar_recepcion(INTEGER, INTEGER, TEXT, TEXT) TO encuentrau_app;
        GRANT EXECUTE ON PROCEDURE sp_preaprobar_solicitud(INTEGER, INTEGER, TEXT, TEXT) TO encuentrau_app;
        GRANT EXECUTE ON PROCEDURE sp_rechazar_solicitud(INTEGER, INTEGER, TEXT, TEXT) TO encuentrau_app;
        GRANT EXECUTE ON PROCEDURE sp_registrar_entrega(INTEGER, INTEGER, TEXT, BOOLEAN, TEXT, TEXT, TEXT) TO encuentrau_app;
        GRANT EXECUTE ON PROCEDURE sp_cerrar_objeto(INTEGER, INTEGER, TEXT, TEXT) TO encuentrau_app;
    END IF;

    -- Row Level Security (RLS): con RLS activo, un usuario de base de datos
    -- solo ve las filas que una política le permite. La aplicación tiene una
    -- política que le permite todo (los permisos finos los aplica Flask);
    -- cualquier otro usuario sin política (por ejemplo, los roles "anon" y
    -- "authenticated" de la API automática de Supabase) no ve NINGUNA fila.
    -- El dueño de las tablas no está sujeto a RLS.
    FOREACH v_tabla IN ARRAY v_tablas LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', v_tabla);
        EXECUTE format('DROP POLICY IF EXISTS p_aplicacion ON %I', v_tabla);
        IF v_hay_app THEN
            EXECUTE format(
                'CREATE POLICY p_aplicacion ON %I TO encuentrau_app USING (true) WITH CHECK (true)',
                v_tabla
            );
        END IF;
    END LOOP;

    -- Supabase expone automáticamente las tablas del esquema public por su
    -- API REST a los roles "anon" y "authenticated". EncuentraU no usa esa
    -- API: se les quita todo permiso (además de RLS, defensa en profundidad).
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated';
        EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated';
        EXECUTE 'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated';
        EXECUTE 'REVOKE ALL ON ALL PROCEDURES IN SCHEMA public FROM anon, authenticated';
    END IF;
END;
$$;
