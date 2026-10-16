# AUTHENTICATION.md — Autenticación de EncuentraU v2.0

Código: `backend/app/services/cuentas_service.py`, `auth_service.py`, `controllers/auth_controller.py`, `models/token_usuario.py`. Pruebas: `backend/tests/integration/test_auth.py`, `tests/unit/test_auth_service.py`, `tests/security/test_csrf_rate_limit.py`.

## 1. Registro

- Solo correos del dominio institucional (`DOMINIO_CORREO_INSTITUCIONAL`, por defecto `sanmateo.edu.co`). Un dominio que solo "termina parecido" (`falsosanmateo.edu.co`) se rechaza.
- Toda cuenta nueva es **estudiante** y empieza con el correo **sin verificar**; el rol enviado por el cliente se ignora.
- Contraseña: 12–128 caracteres, mayúscula, minúscula, número y carácter especial; no puede ser común ni contener el nombre o el correo. Se guarda con **Argon2id**.
- **Sin enumeración de cuentas**: con datos válidos, la respuesta es idéntica exista o no el correo. Si ya existía, al dueño le llega un aviso por correo ("alguien intentó registrarse con tu correo"). El hash Argon2 se calcula en ambos casos, para que el tiempo de respuesta tampoco delate nada.

## 2. Verificación del correo institucional

- Al registrarse se envía un enlace `verificar-correo.html?token=…` (vence en 24 h, un solo uso).
- Sin verificar no se puede iniciar sesión: el login devuelve 403 con `codigo: "correo_no_verificado"`, **solo** si la contraseña es correcta (a quien prueba correos no le revela nada).
- `POST /api/auth/reenviar-verificacion` emite un enlace nuevo e invalida el anterior (respuesta genérica, 3 cada 10 min).
- Restablecer la contraseña con un enlace recibido en el buzón también deja el correo verificado.
- `flask verificar-correo <correo>` permite verificarlo desde la terminal del servidor (desarrollo, o si la oficina confirmó la identidad en persona).

## 3. Tokens de un solo uso

- Se generan con `secrets.token_urlsafe(32)`. En `tokens_usuario` se guarda **solo su hash SHA-256**: una copia robada de la base de datos no permite usar los enlaces (`test_en_la_base_solo_se_guarda_el_hash_del_token`).
- Cada token tiene un propósito (`verificacion` o `recuperacion`) y no sirve para el otro.
- Emitir un token nuevo invalida los pendientes del mismo propósito; usarlo lo marca como usado.
- Las páginas que reciben un token lo borran de la barra de direcciones apenas lo leen (`history.replaceState`) y usan `<meta name="referrer" content="no-referrer">`.

## 4. Recuperación de contraseña

`POST /api/auth/recuperar` → enlace `restablecer-contrasena.html?token=…` (30 min, un solo uso) → `POST /api/auth/restablecer`. La respuesta es genérica exista o no el correo. Si la contraseña nueva es débil, el token **no** se gasta y se puede reintentar.

## 5. Sesión

- Cookie de sesión de Flask firmada con `SECRET_KEY`: `HttpOnly`, `SameSite=Lax`, `Secure` en producción, sin fecha de expiración (se borra al cerrar el navegador). Guarda solo `usuario_id` (`test_la_sesion_solo_guarda_el_id_del_usuario`).
- **Login regenera la sesión** (`session.clear()`): el token CSRF anterior deja de servir y se entrega uno nuevo (`test_login_regenera_la_sesion`). Logout también.
- Cada petición protegida relee el usuario de la base de datos: una cuenta desactivada pierde el acceso de inmediato.
- **CSRF** con Flask-WTF en todo `POST`/`PUT` (header `X-CSRFToken`).
- **Límites de peticiones** (Flask-Limiter, por IP): login 10/min, registro 5/min, recuperar/restablecer 5/min, verificación 10/min, reenvío 3/10 min. Detrás del proxy de Render se usa la IP real gracias a `ProxyFix` (`NUM_PROXIES=1`). El almacenamiento del limitador es en memoria (se reinicia con el servidor).

## 6. Correos

`backend/app/services/correo_service.py`, según `CORREO_PROVEEDOR`:
- `consola` (desarrollo): el correo se imprime en la terminal del servidor, enlace incluido.
- `brevo` (obligatorio en producción): API HTTPS de Brevo (el plan gratuito de Render bloquea los puertos SMTP). *(IMPLEMENTADO, no probado contra Brevo todavía.)*
- `memoria` (pruebas automáticas).

Los correos son texto plano (un nombre de objeto escrito por un usuario no puede inyectar HTML). Un fallo de envío nunca rompe la operación: la notificación queda visible en la aplicación.
