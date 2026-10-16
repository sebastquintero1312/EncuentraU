# API.md — Referencia de la API REST de EncuentraU v2.0

Todos los endpoints viven bajo `/api`. El frontend se sirve desde el mismo origen que la API (Flask sirve `frontend/public` como estático), así que en producción no hace falta CORS.

> La prueba `backend/tests/unit/test_documentacion_api.py` compara esta tabla con las rutas reales de Flask: si se agrega, quita o renombra un endpoint sin actualizar este archivo, la prueba falla.

**Formato de respuestas**: listas → `{datos, total, pagina, por_pagina}`; recurso único → `{mensaje, <recurso>}`; error → `{mensaje, errores?}`. Paginación: `pagina` (≥ 1) y `por_pagina` (1–50).

**CSRF**: todo `POST`/`PUT` requiere el header `X-CSRFToken`, obtenido de `GET /api/auth/csrf-token`. Sin él, la petición falla con 400. Login y logout devuelven un `csrf_token` nuevo (la sesión se regenera).

**Columna "Acceso"** (se verifica en el backend en cada petición; el rol se relee de la base de datos):

| Valor | Significa |
|---|---|
| Pública | sin sesión |
| Sesión | cualquier usuario con sesión iniciada (401 sin sesión) |
| Estudiante / Encargado / Admin | solo ese rol (401 sin sesión, 403 con otro rol) |

---

## Autenticación (`/api/auth`)

| Método | Ruta | Acceso | Límite | Descripción |
|---|---|---|---|---|
| GET | `/api/auth/csrf-token` | Pública | — | `{csrf_token}` |
| POST | `/api/auth/registro` | Pública | 5/min | Crea una cuenta de **estudiante** sin verificar y envía el enlace de verificación. Solo correos `@sanmateo.edu.co`. Con datos válidos responde lo mismo exista o no la cuenta (si ya existía, se avisa al dueño por correo) |
| POST | `/api/auth/login` | Pública | 10/min | `{correo, contrasena}`. 401 genérico si falla. 403 con `codigo: "correo_no_verificado"` si la contraseña es correcta pero el correo no está verificado |
| POST | `/api/auth/logout` | Pública | — | Cierra la sesión |
| GET | `/api/auth/sesion` | Pública | — | `{usuario: {...} \| null}` |
| POST | `/api/auth/verificar-correo` | Pública | 10/min | `{token}` del enlace del correo. Un solo uso, vence en 24 h |
| POST | `/api/auth/reenviar-verificacion` | Pública | 3 cada 10 min | `{correo}`. Respuesta genérica |
| POST | `/api/auth/recuperar` | Pública | 5/min | `{correo}`. Envía un enlace de un solo uso (30 min). Respuesta genérica |
| POST | `/api/auth/restablecer` | Pública | 5/min | `{token, contrasena, confirmar_contrasena}` |

## Comunes (`/api`)

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/api/catalogos` | Sesión | Categorías y ubicaciones **activas**, y los estados por tipo de reporte |
| GET | `/api/estadisticas/publicas` | Pública | Solo dos números: `{en_custodia, entregados}` |
| GET | `/api/notificaciones` | Sesión | Notificaciones propias (máx. 50). `?no_leidas=1` filtra. Incluye `no_leidas` (contador) |
| POST | `/api/notificaciones/<id>/leida` | Sesión | Marca una notificación propia como leída (404 si es de otra persona) |
| POST | `/api/notificaciones/leer-todas` | Sesión | Marca todas como leídas |

## Estudiante — reportes (`/api/objetos`, `/api/mis-reportes`)

| Método | Ruta | Acceso | Límite | Descripción |
|---|---|---|---|---|
| GET | `/api/objetos` | Estudiante | — | Búsqueda: **solo objetos encontrados que están en la oficina** (`en_oficina`, `reservado`) y **solo datos públicos**. Filtros: `q` (nombre), `categoria_id`, `ubicacion_id`, `desde`, `hasta` (AAAA-MM-DD) |
| POST | `/api/objetos` | Estudiante | 20/hora | Crea un reporte. Body: `tipo` (`perdido`\|`encontrado`), `nombre`, `categoria_id`, `ubicacion_id`, `fecha_evento` (no futura), `descripcion` (privada, 10–500), `detalle_ubicacion?` |
| GET | `/api/objetos/<id>` | Sesión | — | Dueño del reporte → con su descripción privada (`es_propio: true`). Otro estudiante → solo datos públicos y solo si está en la oficina (si no, 403); incluye `reclamacion_abierta_id`. Encargado/admin → vista completa |
| PUT | `/api/objetos/<id>` | Estudiante (dueño) | — | Edita mientras el reporte está en su estado inicial. Exige `version` (la que se leyó): si no coincide → **409** (concurrencia optimista). Whitelist: `nombre, categoria_id, ubicacion_id, fecha_evento, descripcion, detalle_ubicacion` |
| POST | `/api/objetos/<id>/cancelar` | Estudiante (dueño) | — | Cancela si la transición lo permite (`buscando` o `pendiente_entrega`) |
| GET | `/api/objetos/<id>/coincidencias` | Estudiante (dueño) | — | Para un reporte de pérdida: objetos en la oficina parecidos (solo datos públicos, puntaje calculado sin la descripción privada) |
| GET | `/api/mis-reportes` | Estudiante | — | Reportes propios. Filtros: `tipo`, `estado` |

## Estudiante — reclamaciones (`/api/solicitudes`, `/api/mis-solicitudes`)

| Método | Ruta | Acceso | Límite | Descripción |
|---|---|---|---|---|
| POST | `/api/solicitudes` | Estudiante | 10/hora | Reclamación a ciegas. Body: `objeto_id`, `descripcion` (20–500), `lugar_perdida`, `fecha_perdida`, `evidencia?`, `reporte_perdida_id?` (debe ser un reporte de pérdida PROPIO). Reglas (también en un trigger de PostgreSQL): objeto en la oficina, no propio, una abierta por objeto, máximo N abiertas, cuenta no marcada en revisión |
| GET | `/api/mis-solicitudes` | Estudiante | — | Reclamaciones propias (el objeto se muestra solo con datos públicos). Antes libera las reservas vencidas |
| POST | `/api/solicitudes/<id>/cancelar` | Estudiante (solicitante) | — | Cancela una reclamación abierta; si estaba pre-aprobada, el objeto vuelve a estar disponible |
| POST | `/api/solicitudes/<id>/codigo` | Estudiante (solicitante) | 5/hora | Solo si está pre-aprobada y no vencida. Devuelve `{codigo, vence_en}` **una sola vez** (en la base solo queda su HMAC). Generar otro invalida el anterior y reinicia los intentos |

## Encargado de la oficina (`/api/encargado`)

| Método | Ruta | Acceso | Límite | Descripción |
|---|---|---|---|---|
| GET | `/api/encargado/objetos` | Encargado | — | Todos los reportes con detalles privados. Filtros: `tipo`, `estado`, `categoria_id`, `q` (nombre o descripción) |
| GET | `/api/encargado/objetos/<id>` | Encargado | — | `{objeto, solicitudes, entrega, coincidencias}` |
| POST | `/api/encargado/objetos/<id>/recepcion` | Encargado | — | `{observaciones?}`. `pendiente_entrega` → `en_oficina` (procedimiento `sp_registrar_recepcion`). Avisa a quien lo encontró y a los dueños de reportes de pérdida parecidos |
| POST | `/api/encargado/objetos/<id>/cerrar` | Encargado | — | `{motivo}` (5–300). Descarta las reclamaciones pendientes (`sp_cerrar_objeto`). No se puede cerrar un objeto reservado |
| POST | `/api/encargado/objetos/<id>/entrega` | Encargado | 30/hora | Entrega presencial: `{codigo, carne_verificado: true, prueba_propiedad, observaciones?}` (`sp_registrar_entrega`). Código incorrecto → 400 y se descuenta un intento; al agotar los intentos el código se invalida |
| GET | `/api/encargado/solicitudes` | Encargado | — | Cola de reclamaciones, las más antiguas primero. `?estado=` (por defecto `pendiente`; `todas` para todas) |
| GET | `/api/encargado/solicitudes/<id>` | Encargado | — | La reclamación al lado de los detalles privados del objeto, la evidencia del reporte previo y las demás reclamaciones del mismo objeto |
| POST | `/api/encargado/solicitudes/<id>/preaprobar` | Encargado | — | `{respuesta?}`. El objeto queda reservado durante `horas_vigencia_retiro` (`sp_preaprobar_solicitud`). Solo una pre-aprobada por objeto (409 si ya hay otra) |
| POST | `/api/encargado/solicitudes/<id>/rechazar` | Encargado | — | `{motivo}` (5–300) (`sp_rechazar_solicitud`). Un trigger pone la cuenta en revisión al llegar a `max_rechazos` |
| GET | `/api/encargado/estadisticas` | Encargado | — | Indicadores generales (vista `v_estadisticas_generales`) |

## Administrador (`/api/admin`)

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/api/admin/usuarios` | Admin | Filtros: `q`, `rol`, `marcados=1` |
| PUT | `/api/admin/usuarios/<id>` | Admin | Whitelist `rol` (`estudiante`\|`encargado`, nunca `administrador`) y `activo`. No sobre sí mismo ni sobre otro administrador. Encargado solo con correo verificado |
| POST | `/api/admin/usuarios/<id>/quitar-revision` | Admin | Levanta la marca de una cuenta en revisión |
| GET | `/api/admin/categorias` | Admin | Todas (activas e inactivas) |
| POST | `/api/admin/categorias` | Admin | `{nombre}` (3–50, único sin importar mayúsculas → 409) |
| PUT | `/api/admin/categorias/<id>` | Admin | `{nombre?, activa?}` |
| GET | `/api/admin/ubicaciones` | Admin | Todas |
| POST | `/api/admin/ubicaciones` | Admin | `{nombre, descripcion?}` |
| PUT | `/api/admin/ubicaciones/<id>` | Admin | `{nombre?, descripcion?, activa?}` |
| GET | `/api/admin/parametros` | Admin | Reglas del negocio y su rango permitido |
| PUT | `/api/admin/parametros/<clave>` | Admin | `{valor}` (entero dentro de `minimo..maximo`) |
| GET | `/api/admin/objetos` | Admin | Todos los reportes (solo lectura) |
| GET | `/api/admin/objetos/<id>` | Admin | Detalle completo (solo lectura) |
| GET | `/api/admin/auditoria` | Admin | Filtros: `tabla`, `operacion`, `registro_id`, `usuario_id`, `transaccion_id`, `desde`, `hasta` |
| GET | `/api/admin/estadisticas` | Admin | Generales, mensuales (12 meses) y desempeño de encargados |
| GET | `/api/admin/exportar/objetos.csv` | Admin | CSV sin datos personales ni descripciones privadas (con protección contra inyección de fórmulas) |
| GET | `/api/admin/exportar/estadisticas-mensuales.csv` | Admin | CSV de actividad por mes |

## Otros

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/` | Pública | Sirve `index.html` |
| GET | `/health` | Pública | `{"estado": "ok"}` |
| GET | `/<archivo>` | Pública | Archivos estáticos de `frontend/public/` |

## Estados

**Reportes perdidos**: `buscando` → `recuperado` (al entregarle un objeto) · `cancelado` · `cerrado`.
**Reportes encontrados**: `pendiente_entrega` → `en_oficina` → `reservado` → `entregado`; también `cancelado` (antes de llevarlo) y `cerrado` (por la oficina). Las transiciones permitidas están en la tabla `transiciones_objeto` y un trigger rechaza cualquier otra.
**Reclamaciones**: `pendiente` → `preaprobada` → `entregada`; cierres: `rechazada` (cuenta para la revisión de la cuenta), `cancelada`, `vencida`, `descartada` (el objeto se entregó a otra persona o se cerró).

## Códigos de error

| Código | Cuándo |
|---|---|
| 400 | Validación fallida, CSRF ausente/inválido, JSON malformado, código de retiro incorrecto |
| 401 | Sin sesión donde se requiere |
| 403 | Autenticado pero sin permiso (otro rol, no es dueño); también login con correo sin verificar |
| 404 | Recurso inexistente |
| 409 | Conflicto: regla del negocio aplicada por la base de datos (mensaje en español), versión desactualizada (concurrencia optimista), registro duplicado o bloqueo concurrente |
| 413 | Cuerpo mayor a 1 MB |
| 429 | Límite de peticiones alcanzado |
| 500 | Error interno (nunca expone detalles) |
