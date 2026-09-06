# AUTHORIZATION.md — Autorización en EncuentraU v1.0

## Roles

| Rol | Permisos |
|---|---|
| `ciudadano` | CRUD de sus propios reportes, ver reportes públicos de otros, crear/cancelar sus propias solicitudes, ver solicitudes recibidas sobre sus propios reportes |
| `administrador` | Todo lo anterior + ver y gestionar todos los reportes (cualquier estado), aprobar/rechazar cualquier solicitud, ver/gestionar usuarios (rol, activo) |

El rol se guarda en `usuarios.rol` y **siempre se relee de la base de datos** en cada petición (`middlewares/autorizacion.py`); nunca se confía en un valor enviado por el cliente (body, header, cookie propia).

## Decoradores (`backend/app/middlewares/autorizacion.py`)

```python
@login_requerido   # exige sesión válida; pasa el objeto Usuario como primer argumento
@admin_requerido    # exige sesión válida Y rol == 'administrador'
```

Ambos: si no hay `usuario_id` en sesión → 401. Si el usuario fue borrado/desactivado desde que inició sesión → se limpia la sesión y 401. `admin_requerido` además exige `usuario.rol == 'administrador'` → si no, 403.

## Ownership (IDOR)

Cada endpoint que modifica un recurso específico verifica que el usuario actual es su dueño (o admin) **antes** de aplicar el cambio:

- `objetos_controller._es_dueno_o_admin(objeto, usuario)` — usado en `actualizar`, `cancelar`, `solicitudes_del_objeto`.
- `solicitudes_controller.cancelar` — compara `solicitud.solicitante_id` contra el usuario actual.
- `usuarios_admin_controller` — solo accesible con `admin_requerido`; además, un admin no puede modificar su propia fila (`usuarios_admin_service.actualizar_usuario`), para evitar que se quite su propio rol o se desactive por accidente y deje el sistema sin administradores.

Un intento de acceso sin permiso retorna **403**, nunca 404 (el recurso sí existe, solo no está permitido) — excepto cuando el recurso realmente no existe, que sí retorna 404.

## Mass assignment

Cada endpoint de escritura acepta solo una **whitelist explícita** de campos, nunca el body completo:

| Endpoint | Campos aceptados |
|---|---|
| `POST /api/auth/registro` | nombre, apellido, correo, contraseña — **nunca `rol`** |
| `PUT /api/objetos/:id` | `CAMPOS_EDITABLES` en `objetos_service.py`: nombre, categoría, descripción, ubicación, fecha, imagen — **nunca `estado` ni `usuario_id`** |
| `PUT /api/admin/usuarios/:id` | solo `rol` y/o `activo` |

## El frontend nunca es la autoridad

`frontend/public/js/sesion.js` (`protegerPagina`) redirige a un usuario sin sesión o sin rol admin fuera de una página protegida — esto es **solo experiencia de usuario**. La prueba real de que la autorización funciona es que el backend, probado directamente sin pasar por el frontend (toda la suite de `pytest`), rechaza exactamente las mismas peticiones.

## Evidencia

Ver `docs/REGLAS_100.md` categoría B (RU-016 a RU-030) para el detalle regla por regla con su evidencia citada, y `docs/evidencia/` para las ejecuciones reales (pytest + E2E con navegador).
