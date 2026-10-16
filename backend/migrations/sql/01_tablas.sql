-- =====================================================================
-- 01_tablas.sql — Tablas, restricciones e índices de EncuentraU v2.0
-- =====================================================================
--
-- Diseño normalizado hasta Tercera Forma Normal (3FN):
--
--   * 1FN: cada columna guarda un solo valor (no hay listas dentro de un
--     campo, ni columnas repetidas tipo "telefono1, telefono2").
--   * 2FN: toda columna que no es clave depende de la clave COMPLETA
--     (aplica a las tablas con clave compuesta: estados_objeto y
--     transiciones_objeto).
--   * 3FN: no hay dependencias transitivas. Ejemplo: el nombre de una
--     categoría NO se repite en cada reporte; el reporte guarda solo
--     categoria_id y el nombre vive una sola vez en la tabla categorias.
--     Si el administrador renombra "Útiles" a "Útiles escolares", se cambia
--     en un solo lugar y no queda ningún reporte con el nombre viejo.
--
-- Tablas de catálogo (datos de referencia):
--   roles, estados_objeto, transiciones_objeto, estados_solicitud,
--   parametros, categorias, ubicaciones
-- Tablas del negocio:
--   usuarios, tokens_usuario, objetos, solicitudes, entregas, notificaciones
-- Tabla de control:
--   auditoria (la llenan los triggers de 02_funciones_triggers.sql)
--
-- Claves: los catálogos FIJOS del sistema (roles, estados) usan su código
-- como clave natural ('estudiante', 'en_oficina'...) para que las consultas
-- sean legibles. Los catálogos EDITABLES por el administrador (categorías,
-- ubicaciones) usan una clave sustituta numérica (id), para que renombrar
-- uno no obligue a cambiar las filas que lo referencian.
-- =====================================================================

-- Extensión para búsqueda por similitud de texto (índices de trigramas).
-- Es una extensión "trusted": la puede instalar el dueño de la base de datos
-- sin ser superusuario.
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- ---------------------------------------------------------------------
-- Catálogos fijos del sistema
-- ---------------------------------------------------------------------

CREATE TABLE roles (
    codigo      VARCHAR(20)  PRIMARY KEY,
    nombre      VARCHAR(50)  NOT NULL,
    descripcion VARCHAR(255) NOT NULL
);

-- Estados posibles de un reporte. Un objeto PERDIDO y uno ENCONTRADO
-- recorren estados distintos, por eso la clave es (tipo, codigo).
CREATE TABLE estados_objeto (
    tipo        VARCHAR(20)  NOT NULL,
    codigo      VARCHAR(20)  NOT NULL,
    nombre      VARCHAR(50)  NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    es_inicial  BOOLEAN      NOT NULL DEFAULT FALSE,
    es_final    BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_estados_objeto PRIMARY KEY (tipo, codigo),
    CONSTRAINT ck_estados_objeto_tipo CHECK (tipo IN ('perdido', 'encontrado')),
    CONSTRAINT ck_estados_objeto_inicial_no_final CHECK (NOT (es_inicial AND es_final))
);

-- Máquina de estados como DATOS: qué cambio de estado está permitido y
-- quién puede pedirlo. El trigger trg_objetos_validar_estado rechaza
-- cualquier UPDATE que no esté en esta tabla, aunque venga de un bug.
CREATE TABLE transiciones_objeto (
    tipo           VARCHAR(20) NOT NULL,
    estado_origen  VARCHAR(20) NOT NULL,
    estado_destino VARCHAR(20) NOT NULL,
    actor          VARCHAR(20) NOT NULL,
    CONSTRAINT pk_transiciones_objeto PRIMARY KEY (tipo, estado_origen, estado_destino),
    CONSTRAINT fk_transiciones_origen FOREIGN KEY (tipo, estado_origen)
        REFERENCES estados_objeto (tipo, codigo),
    CONSTRAINT fk_transiciones_destino FOREIGN KEY (tipo, estado_destino)
        REFERENCES estados_objeto (tipo, codigo),
    CONSTRAINT ck_transiciones_distintos CHECK (estado_origen <> estado_destino),
    -- 'sistema' = solo un procedimiento almacenado puede hacer ese cambio
    CONSTRAINT ck_transiciones_actor CHECK (actor IN ('estudiante', 'encargado', 'sistema'))
);

CREATE TABLE estados_solicitud (
    codigo              VARCHAR(20)  PRIMARY KEY,
    nombre              VARCHAR(50)  NOT NULL,
    descripcion         VARCHAR(255) NOT NULL,
    es_abierta          BOOLEAN      NOT NULL,
    -- Solo los rechazos hechos por un encargado cuentan para marcar una
    -- cuenta como sospechosa ('descartada' no cuenta: el objeto se entregó
    -- a otra persona, no fue culpa del estudiante).
    cuenta_como_rechazo BOOLEAN      NOT NULL DEFAULT FALSE
);

-- Reglas del negocio que se pueden ajustar sin tocar el código.
CREATE TABLE parametros (
    clave       VARCHAR(50)  PRIMARY KEY,
    valor       INTEGER      NOT NULL,
    minimo      INTEGER      NOT NULL,
    maximo      INTEGER      NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_parametros_rango CHECK (valor BETWEEN minimo AND maximo)
);


-- ---------------------------------------------------------------------
-- Catálogos editables por el administrador
-- ---------------------------------------------------------------------

CREATE TABLE categorias (
    id         INTEGER     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre     VARCHAR(50) NOT NULL,
    activa     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_categorias_nombre CHECK (char_length(btrim(nombre)) BETWEEN 3 AND 50)
);
-- Índice único sobre una EXPRESIÓN: impide "Ropa" y "ropa" como categorías distintas.
CREATE UNIQUE INDEX ux_categorias_nombre ON categorias (lower(nombre));

CREATE TABLE ubicaciones (
    id          INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre      VARCHAR(80)  NOT NULL,
    descripcion VARCHAR(200) NOT NULL DEFAULT '',
    activa      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_ubicaciones_nombre CHECK (char_length(btrim(nombre)) BETWEEN 3 AND 80)
);
CREATE UNIQUE INDEX ux_ubicaciones_nombre ON ubicaciones (lower(nombre));


-- ---------------------------------------------------------------------
-- Usuarios y tokens
-- ---------------------------------------------------------------------

CREATE TABLE usuarios (
    id                   INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    primer_nombre        VARCHAR(80)  NOT NULL,
    segundo_nombre       VARCHAR(80)  NOT NULL DEFAULT '',
    primer_apellido      VARCHAR(80)  NOT NULL,
    segundo_apellido     VARCHAR(80)  NOT NULL DEFAULT '',
    correo               VARCHAR(255) NOT NULL,
    password_hash        VARCHAR(255) NOT NULL,
    rol                  VARCHAR(20)  NOT NULL DEFAULT 'estudiante',
    activo               BOOLEAN      NOT NULL DEFAULT TRUE,
    -- NULL = el estudiante todavía no confirmó que es dueño de su correo.
    correo_verificado_en TIMESTAMPTZ  NULL,
    -- Lo activa el trigger trg_solicitudes_marcar_rechazos; lo quita un administrador.
    marcado_revision     BOOLEAN      NOT NULL DEFAULT FALSE,
    motivo_revision      VARCHAR(255) NOT NULL DEFAULT '',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol) REFERENCES roles (codigo),
    CONSTRAINT ck_usuarios_correo_minusculas CHECK (correo = lower(correo)),
    CONSTRAINT ck_usuarios_correo_formato CHECK (correo ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    CONSTRAINT ck_usuarios_nombres CHECK (
        char_length(btrim(primer_nombre)) >= 1 AND char_length(btrim(primer_apellido)) >= 1
    )
);
CREATE UNIQUE INDEX ux_usuarios_correo ON usuarios (correo);
CREATE INDEX ix_usuarios_rol ON usuarios (rol);
-- Índice PARCIAL: solo indexa las (pocas) cuentas marcadas, para el panel del administrador.
CREATE INDEX ix_usuarios_marcados ON usuarios (updated_at DESC) WHERE marcado_revision;

-- Tokens de un solo uso para verificar el correo y para recuperar la
-- contraseña. Se guarda solo el HASH (SHA-256) del token: si alguien
-- robara una copia de la base de datos, no podría usar los enlaces.
CREATE TABLE tokens_usuario (
    id         INTEGER     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id INTEGER     NOT NULL,
    proposito  VARCHAR(20) NOT NULL,
    token_hash CHAR(64)    NOT NULL,
    expira_en  TIMESTAMPTZ NOT NULL,
    usado_en   TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_tokens_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    CONSTRAINT ck_tokens_proposito CHECK (proposito IN ('verificacion', 'recuperacion')),
    CONSTRAINT ck_tokens_expiracion CHECK (expira_en > created_at)
);
CREATE UNIQUE INDEX ux_tokens_hash ON tokens_usuario (token_hash);
CREATE INDEX ix_tokens_usuario ON tokens_usuario (usuario_id, proposito);


-- ---------------------------------------------------------------------
-- Reportes de objetos (perdidos y encontrados)
-- ---------------------------------------------------------------------

CREATE TABLE objetos (
    id                     INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo                   VARCHAR(20)  NOT NULL,
    -- PÚBLICO: nombre genérico ("Celular", "Chaqueta"). Lo ve cualquier estudiante.
    nombre                 VARCHAR(120) NOT NULL,
    categoria_id           INTEGER      NOT NULL,
    ubicacion_id           INTEGER      NOT NULL,
    fecha_evento           DATE         NOT NULL,
    -- PRIVADO: detalles que solo conoce el dueño real (marca, color, señas).
    -- Nunca se muestran en la búsqueda: son la base de la verificación a ciegas.
    descripcion            VARCHAR(500) NOT NULL,
    detalle_ubicacion      VARCHAR(150) NOT NULL DEFAULT '',
    estado                 VARCHAR(20)  NOT NULL,
    usuario_id             INTEGER      NOT NULL,
    -- Recepción física en la oficina (solo objetos encontrados)
    recibido_por_id        INTEGER      NULL,
    recibido_en            TIMESTAMPTZ  NULL,
    observaciones_custodia VARCHAR(500) NOT NULL DEFAULT '',
    motivo_cierre          VARCHAR(300) NOT NULL DEFAULT '',
    -- Control de concurrencia OPTIMISTA: cada modificación incrementa la
    -- versión; si dos personas editan a la vez, la segunda recibe un conflicto.
    version                INTEGER      NOT NULL DEFAULT 1,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_objetos_categoria FOREIGN KEY (categoria_id) REFERENCES categorias (id),
    CONSTRAINT fk_objetos_ubicacion FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
    CONSTRAINT fk_objetos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    CONSTRAINT fk_objetos_recibido_por FOREIGN KEY (recibido_por_id) REFERENCES usuarios (id),
    -- Clave foránea COMPUESTA: garantiza que el estado pertenece al tipo del
    -- reporte (un objeto perdido nunca puede quedar "en_oficina").
    CONSTRAINT fk_objetos_estado FOREIGN KEY (tipo, estado) REFERENCES estados_objeto (tipo, codigo),
    CONSTRAINT ck_objetos_tipo CHECK (tipo IN ('perdido', 'encontrado')),
    CONSTRAINT ck_objetos_nombre CHECK (char_length(btrim(nombre)) BETWEEN 3 AND 120),
    CONSTRAINT ck_objetos_descripcion CHECK (char_length(btrim(descripcion)) BETWEEN 10 AND 500),
    CONSTRAINT ck_objetos_fecha_no_futura CHECK (
        fecha_evento <= (created_at AT TIME ZONE 'America/Bogota')::date
    ),
    CONSTRAINT ck_objetos_recepcion_completa CHECK ((recibido_por_id IS NULL) = (recibido_en IS NULL)),
    CONSTRAINT ck_objetos_recepcion_solo_encontrados CHECK (tipo = 'encontrado' OR recibido_por_id IS NULL),
    CONSTRAINT ck_objetos_version CHECK (version >= 1)
);
-- PostgreSQL NO crea índices automáticamente para las claves foráneas:
-- se crean a mano para que los JOIN y los filtros por FK sean rápidos.
CREATE INDEX ix_objetos_usuario ON objetos (usuario_id, created_at DESC);
CREATE INDEX ix_objetos_categoria ON objetos (categoria_id);
CREATE INDEX ix_objetos_ubicacion ON objetos (ubicacion_id);
CREATE INDEX ix_objetos_recibido_por ON objetos (recibido_por_id) WHERE recibido_por_id IS NOT NULL;
-- Índice COMPUESTO para el panel del encargado (filtra por tipo y estado, ordena por fecha).
CREATE INDEX ix_objetos_tipo_estado_fecha ON objetos (tipo, estado, fecha_evento DESC);
-- Índice PARCIAL para la búsqueda de los estudiantes: solo los objetos que
-- están físicamente en la oficina (la gran mayoría de búsquedas).
CREATE INDEX ix_objetos_disponibles ON objetos (categoria_id, fecha_evento DESC)
    WHERE tipo = 'encontrado' AND estado IN ('en_oficina', 'reservado');
-- Índice GIN de TRIGRAMAS: acelera la búsqueda por texto con ILIKE '%celu%'
-- (un índice B-tree normal no sirve cuando el patrón empieza con %).
CREATE INDEX ix_objetos_nombre_trgm ON objetos USING gin (nombre gin_trgm_ops);


-- ---------------------------------------------------------------------
-- Reclamaciones (solicitudes) y entregas
-- ---------------------------------------------------------------------

CREATE TABLE solicitudes (
    id                 INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    objeto_id          INTEGER      NOT NULL,
    solicitante_id     INTEGER      NOT NULL,
    -- Opcional: el reporte de pérdida que el estudiante hizo ANTES de que
    -- apareciera el objeto. Es evidencia fuerte de propiedad.
    reporte_perdida_id INTEGER      NULL,
    -- Verificación a ciegas: el estudiante describe el objeto SIN haber
    -- visto los detalles privados. El encargado compara.
    descripcion        VARCHAR(500) NOT NULL,
    lugar_perdida      VARCHAR(150) NOT NULL,
    fecha_perdida      DATE         NOT NULL,
    evidencia          VARCHAR(300) NOT NULL DEFAULT '',
    estado             VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
    revisado_por_id    INTEGER      NULL,
    revisado_en        TIMESTAMPTZ  NULL,
    respuesta          VARCHAR(300) NOT NULL DEFAULT '',
    -- Ventana para retirar el objeto en la oficina tras la pre-aprobación
    preaprobada_en     TIMESTAMPTZ  NULL,
    vence_en           TIMESTAMPTZ  NULL,
    -- Código de retiro de un solo uso: se guarda solo su HMAC-SHA256.
    codigo_hash        CHAR(64)     NULL,
    codigo_generado_en TIMESTAMPTZ  NULL,
    intentos_codigo    SMALLINT     NOT NULL DEFAULT 0,
    version            INTEGER      NOT NULL DEFAULT 1,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_solicitudes_objeto FOREIGN KEY (objeto_id) REFERENCES objetos (id),
    CONSTRAINT fk_solicitudes_solicitante FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
    CONSTRAINT fk_solicitudes_reporte_perdida FOREIGN KEY (reporte_perdida_id) REFERENCES objetos (id),
    CONSTRAINT fk_solicitudes_revisor FOREIGN KEY (revisado_por_id) REFERENCES usuarios (id),
    CONSTRAINT fk_solicitudes_estado FOREIGN KEY (estado) REFERENCES estados_solicitud (codigo),
    -- Necesaria para la clave foránea compuesta de entregas (ver abajo)
    CONSTRAINT uq_solicitudes_id_objeto UNIQUE (id, objeto_id),
    CONSTRAINT ck_solicitudes_descripcion CHECK (char_length(btrim(descripcion)) BETWEEN 20 AND 500),
    CONSTRAINT ck_solicitudes_lugar CHECK (char_length(btrim(lugar_perdida)) BETWEEN 3 AND 150),
    CONSTRAINT ck_solicitudes_reporte_distinto CHECK (reporte_perdida_id IS NULL OR reporte_perdida_id <> objeto_id),
    CONSTRAINT ck_solicitudes_intentos CHECK (intentos_codigo BETWEEN 0 AND 10),
    CONSTRAINT ck_solicitudes_preaprobada CHECK (
        estado <> 'preaprobada' OR (preaprobada_en IS NOT NULL AND vence_en IS NOT NULL)
    ),
    CONSTRAINT ck_solicitudes_codigo_completo CHECK ((codigo_hash IS NULL) = (codigo_generado_en IS NULL)),
    CONSTRAINT ck_solicitudes_codigo_solo_preaprobada CHECK (codigo_hash IS NULL OR estado = 'preaprobada'),
    CONSTRAINT ck_solicitudes_version CHECK (version >= 1)
);
-- Índice ÚNICO PARCIAL: un estudiante solo puede tener UNA reclamación
-- abierta por objeto. Lo garantiza la base de datos, no solo Python.
CREATE UNIQUE INDEX ux_solicitudes_abierta_por_usuario ON solicitudes (objeto_id, solicitante_id)
    WHERE estado IN ('pendiente', 'preaprobada');
-- Índice ÚNICO PARCIAL: como máximo UNA reclamación pre-aprobada por objeto.
-- Aunque dos encargados aprueben al mismo tiempo, la segunda falla aquí.
CREATE UNIQUE INDEX ux_solicitudes_una_preaprobada ON solicitudes (objeto_id)
    WHERE estado = 'preaprobada';
CREATE INDEX ix_solicitudes_objeto ON solicitudes (objeto_id, estado);
CREATE INDEX ix_solicitudes_solicitante ON solicitudes (solicitante_id, created_at DESC);
CREATE INDEX ix_solicitudes_reporte_perdida ON solicitudes (reporte_perdida_id) WHERE reporte_perdida_id IS NOT NULL;
CREATE INDEX ix_solicitudes_revisor ON solicitudes (revisado_por_id) WHERE revisado_por_id IS NOT NULL;
CREATE INDEX ix_solicitudes_pendientes ON solicitudes (created_at) WHERE estado = 'pendiente';
CREATE INDEX ix_solicitudes_vencimiento ON solicitudes (vence_en) WHERE estado = 'preaprobada';

-- Acta de entrega: registro definitivo de que un objeto salió de la oficina.
-- Una entrega nunca se modifica ni se borra (ver permisos en 06_permisos.sql).
CREATE TABLE entregas (
    id               INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    objeto_id        INTEGER      NOT NULL,
    solicitud_id     INTEGER      NOT NULL,
    entregado_por_id INTEGER      NOT NULL,
    carne_verificado BOOLEAN      NOT NULL,
    prueba_propiedad VARCHAR(300) NOT NULL,
    observaciones    VARCHAR(300) NOT NULL DEFAULT '',
    entregado_en     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- objeto_id se puede deducir de la solicitud; se guarda igual para poder
    -- exigir "un objeto se entrega UNA sola vez" (UNIQUE). La clave foránea
    -- compuesta impide que objeto_id y solicitud_id no coincidan
    -- ("redundancia controlada": la copia nunca puede quedar inconsistente).
    CONSTRAINT fk_entregas_solicitud FOREIGN KEY (solicitud_id, objeto_id)
        REFERENCES solicitudes (id, objeto_id),
    CONSTRAINT fk_entregas_entregado_por FOREIGN KEY (entregado_por_id) REFERENCES usuarios (id),
    CONSTRAINT uq_entregas_objeto UNIQUE (objeto_id),
    CONSTRAINT uq_entregas_solicitud UNIQUE (solicitud_id),
    CONSTRAINT ck_entregas_carne CHECK (carne_verificado),
    CONSTRAINT ck_entregas_prueba CHECK (char_length(btrim(prueba_propiedad)) BETWEEN 5 AND 300)
);
CREATE INDEX ix_entregas_entregado_por ON entregas (entregado_por_id, entregado_en DESC);


-- ---------------------------------------------------------------------
-- Notificaciones (lo que también se envía por correo)
-- ---------------------------------------------------------------------

CREATE TABLE notificaciones (
    id                INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id        INTEGER      NOT NULL,
    tipo              VARCHAR(40)  NOT NULL,
    titulo            VARCHAR(120) NOT NULL,
    mensaje           VARCHAR(500) NOT NULL,
    -- Página interna de la aplicación (nunca una URL externa)
    enlace            VARCHAR(200) NOT NULL DEFAULT '',
    leida_en          TIMESTAMPTZ  NULL,
    correo_enviado_en TIMESTAMPTZ  NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_notificaciones_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    CONSTRAINT ck_notificaciones_enlace_interno CHECK (enlace = '' OR enlace ~ '^[a-z0-9-]+\.html(\?[a-zA-Z0-9=&_-]*)?$')
);
CREATE INDEX ix_notificaciones_usuario ON notificaciones (usuario_id, created_at DESC);
CREATE INDEX ix_notificaciones_no_leidas ON notificaciones (usuario_id) WHERE leida_en IS NULL;


-- ---------------------------------------------------------------------
-- Auditoría
-- ---------------------------------------------------------------------

-- Una fila por cada INSERT/UPDATE/DELETE en las tablas auditadas. La llena
-- SOLO la función fn_auditoria() (trigger); la aplicación no tiene permiso
-- para insertar, modificar ni borrar aquí (ver 06_permisos.sql).
CREATE TABLE auditoria (
    id                 BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla              VARCHAR(63) NOT NULL,
    registro_id        BIGINT      NULL,
    operacion          VARCHAR(10) NOT NULL,
    -- Sin clave foránea a propósito: la auditoría no debe depender de otras
    -- tablas ni impedir nada. NULL = acción del sistema o sin sesión.
    usuario_id         INTEGER     NULL,
    ip                 INET        NULL,
    datos_anteriores   JSONB       NULL,
    datos_nuevos       JSONB       NULL,
    campos_modificados TEXT[]      NULL,
    -- Agrupa los cambios hechos en una misma transacción (por ejemplo, una
    -- entrega modifica objetos, solicitudes y entregas al mismo tiempo).
    transaccion_id     BIGINT      NOT NULL DEFAULT (pg_current_xact_id()::text::bigint),
    fecha              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_auditoria_operacion CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE'))
);
CREATE INDEX ix_auditoria_registro ON auditoria (tabla, registro_id);
CREATE INDEX ix_auditoria_usuario ON auditoria (usuario_id, fecha DESC);
-- Índice BRIN: ideal para tablas que solo crecen en orden de tiempo. Ocupa
-- una fracción del espacio de un B-tree y sirve para filtrar por rango de fechas.
CREATE INDEX ix_auditoria_fecha ON auditoria USING brin (fecha);
