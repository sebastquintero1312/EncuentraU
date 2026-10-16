-- =====================================================================
-- 00_eliminar.sql — Deshace la migración 0001 (flask db downgrade base)
-- =====================================================================
-- Borra TODOS los objetos de EncuentraU v2.0. Solo para desarrollo:
-- en producción NUNCA se hace downgrade sin un respaldo previo
-- (ver database/scripts/respaldo.py).
-- =====================================================================

DROP VIEW IF EXISTS v_auditoria_detallada, v_desempeno_encargados, v_estadisticas_mensuales,
    v_estadisticas_generales, v_objetos_disponibles;

DROP FUNCTION IF EXISTS fn_vencer_reservas();
DROP PROCEDURE IF EXISTS sp_cerrar_objeto(INTEGER, INTEGER, TEXT, TEXT);
DROP PROCEDURE IF EXISTS sp_registrar_entrega(INTEGER, INTEGER, TEXT, BOOLEAN, TEXT, TEXT, TEXT);
DROP PROCEDURE IF EXISTS sp_rechazar_solicitud(INTEGER, INTEGER, TEXT, TEXT);
DROP PROCEDURE IF EXISTS sp_preaprobar_solicitud(INTEGER, INTEGER, TEXT, TEXT);
DROP PROCEDURE IF EXISTS sp_registrar_recepcion(INTEGER, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS fn_exigir_encargado(INTEGER);

-- Las tablas se borran con sus triggers, índices y políticas (CASCADE).
DROP TABLE IF EXISTS auditoria, notificaciones, entregas, solicitudes, objetos, tokens_usuario,
    usuarios, ubicaciones, categorias, parametros, estados_solicitud, transiciones_objeto,
    estados_objeto, roles CASCADE;

DROP FUNCTION IF EXISTS fn_auditoria_inmutable();
DROP FUNCTION IF EXISTS fn_auditoria();
DROP FUNCTION IF EXISTS fn_marcar_cuenta_por_rechazos();
DROP FUNCTION IF EXISTS fn_validar_nueva_solicitud();
DROP FUNCTION IF EXISTS fn_validar_estado_objeto();
DROP FUNCTION IF EXISTS fn_actualizar_updated_at();
DROP FUNCTION IF EXISTS fn_parametro(TEXT);
