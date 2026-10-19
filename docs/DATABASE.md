# DATABASE.md — Base de datos de EncuentraU v2.0

Este documento describe la base de datos **tal como está implementada** en `backend/migrations/sql/` y verificada por `backend/tests/integration/test_esquema_bd.py` y `test_concurrencia.py` (evidencia: `docs/evidencia/pytest_v2.0.txt`).

## 1. Motor y usuarios

- **PostgreSQL** en todos los entornos: desarrollo, pruebas y producción (Supabase). SQLite ya no se usa: no tiene procedimientos almacenados, permisos ni RLS. La aplicación se niega a arrancar si `DATABASE_URL` no es PostgreSQL (`Config.validar_configuracion`).
- **ORM**: SQLAlchemy 2 (Flask-SQLAlchemy). **Migraciones**: Alembic (Flask-Migrate). La única migración, `0001_esquema_v2_postgresql.py`, ejecuta en orden los archivos SQL de `backend/migrations/sql/` dentro de **una sola transacción**: si un archivo falla, no se aplica nada.

Dos usuarios de base de datos (principio de **mínimo privilegio**):

| Usuario | Lo usa | Puede |
|---|---|---|
| `encuentrau` (dueño) | migraciones (`DATABASE_URL_MIGRACIONES`) y respaldos | crear tablas, triggers, procedimientos |
| `encuentrau_app` | la aplicación web (`DATABASE_URL`) | solo lo de `06_permisos.sql`: leer, insertar y actualizar columnas concretas. **Nunca** borrar filas, tocar la auditoría, crear tablas ni desactivar triggers |

Se crean con `database/scripts/crear_bd_local.sql` (ver README).

## 2. Archivos del esquema

| Archivo | Contenido |
|---|---|
| `01_tablas.sql` | 14 tablas, claves, restricciones CHECK/UNIQUE/FK e índices |
| `02_funciones_triggers.sql` | triggers: `updated_at`, máquina de estados, reglas contra el abuso, marcado de cuentas, auditoría e inmutabilidad de la auditoría |
| `03_procedimientos.sql` | procedimientos almacenados del negocio (recepción, pre-aprobación, rechazo, entrega, cierre) y la función de vencimiento de reservas |
| `04_vistas.sql` | vistas para estadísticas e integración |
| `05_datos_iniciales.sql` | roles, estados, transiciones, parámetros, categorías y ubicaciones (idempotente) |
| `06_permisos.sql` | permisos de `encuentrau_app`, Row Level Security y endurecimiento para Supabase (idempotente) |
| `00_eliminar.sql` | `flask db downgrade base` (borra todo; solo desarrollo) |

## 3. Normalización (hasta 3FN)

Diagrama entidad-relación: `docs/DIAGRAMAS.md`, sección 1.

- **1FN**: cada columna guarda un valor atómico; no hay listas dentro de un campo ni columnas repetidas.
- **2FN**: en las tablas con clave compuesta (`estados_objeto (tipo, codigo)`, `transiciones_objeto (tipo, estado_origen, estado_destino)`), cada atributo depende de la clave **completa** (el nombre "Cerrado" depende del par tipo + código).
- **3FN**: sin dependencias transitivas. Ejemplo: en v1.0 cada reporte guardaba el **texto** de su categoría y de su ubicación; en v2.0 guarda `categoria_id` y `ubicacion_id`, y el nombre vive una sola vez en `categorias` / `ubicaciones`. Renombrar una categoría la cambia en todos los reportes sin tocar ninguno (probado en `test_crear_y_renombrar_categoria`).
- **Redundancia controlada** (decisión consciente): `entregas.objeto_id` se podría deducir de la solicitud, pero se guarda para poder exigir `UNIQUE (objeto_id)` ("un objeto se entrega una sola vez"). Una **clave foránea compuesta** `(solicitud_id, objeto_id) → solicitudes (id, objeto_id)` impide que la copia quede inconsistente (probado en `test_entrega_con_objeto_que_no_coincide_con_la_solicitud`).

**Claves**: los catálogos fijos del sistema (roles, estados) usan su código como clave natural (`'estudiante'`, `'en_oficina'`), para que las consultas sean legibles. Los catálogos que el administrador puede renombrar (categorías, ubicaciones) usan clave sustituta (`id`).

## 4. Tablas

| Tabla | Para qué |
|---|---|
| `roles` | estudiante, encargado, administrador |
| `estados_objeto` | estados por tipo de reporte, con `es_inicial` / `es_final` |
| `transiciones_objeto` | máquina de estados como datos: origen → destino y quién puede pedirlo (`estudiante`, `encargado`, `sistema`) |
| `estados_solicitud` | estados de una reclamación, con `es_abierta` y `cuenta_como_rechazo` |
| `parametros` | reglas ajustables: `max_solicitudes_abiertas` (3), `max_rechazos` (3), `horas_vigencia_retiro` (72), `max_intentos_codigo` (5), cada una con su rango |
| `categorias`, `ubicaciones` | catálogos editables (nada se borra: se desactiva) |
| `usuarios` | cuentas; `correo_verificado_en`, `marcado_revision` |
| `tokens_usuario` | tokens de verificación y recuperación (solo el **hash** SHA-256) |
| `objetos` | reportes; parte pública (`nombre`, categoría, ubicación, fecha) y privada (`descripcion`, `detalle_ubicacion`, `observaciones_custodia`); `version` para concurrencia optimista |
| `solicitudes` | reclamaciones a ciegas; ventana de retiro (`vence_en`); código de retiro (solo su HMAC) e intentos |
| `entregas` | acta de entrega (carné verificado, prueba de propiedad); nunca se modifica |
| `notificaciones` | avisos en la aplicación (y si se enviaron por correo) |
| `auditoria` | todos los cambios de las tablas importantes (la llena un trigger) |

Restricciones destacadas (todas en `01_tablas.sql`):
- **CHECK**: correo en minúsculas y con formato; longitudes; `fecha_evento` no futura respecto a la fecha de creación (hora de Colombia); recepción completa (`recibido_por_id` y `recibido_en` juntos); `carne_verificado` debe ser verdadero; intentos de código en rango; una solicitud pre-aprobada debe tener su ventana de retiro.
- **FK compuesta** `objetos (tipo, estado) → estados_objeto (tipo, codigo)`: un objeto perdido nunca puede quedar "en_oficina" (`test_fk_compuesta_impide_un_estado_de_otro_tipo`).
- **UNIQUE**: correo; nombre de categoría/ubicación sin importar mayúsculas (índice único sobre `lower(nombre)`); hash de token; `entregas.objeto_id`; `entregas.solicitud_id`.

## 5. Índices

PostgreSQL crea índice para PK y UNIQUE, pero **no para las claves foráneas**: se crearon a mano. Tipos usados (todos verificados en `test_indices_especiales_existen`):

| Tipo | Ejemplo | Por qué |
|---|---|---|
| B-tree en FK | `ix_objetos_usuario (usuario_id, created_at DESC)` | JOINs y "mis reportes" ordenados |
| Compuesto | `ix_objetos_tipo_estado_fecha (tipo, estado, fecha_evento DESC)` | listado del encargado |
| **Parcial** | `ix_objetos_disponibles … WHERE tipo='encontrado' AND estado IN ('en_oficina','reservado')` | la búsqueda de los estudiantes solo recorre lo que está en la oficina |
| **Único parcial** | `ux_solicitudes_abierta_por_usuario (objeto_id, solicitante_id) WHERE estado IN ('pendiente','preaprobada')` | una reclamación abierta por objeto y persona |
| **Único parcial** | `ux_solicitudes_una_preaprobada (objeto_id) WHERE estado='preaprobada'` | como máximo una pre-aprobada por objeto, aunque dos encargados actúen a la vez |
| Sobre expresión | `ux_categorias_nombre (lower(nombre))` | "Ropa" y "ropa" son la misma categoría |
| **GIN de trigramas** (`pg_trgm`) | `ix_objetos_nombre_trgm` | acelera `ILIKE '%celu%'`, que un B-tree no puede usar (`test_la_busqueda_por_texto_puede_usar_el_indice_de_trigramas` muestra el plan con `EXPLAIN`) |
| **BRIN** | `ix_auditoria_fecha` | tabla que solo crece en orden de tiempo: índice diminuto para filtrar por fechas |

## 6. Triggers (`02_funciones_triggers.sql`)

| Trigger | Cuándo | Qué hace |
|---|---|---|
| `trg_*_updated_at` | BEFORE UPDATE | mantiene `updated_at` |
| `trg_objetos_validar_estado` | BEFORE INSERT/UPDATE en `objetos` | todo reporte nace en el estado inicial de su tipo; solo se permiten las transiciones de `transiciones_objeto`; no se puede cambiar el tipo ni el autor (`test_trigger_rechaza_transiciones_no_permitidas`) |
| `trg_solicitudes_validar_nueva` | BEFORE INSERT en `solicitudes` | solo estudiantes verificados y no marcados; objeto en la oficina; no propio; máximo de reclamaciones abiertas; el reporte de pérdida vinculado debe ser propio; fuerza el estado inicial. Bloquea filas en orden fijo (objeto → usuario) para que dos peticiones simultáneas no se salten el límite (`test_el_limite_tambien_lo_exige_la_base_de_datos`) |
| `trg_solicitudes_marcar_rechazos` | AFTER UPDATE OF estado | al llegar a `max_rechazos` reclamaciones rechazadas, marca la cuenta en revisión (`test_tres_rechazos_ponen_la_cuenta_en_revision`) |
| `trg_auditoria_<tabla>` | AFTER INSERT/UPDATE/DELETE en 8 tablas | escribe en `auditoria` |
| `trg_auditoria_sin_modificar` / `trg_auditoria_sin_vaciar` | BEFORE UPDATE/DELETE/TRUNCATE en `auditoria` | la auditoría es de solo inserción, incluso para el dueño (`test_auditoria_es_inmutable_incluso_para_el_dueno`) |

Los errores de reglas del negocio usan `ERRCODE 'P0001'` con un mensaje en español; la aplicación lo muestra tal cual (HTTP 409).

## 7. Auditoría

Cada fila de `auditoria` guarda: tabla, id del registro, operación, **quién** (`usuario_id`), **desde dónde** (`ip`), **qué había antes y qué quedó** (`datos_anteriores` / `datos_nuevos` en JSONB), la lista de `campos_modificados` y el `transaccion_id` (agrupa los cambios de una misma operación, por ejemplo una entrega que toca tres tablas).

- **Quién**: al inicio de cada transacción la aplicación ejecuta `set_config('app.usuario_id', '<id>', true)` (`backend/app/auditoria_contexto.py`); el `true` limita el valor a esa transacción. Las acciones de terminal quedan como "Sistema".
- **Secretos**: nunca se copian los hashes (`password_hash`, `token_hash`, `codigo_hash`); si cambian, sí queda registrado que cambiaron (`test_cambio_de_contrasena_queda_auditado_sin_el_hash`).
- **`SECURITY DEFINER`**: `fn_auditoria()` se ejecuta con los permisos de su dueño, con `search_path` fijo. Así `encuentrau_app` genera auditoría sin tener permiso de `INSERT` (ni `UPDATE`/`DELETE`) sobre la tabla.
- Se consulta desde el panel del administrador (vista `v_auditoria_detallada`, con el nombre de cada persona).

## 8. Procedimientos almacenados y ACID (`03_procedimientos.sql`)

| Procedimiento | Qué hace (todo o nada) |
|---|---|
| `sp_registrar_recepcion` | el encargado confirma que el objeto está en la oficina |
| `sp_preaprobar_solicitud` | reserva el objeto y abre la ventana de retiro |
| `sp_rechazar_solicitud` | rechaza; si estaba pre-aprobada, el objeto vuelve a la oficina |
| `sp_registrar_entrega` | valida ventana, código (HMAC) e intentos, carné y prueba; crea el acta, entrega, descarta las demás reclamaciones y marca como recuperado el reporte de pérdida vinculado |
| `sp_cerrar_objeto` | cierre por la oficina, descartando reclamaciones pendientes |
| `fn_vencer_reservas()` | función (devuelve filas) que libera las reservas vencidas |

Cada uno vuelve a comprobar en la base de datos que quien actúa es un **encargado activo** (`fn_exigir_encargado`, defensa en profundidad; `test_la_base_de_datos_tambien_exige_el_rol_encargado`).

**ACID** en la práctica:
- **Atomicidad**: si la entrega falla a mitad de camino (por ejemplo, carné no verificado), no queda nada a medias (`test_atomicidad_un_error_deshace_todo_el_procedimiento`).
- **Consistencia**: CHECK, FK, índices únicos y triggers se validan en cada sentencia.
- **Aislamiento**: nivel `READ COMMITTED` (el de PostgreSQL por defecto) más bloqueo explícito de filas.
- **Durabilidad**: PostgreSQL escribe el WAL antes de confirmar el `COMMIT`.

**Concurrencia**:
- **Pesimista**: `SELECT … FOR UPDATE` dentro de los procedimientos y en `solicitudes_service` (`with_for_update()`). Con dos conexiones reales a la vez, la segunda espera a la primera y luego ve el estado ya cambiado (`test_dos_encargados_entregan_el_mismo_objeto_al_tiempo`, `test_dos_encargados_preaprueban_reclamaciones_distintas_al_tiempo`).
- **Orden fijo de bloqueo** (objeto → solicitudes → usuario) en todos los procedimientos y triggers, para no formar ciclos de espera (deadlocks). Si aun así ocurriera uno, la API responde 409 "intenta de nuevo".
- **Optimista**: columna `version` en `objetos` y `solicitudes` (`version_id_col` de SQLAlchemy). Una edición con una versión vieja recibe 409 en vez de pisar el cambio de otra persona (`test_editar_con_version_vieja_devuelve_conflicto`, `test_concurrencia_optimista_en_el_orm`).
- **Garantía final en la base**: el índice único parcial impide dos pre-aprobadas aunque alguien escribiera directo en la tabla (`test_indice_unico_parcial_impide_dos_preaprobadas`).

## 9. Vistas (`04_vistas.sql`)

| Vista | Uso |
|---|---|
| `v_objetos_disponibles` | objetos en la oficina con solo columnas públicas |
| `v_estadisticas_generales` | indicadores (usa `count(*) FILTER (WHERE …)`) |
| `v_estadisticas_mensuales` | actividad por mes (hora de Colombia) |
| `v_desempeno_encargados` | recepciones, pre-aprobaciones, rechazos y entregas por encargado (control del administrador) |
| `v_auditoria_detallada` | auditoría con el nombre de quién hizo cada cambio |

## 10. Permisos, RLS y Supabase (`06_permisos.sql`)

- **Permisos por columna**: `encuentrau_app` no puede cambiar el correo de un usuario, el autor o el tipo de un reporte, ni el texto de una reclamación ya enviada. Las actas de entrega solo admiten `INSERT`. La auditoría solo admite `SELECT`. Los procedimientos no se pueden ejecutar por `PUBLIC`. Doce intentos prohibidos se prueban en `test_la_aplicacion_no_tiene_permiso` (todos devuelven `42501 insufficient_privilege`).
- **Row Level Security** activo en las 14 tablas, con una política solo para `encuentrau_app` (`test_rls_activo_en_todas_las_tablas`).
- **Supabase** expone automáticamente las tablas del esquema `public` por su API REST a los roles `anon` y `authenticated`. EncuentraU no usa esa API: si esos roles existen, se les revocan todos los permisos y, sin política RLS, no ven ninguna fila. *(VERIFICADO en Supabase el 2026-10-19: `anon` y `authenticated` sin ningún privilegio sobre las tablas de `public`.)*

## 11. Respaldos

- **Local**: `database/scripts/respaldo.py` (`pg_dump -Fc`, guarda los N más recientes en `database/respaldos/`, ignorada por git) y `database/scripts/restaurar.py` (`pg_restore --clean --single-transaction`, exige `--confirmar`). **VERIFICADO**: respaldo de la base de desarrollo restaurado en la de pruebas con los mismos conteos de usuarios, objetos, reclamaciones, entregas, auditoría y triggers (`docs/evidencia/respaldo_restauracion_v2.0.txt`). Después de restaurar hay que volver a ejecutar `06_permisos.sql`.
- **En la nube**: `.github/workflows/respaldo-bd.yml` ejecuta el respaldo cada día desde GitHub Actions, lo **cifra con AES-256** (los artifacts de un repositorio público los puede descargar cualquiera) y lo guarda 30 días. Supabase gratuito no ofrece respaldos descargables. *(IMPLEMENTADO: requiere los secretos `SUPABASE_DB_URL` y `BACKUP_PASSPHRASE`; todavía no se ha ejecutado.)*

## 12. Integración con otras aplicaciones

- **API REST** documentada en `docs/API.md`.
- **Exportación CSV** para Excel (`/api/admin/exportar/*.csv`), sin datos personales y protegida contra inyección de fórmulas (`test_exportar_csv_sin_datos_personales_y_seguro_para_excel`).
- **Herramientas de análisis** (Power BI, Looker Studio, Excel): `database/scripts/crear_rol_lector.sql` crea `encuentrau_lector`, que solo puede leer las vistas de estadísticas. *(IMPLEMENTADO, no ejecutado.)*
- **Correo**: Brevo por API HTTPS (`backend/app/services/correo_service.py`). *(IMPLEMENTADO: en desarrollo y pruebas se usan los modos "consola" y "memoria".)*
- **CI en la nube**: `.github/workflows/pruebas.yml` levanta PostgreSQL en GitHub Actions y ejecuta pytest en cada push. *(VERIFICADO: primera ejecución exitosa en `main` el 2026-10-19, https://github.com/sebastquintero1312/EncuentraU/actions/runs/39299522079.)*

## 13. Ver la base de datos

- **pgAdmin 4** (viene con la instalación de PostgreSQL): servidor `localhost:5432`, base `encuentrau_dev`, usuario `encuentrau` (contraseña en `backend/.env`, `DATABASE_URL_MIGRACIONES`).
- **psql**: `& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U encuentrau -d encuentrau_dev`
- **Supabase** (producción): *Table Editor* y *SQL Editor* del panel.

Consultas útiles: `SELECT * FROM v_auditoria_detallada ORDER BY id DESC LIMIT 20;` · `SELECT * FROM v_estadisticas_generales;` · `\d objetos` (estructura, índices y triggers de una tabla).
