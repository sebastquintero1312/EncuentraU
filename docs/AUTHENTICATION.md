# AUTHENTICATION.md — Autenticación en EncuentraU v1.0

## Flujo

1. **Registro** (`POST /api/auth/registro`): valida nombre, apellido, correo (formato + unicidad) y contraseña (política abajo). El rol se fija siempre en `ciudadano` — cualquier `rol` que envíe el cliente se ignora.
2. **Login** (`POST /api/auth/login`): busca por correo, verifica el hash Argon2id, verifica que la cuenta esté `activo`. Mensaje de error idéntico si el correo no existe o si la contraseña es incorrecta (anti user-enumeration). Al iniciar sesión: `session.clear()` (anti session-fixation) → `session['usuario_id'] = usuario.id`. Como `session.clear()` también borra el token CSRF de la sesión anterior, la respuesta de login incluye un `csrf_token` nuevo (ver más abajo).
3. **Sesión** (`GET /api/auth/sesion`): devuelve el usuario actual o `null`, sin filtrar si existe o no un `usuario_id` en la sesión.
4. **Logout** (`POST /api/auth/logout`): `session.clear()` — invalida la sesión por completo. También devuelve un `csrf_token` nuevo.
5. **Recuperación** (`POST /api/auth/recuperar` → `POST /api/auth/restablecer`): genera un token con `secrets.token_urlsafe(32)` (CSPRNG), válido 30 minutos, de un solo uso. El mensaje de "solicitud recibida" es siempre el mismo exista o no el correo. **El envío de correo real no está implementado**: el token se imprime en el log del servidor (`print(...)` en `auth_controller.solicitar_recuperacion`) — limitación conocida, documentada también en `SECURITY.md`.

## Contraseñas

- Hash: **Argon2id** (`argon2-cffi`), parámetros por defecto de la librería.
- Política (validada en backend, `auth_service.validar_contrasena`): mínimo 12 caracteres, al menos una mayúscula, una minúscula, un número, un carácter especial (`!@#$%^&*()_-+=`), no debe ser una contraseña común (lista corta bloqueada), no debe contener el correo ni el nombre del usuario.
- El frontend (`js/contrasena-fortaleza.js`) replica estas reglas solo como ayuda visual — **no es la autoridad**; el backend siempre revalida todo.

## Sesión

- Cookie de sesión de Flask, firmada con `SECRET_KEY`.
- `HttpOnly=True` (JS no puede leerla), `SameSite=Lax`, `Secure` solo en producción (`FLASK_ENV=production`).
- `session.permanent = False`: expira al cerrar el navegador.
- Solo se guarda `usuario_id` en la sesión — nunca contraseñas, tokens ni datos sensibles.

## CSRF y el token que "desaparece" tras login/logout

Flask-WTF guarda el `csrf_token` **dentro de la misma sesión** que `usuario_id`. Como el login y el logout llaman `session.clear()` (necesario para prevenir session fixation), cualquier CSRF token obtenido *antes* de esa llamada deja de ser válido. Para que el frontend no se rompa con la siguiente petición protegida:

- `login` y `logout` generan y devuelven un `csrf_token` nuevo en su respuesta JSON.
- `frontend/public/js/api.js` (`peticionProtegida`) actualiza automáticamente `csrfTokenEnMemoria` cada vez que una respuesta trae un `csrf_token`.

Este era un bug real en el diseño original de v0.25 (nunca se manifestó porque nadie probó una petición protegida inmediatamente después de un login) — encontrado y corregido durante la migración a v1.0. Ver `docs/evidencia/smoke_test_manual_v1.0.md` y `CHANGELOG.md`.

## Qué falta (limitaciones conocidas)

- No se envían correos reales (recuperación de contraseña, confirmación de cuenta).
- No hay verificación de dominio institucional del correo (cualquier dirección con formato válido es aceptada).
- No hay autenticación de dos factores.

Estas limitaciones están fuera del alcance definido para v1.0 por la propia auditoría inicial (`docs/ESTADO_V025.md`) y no bloquean la funcionalidad principal del sistema.
