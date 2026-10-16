-- =====================================================================
-- 04_vistas.sql — Vistas para reportes e integración con otras apps
-- =====================================================================
--
-- Una VISTA es una consulta guardada con nombre: se usa como si fuera una
-- tabla, pero no guarda datos propios. Sirven para:
--
--   * Estadísticas del panel del administrador y del encargado.
--   * Integración: una herramienta externa (Excel, Power BI, Looker Studio)
--     puede conectarse con un usuario de SOLO LECTURA que únicamente tenga
--     permiso sobre estas vistas, nunca sobre las tablas con datos
--     personales (ver database/scripts/crear_rol_lector.sql).
-- =====================================================================


-- Objetos que un estudiante puede ver y reclamar. Solo columnas PÚBLICAS:
-- sin descripción privada, sin quién lo encontró.
CREATE VIEW v_objetos_disponibles AS
SELECT o.id,
       o.nombre,
       c.nombre AS categoria,
       u.nombre AS ubicacion,
       o.fecha_evento,
       o.recibido_en,
       o.estado
FROM objetos o
JOIN categorias c ON c.id = o.categoria_id
JOIN ubicaciones u ON u.id = o.ubicacion_id
WHERE o.tipo = 'encontrado'
  AND o.estado IN ('en_oficina', 'reservado');


-- Resumen general (una sola fila). Usa FILTER, que cuenta por condición
-- dentro de un mismo recorrido de la tabla.
CREATE VIEW v_estadisticas_generales AS
SELECT
    count(*) FILTER (WHERE tipo = 'perdido')                                       AS reportes_perdidos,
    count(*) FILTER (WHERE tipo = 'encontrado')                                    AS reportes_encontrados,
    count(*) FILTER (WHERE tipo = 'perdido' AND estado = 'buscando')               AS perdidos_buscando,
    count(*) FILTER (WHERE tipo = 'encontrado' AND estado = 'pendiente_entrega')   AS pendientes_de_recibir,
    count(*) FILTER (WHERE tipo = 'encontrado' AND estado IN ('en_oficina', 'reservado')) AS en_custodia,
    count(*) FILTER (WHERE tipo = 'encontrado' AND estado = 'reservado')           AS reservados,
    count(*) FILTER (WHERE estado = 'entregado')                                   AS entregados,
    count(*) FILTER (WHERE estado = 'recuperado')                                  AS perdidos_recuperados,
    (SELECT count(*) FROM solicitudes WHERE estado = 'pendiente')                  AS reclamaciones_pendientes,
    (SELECT count(*) FROM solicitudes WHERE estado = 'rechazada')                  AS reclamaciones_rechazadas,
    (SELECT count(*) FROM usuarios WHERE marcado_revision)                         AS cuentas_en_revision
FROM objetos;


-- Actividad por mes (hora de Colombia).
CREATE VIEW v_estadisticas_mensuales AS
WITH reportes AS (
    SELECT date_trunc('month', created_at AT TIME ZONE 'America/Bogota')::date AS mes,
           count(*) FILTER (WHERE tipo = 'perdido')    AS perdidos,
           count(*) FILTER (WHERE tipo = 'encontrado') AS encontrados
    FROM objetos
    GROUP BY 1
),
entregas_mes AS (
    SELECT date_trunc('month', entregado_en AT TIME ZONE 'America/Bogota')::date AS mes,
           count(*) AS entregados
    FROM entregas
    GROUP BY 1
)
SELECT COALESCE(r.mes, e.mes)      AS mes,
       COALESCE(r.perdidos, 0)     AS perdidos,
       COALESCE(r.encontrados, 0)  AS encontrados,
       COALESCE(e.entregados, 0)   AS entregados
FROM reportes r
FULL JOIN entregas_mes e ON e.mes = r.mes;


-- Control del administrador sobre los encargados (separación de funciones):
-- cuántas reclamaciones revisa, aprueba y rechaza cada uno. Un encargado
-- que aprueba casi todo, o que entrega mucho más que sus compañeros, es
-- una señal para revisar su historial en la auditoría.
CREATE VIEW v_desempeno_encargados AS
SELECT u.id                                         AS encargado_id,
       u.primer_nombre || ' ' || u.primer_apellido  AS encargado,
       u.correo,
       u.rol,
       u.activo,
       (SELECT count(*) FROM objetos o WHERE o.recibido_por_id = u.id)                   AS objetos_recibidos,
       (SELECT count(*) FROM solicitudes s
         WHERE s.revisado_por_id = u.id AND s.preaprobada_en IS NOT NULL)                AS preaprobaciones,
       (SELECT count(*) FROM solicitudes s
         WHERE s.revisado_por_id = u.id AND s.estado = 'rechazada')                      AS rechazos,
       (SELECT count(*) FROM entregas e WHERE e.entregado_por_id = u.id)                 AS entregas,
       (SELECT round(avg(extract(epoch FROM (e.entregado_en - o.recibido_en)) / 3600)::numeric, 1)
          FROM entregas e JOIN objetos o ON o.id = e.objeto_id
         WHERE e.entregado_por_id = u.id)                                                AS horas_promedio_custodia
FROM usuarios u
WHERE u.rol = 'encargado'
   OR EXISTS (SELECT 1 FROM objetos o WHERE o.recibido_por_id = u.id)
   OR EXISTS (SELECT 1 FROM solicitudes s WHERE s.revisado_por_id = u.id)
   OR EXISTS (SELECT 1 FROM entregas e WHERE e.entregado_por_id = u.id);


-- Auditoría con el nombre de quien hizo cada cambio.
-- (usuario_rol es el rol ACTUAL de la persona, no el que tenía en ese momento.)
CREATE VIEW v_auditoria_detallada AS
SELECT a.id,
       a.fecha,
       a.tabla,
       a.registro_id,
       a.operacion,
       a.usuario_id,
       COALESCE(u.primer_nombre || ' ' || u.primer_apellido, 'Sistema') AS usuario_nombre,
       u.correo AS usuario_correo,
       u.rol    AS usuario_rol,
       a.ip,
       a.campos_modificados,
       a.datos_anteriores,
       a.datos_nuevos,
       a.transaccion_id
FROM auditoria a
LEFT JOIN usuarios u ON u.id = a.usuario_id;
