-- =====================================================================
-- 05_datos_iniciales.sql — Catálogos y parámetros iniciales
-- =====================================================================
-- Idempotente (ON CONFLICT DO NOTHING): se puede ejecutar varias veces sin
-- duplicar nada. Las pruebas automáticas lo vuelven a ejecutar después de
-- limpiar las tablas.
-- =====================================================================

INSERT INTO roles (codigo, nombre, descripcion) VALUES
    ('estudiante',    'Estudiante',    'Reporta objetos perdidos o encontrados y reclama los suyos'),
    ('encargado',     'Encargado',     'Recibe los objetos en la oficina, verifica reclamaciones y entrega'),
    ('administrador', 'Administrador', 'Gestiona usuarios, roles, catálogos y revisa la auditoría')
ON CONFLICT DO NOTHING;

INSERT INTO estados_objeto (tipo, codigo, nombre, descripcion, es_inicial, es_final) VALUES
    ('perdido',    'buscando',          'Buscando',             'El estudiante perdió el objeto y lo está buscando', TRUE,  FALSE),
    ('perdido',    'recuperado',        'Recuperado',           'El objeto fue devuelto a su dueño',                 FALSE, TRUE),
    ('perdido',    'cerrado',           'Cerrado',              'La oficina cerró el reporte',                       FALSE, TRUE),
    ('perdido',    'cancelado',         'Cancelado',            'El estudiante canceló el reporte',                  FALSE, TRUE),
    ('encontrado', 'pendiente_entrega', 'Pendiente de entrega', 'Reportado; falta llevarlo a la oficina',            TRUE,  FALSE),
    ('encontrado', 'en_oficina',        'En la oficina',        'En custodia de la oficina; se puede reclamar',      FALSE, FALSE),
    ('encontrado', 'reservado',         'Reservado',            'Hay una reclamación pre-aprobada esperando retiro', FALSE, FALSE),
    ('encontrado', 'entregado',         'Entregado',            'Entregado a su dueño tras verificar su propiedad',  FALSE, TRUE),
    ('encontrado', 'cerrado',           'Cerrado',              'La oficina cerró el reporte',                       FALSE, TRUE),
    ('encontrado', 'cancelado',         'Cancelado',            'Quien lo encontró canceló el reporte',              FALSE, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO transiciones_objeto (tipo, estado_origen, estado_destino, actor) VALUES
    ('perdido',    'buscando',          'cancelado',  'estudiante'),
    ('perdido',    'buscando',          'cerrado',    'encargado'),
    ('perdido',    'buscando',          'recuperado', 'sistema'),
    ('encontrado', 'pendiente_entrega', 'en_oficina', 'encargado'),
    ('encontrado', 'pendiente_entrega', 'cancelado',  'estudiante'),
    ('encontrado', 'pendiente_entrega', 'cerrado',    'encargado'),
    ('encontrado', 'en_oficina',        'reservado',  'sistema'),
    ('encontrado', 'en_oficina',        'cerrado',    'encargado'),
    ('encontrado', 'reservado',         'entregado',  'sistema'),
    ('encontrado', 'reservado',         'en_oficina', 'sistema')
ON CONFLICT DO NOTHING;

INSERT INTO estados_solicitud (codigo, nombre, descripcion, es_abierta, cuenta_como_rechazo) VALUES
    ('pendiente',   'Pendiente',   'Esperando la revisión de un encargado',                          TRUE,  FALSE),
    ('preaprobada', 'Pre-aprobada', 'Descripción correcta; falta retirar el objeto en persona',      TRUE,  FALSE),
    ('entregada',   'Entregada',   'El objeto fue entregado al estudiante',                          FALSE, FALSE),
    ('rechazada',   'Rechazada',   'El encargado no pudo verificar la propiedad',                    FALSE, TRUE),
    ('cancelada',   'Cancelada',   'El estudiante canceló la reclamación',                           FALSE, FALSE),
    ('vencida',     'Vencida',     'Pasó el plazo para retirar el objeto',                           FALSE, FALSE),
    ('descartada',  'Descartada',  'El objeto se entregó a otra persona o la oficina cerró el caso',  FALSE, FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO parametros (clave, valor, minimo, maximo, descripcion) VALUES
    ('max_solicitudes_abiertas', 3,  1, 10,  'Reclamaciones abiertas que puede tener un estudiante al mismo tiempo'),
    ('max_rechazos',             3,  1, 20,  'Reclamaciones rechazadas tras las cuales la cuenta queda en revisión'),
    ('horas_vigencia_retiro',    72, 1, 336, 'Horas que tiene el estudiante para retirar un objeto pre-aprobado'),
    ('max_intentos_codigo',      5,  1, 10,  'Intentos fallidos del código de retiro antes de invalidarlo')
ON CONFLICT DO NOTHING;

INSERT INTO categorias (nombre) VALUES
    ('Tecnología'), ('Documentos'), ('Llaves'), ('Billeteras y bolsos'), ('Ropa'),
    ('Accesorios'), ('Útiles escolares'), ('Botellas y termos'), ('Otro')
ON CONFLICT DO NOTHING;

INSERT INTO ubicaciones (nombre, descripcion) VALUES
    ('Biblioteca',                'Salas de lectura y préstamo'),
    ('Cafetería',                 'Cafetería y zona de mesas'),
    ('Salones de clase',          'Cualquier salón de clase'),
    ('Laboratorios',              'Laboratorios de sistemas y especializados'),
    ('Auditorio',                 'Auditorio principal'),
    ('Baños',                     'Baños de cualquier piso'),
    ('Zonas comunes',             'Pasillos, escaleras, plazoleta y zonas de descanso'),
    ('Entrada principal',         'Portería y recepción'),
    ('Otro lugar',                'Un lugar que no está en la lista')
ON CONFLICT DO NOTHING;
