# API.md — Referencia de la API REST de EncuentraU v1.0

Todos los endpoints viven bajo `/api`. El frontend se sirve desde el mismo origen que la API (Flask sirve `frontend/public` como estático), así que en producción no hace falta CORS.

**Formato de respuestas**: ver `.claude/skills/api/SKILL.md` sección 4. Listas: `{datos, total, pagina, por_pagina}`. Recurso único: `{mensaje, <recurso>}`. Error: `{mensaje, errores?}`.

**CSRF**: todo endpoint POST/PUT/DELETE requiere el header `X-CSRFToken`, obtenido de `GET /api/auth/csrf-token`. Sin él, la petición falla con 400.

**Auth**: "Sí" = requiere sesión (`login_requerido`). "Admin" = requiere sesión + rol `administrador` (`admin_requerido`). El rol se relee de la base de datos en cada petición, nunca se confía en el cliente.

---

## Autenticación (`/api/auth`)

| Método | Ruta | Auth | Rate limit | Descripción |
|---|---|---|---|---|
| GET | `/api/auth/csrf-token` | No | — | Devuelve `{csrf_token}` |
| POST | `/api/auth/registro` | No | 5/min | Crea una cuenta (rol siempre `ciudadano`, sin importar lo que envíe el cliente) |
| POST | `/api/auth/login` | No | 10/min | Inicia sesión. Devuelve `{mensaje, usuario, csrf_token}` — el `csrf_token` es nuevo porque el login regenera la sesión |
| POST | `/api/auth/logout` | No | — | Cierra sesión. Devuelve un `csrf_token` nuevo por el mismo motivo |
| GET | `/api/auth/sesion` | No | — | `{usuario: {...} \| null}` |
| POST | `/api/auth/recuperar` | No | 5/min | Solicita recuperación. Siempre responde el mismo mensaje genérico, exista o no el correo |
| POST | `/api/auth/restablecer` | No | 5/min | Cambia la contraseña con un token válido de un solo uso |

**Body de registro**: `primer_nombre, segundo_nombre?, primer_apellido, segundo_apellido?, correo, contrasena, confirmar_contrasena`.
**Body de login**: `correo, contrasena`.
**Body de recuperar**: `correo`.
**Body de restablecer**: `token, contrasena, confirmar_contrasena`.

## Objetos — reportes de perdido/encontrado (`/api/objetos`, `/api/mis-reportes`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/objetos` | No | Búsqueda pública. Query: `tipo`, `categoria`, `estado`, `ubicacion`, `q` (nombre/descripción), `pagina`, `por_pagina`. Sin `estado`, solo muestra `activo`/`en_proceso` |
| POST | `/api/objetos` | Sí — 20/hora | Crea un reporte. Body: `tipo` (`perdido`\|`encontrado`), `nombre`, `categoria`, `descripcion`, `ubicacion`, `fecha_evento` (AAAA-MM-DD, no futura), `imagen_url?` (URL http(s) opcional) |
| GET | `/api/objetos/:id` | No | Detalle. Devuelve `{objeto, coincidencias: [...]}` — coincidencias solo si el objeto está activo/en_proceso |
| PUT | `/api/objetos/:id` | Sí (dueño o admin) | Actualiza `nombre, categoria, descripcion, ubicacion, fecha_evento, imagen_url` (whitelist; `estado`/`usuario_id` se ignoran) |
| DELETE | `/api/objetos/:id` | Sí (dueño o admin) | Cancela el reporte (`estado → cancelado`), solo si la transición es válida |
| GET | `/api/objetos/:id/solicitudes` | Sí (dueño o admin) | Solicitudes de reclamación recibidas, con la información privada de verificación |
| GET | `/api/mis-reportes` | Sí | Reportes del usuario actual. Query: `tipo`, `estado`, `pagina`, `por_pagina` |

**Categorías válidas**: `Tecnología, Accesorios, Útiles, Documentos, Ropa, Otro`.
**Estados de un objeto**: `activo, en_proceso, resuelto, cerrado, cancelado`. Transiciones permitidas: `activo → {en_proceso, cancelado, cerrado}`, `en_proceso → {resuelto, activo, cerrado}`. `resuelto`, `cerrado` y `cancelado` son finales.

## Solicitudes — proceso de reclamación (`/api/solicitudes`, `/api/mis-solicitudes`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/api/solicitudes` | Sí — 20/hora | Crea una solicitud. Body: `objeto_id, contacto, mensaje`. Rechaza si el objeto es propio, no admite solicitudes, o ya hay una solicitud abierta del mismo usuario |
| GET | `/api/mis-solicitudes` | Sí | Solicitudes hechas por el usuario actual |
| DELETE | `/api/solicitudes/:id` | Sí (solicitante) | Cancela la propia solicitud (si sigue abierta) |
| GET | `/api/admin/solicitudes` | Admin | Todas las solicitudes. Query: `estado`, `pagina`, `por_pagina` |
| PUT | `/api/admin/solicitudes/:id` | Admin | Aprueba o rechaza. Body: `estado` (`aprobada`\|`rechazada`), `respuesta_admin?` |

**Estados de una solicitud**: `pendiente, en_revision, aprobada, rechazada, cancelada`. Aprobar resuelve el objeto y rechaza automáticamente otras solicitudes abiertas sobre el mismo objeto; rechazar/cancelar la única solicitud abierta reactiva el objeto.

## Administración (`/api/admin`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/admin/usuarios` | Admin | Lista usuarios. Query: `q` (nombre/correo), `rol`, `pagina`, `por_pagina` |
| PUT | `/api/admin/usuarios/:id` | Admin | Cambia `rol` y/o `activo` (whitelist). Un admin no puede modificarse a sí mismo |
| GET | `/api/admin/objetos` | Admin | Lista TODOS los reportes, cualquier estado (a diferencia de `GET /api/objetos`) |
| PUT | `/api/admin/objetos/:id/estado` | Admin | Cambia el estado de un reporte. Body: `estado`. Respeta las transiciones válidas |

## Otros

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | No | Sirve `index.html` (frontend) |
| GET | `/health` | No | `{"estado": "ok"}` — health check mínimo, sin detalles internos |
| GET | `/<archivo>` | No | Sirve cualquier archivo estático de `frontend/public/` (HTML, CSS, JS, imágenes) |

## Códigos de error

| Código | Cuándo |
|---|---|
| 400 | Validación fallida, CSRF ausente/inválido, JSON malformado, transición de estado inválida |
| 401 | Sin sesión donde se requiere |
| 403 | Autenticado pero sin permiso (no es dueño, no es admin) |
| 404 | Recurso inexistente |
| 413 | Cuerpo de la petición mayor a 1 MB (`MAX_CONTENT_LENGTH`) |
| 429 | Rate limit alcanzado |
| 500 | Error interno no controlado (nunca expone detalles) |
