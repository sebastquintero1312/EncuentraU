# Seguridad de EncuentraU

Versión: **v1.0**

Este documento explica, con honestidad, qué medidas de seguridad están implementadas, cómo funcionan, cómo se probaron y qué limitaciones tienen todavía. Ver también `docs/MATRIZ_SEGURIDAD.md` (revisión OWASP Top 10) y `docs/REGLAS_100.md` (las 100 reglas con evidencia).

## 1. Política de contraseñas

Igual que en v0.25 (sin cambios en la política, solo en el algoritmo de hash — ver sección 2): mínimo 12 caracteres, mayúscula, minúscula, número, carácter especial, sin contraseñas comunes, sin el correo/nombre del usuario. Validado en backend (`backend/app/services/auth_service.py`), el frontend solo ayuda visualmente.

## 2. Hashing de contraseñas — cambio en v1.0

**v0.25** usaba `werkzeug.security.generate_password_hash` (algoritmo `scrypt`). **v1.0 usa Argon2id** (`argon2-cffi`), el algoritmo recomendado actualmente (ganador del Password Hashing Competition). Verificado con `backend/tests/unit/test_auth_service.py`: el hash generado empieza con `$argon2id$`.

## 3. Recuperación de contraseña

Sin cambios de diseño respecto a v0.25 (token con `secrets.token_urlsafe(32)`, expira en 30 minutos, un solo uso, mensaje genérico anti-enumeración). En v1.0 esto se probó con evidencia real, incluyendo forzar la expiración de un token sin esperar 30 minutos (`test_token_recuperacion_expirado_es_rechazado`).

**Limitación honesta, sigue vigente**: no hay envío real de correos. El token se imprime en el log del servidor.

## 4. Rate limiting (Flask-Limiter)

Mismos límites que v0.25 (login 10/min, registro/recuperación/restablecimiento 5/min), más un nuevo límite de 20/hora en creación de reportes y solicitudes (`backend/app/routes/objetos_routes.py`, `solicitudes_routes.py`).

**A diferencia de v0.25** (donde había una nota de incertidumbre sobre si Flask-Limiter llegó a probarse instalado), en v1.0 se verificó con ejecución real: `tests/security/test_csrf_rate_limit.py::test_rate_limit_login` y `test_rate_limit_registro` fuerzan el límite y confirman el código 429.

## 5. Sesión

Sin cambios de diseño. Verificado con una cabecera `Set-Cookie` real: `HttpOnly; Path=/; SameSite=Lax` (confirmado con `curl` contra el servidor real). `Secure` se activa solo si `FLASK_ENV=production` — no verificado todavía en un despliegue HTTPS real.

## 6. CSRF — bug real encontrado y corregido en v1.0

El diseño (Flask-WTF, token en header `X-CSRFToken`) es el mismo de v0.25, pero durante la migración se encontraron y corrigieron **dos bugs reales**, invisibles en v0.25 porque nunca se probó un login seguido de otra petición protegida:

1. **El token CSRF quedaba invalidado tras login/logout.** `session.clear()` (necesario para prevenir session fixation) también borra el `csrf_token` guardado en la sesión. Corregido: login/logout ahora devuelven un `csrf_token` nuevo en su respuesta, y el frontend lo actualiza automáticamente.
2. **Un CSRF ausente/inválido devolvía 500 en vez de 400.** El manejador de errores solo tenía casos específicos para 404/405/429, y el manejador genérico de `Exception` interceptaba cualquier otro `HTTPException` (incluyendo `CSRFError`) antes de que Flask pudiera usar su código HTTP real. Corregido con un manejador explícito para `werkzeug.exceptions.HTTPException`.

Ambos verificados con pruebas automatizadas (`tests/security/test_csrf_rate_limit.py`) y con la prueba manual documentada en `docs/evidencia/smoke_test_manual_v1.0.md`.

## 7. Cabeceras de seguridad — nuevo en v1.0

v0.25 no tenía ninguna cabecera de seguridad además de las de sesión. v1.0 agrega, a cada respuesta:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=63072000; includeSubDomains   (solo en producción)
```

Confirmado con una respuesta HTTP real (`curl -I`) y con la verificación E2E completa (si la CSP hubiera bloqueado algún script del frontend, ninguna de esas 14 verificaciones habría podido completarse).

**Nota sobre `style-src 'unsafe-inline'`**: se mantiene porque varias páginas usan atributos `style="..."` inline para ajustes menores de layout (ej. `style="width:100%"` en botones). Quitarlo requeriría mover esos estilos a clases CSS — mejora posible a futuro, riesgo bajo (no es un vector de XSS ejecutable, solo de inyección de estilos).

## 8. Validación en el backend

Sin cambios de principio respecto a v0.25 (el frontend nunca es la autoridad); se amplía a todos los módulos nuevos (objetos, solicitudes, administración) con la misma disciplina.

## 9. Mensajes de error

Sin cambios de principio; se corrigió el bug de la sección 6.2 que hacía que algunos errores expusieran el código 500 genérico en vez del código real (sin exponer nunca detalles internos en ninguno de los dos casos — la diferencia era solo el código HTTP, no el contenido).

## 10. Autorización — nuevo en v1.0 (no existía en v0.25 más allá de la autenticación)

Ver `docs/AUTHORIZATION.md` para el detalle completo: decoradores `login_requerido`/`admin_requerido`, verificación de ownership (IDOR) en cada modificación, whitelist de campos contra mass assignment, un admin no puede modificarse a sí mismo.

## 11. Base de datos — nuevo en v1.0

v0.25 no tenía base de datos real. v1.0 usa SQLAlchemy con `CheckConstraint` a nivel de base de datos para los campos de valores fijos (defensa en profundidad: ni un bug de Python podría escribir un rol o estado inválido), claves foráneas reales, y migraciones versionadas con Alembic. Ver `docs/DATABASE.md`.

## 12. Pruebas de seguridad ejecutadas (checklist de la skill seguridad-ofensiva-defensiva)

| Prueba | Resultado |
|---|---|
| SQL Injection | Probado, sistema protegido (SQLAlchemy parametrizado) |
| XSS almacenado | Probado, se guarda como texto plano; frontend usa `textContent` al mostrar |
| IDOR | Probado, ownership verificado en cada endpoint relevante |
| Fuerza bruta | Probado, rate limiting activo y confirmado con 429 |
| CSRF | Probado, token requerido; 2 bugs reales encontrados y corregidos |
| Escalamiento de roles (mass assignment) | Probado, el campo `rol` del cliente se ignora siempre |
| Tokens expirados | Probado, rechazados con 400 (forzando la expiración en la prueba) |
| Tokens usados | Probado, rechazados con 400 en el segundo uso |
| Payloads oversized | Probado, rechazados con 413 (`MAX_CONTENT_LENGTH`, agregado en v1.0) |
| JSON malformado | Probado, no causa 500 |
| Path traversal | Probado sobre archivos estáticos, 404 |

Ver `docs/evidencia/` para las ejecuciones reales y `backend/tests/security/` para el código de las pruebas.

## 13. Lo que NO se implementó todavía (a propósito o por bloqueo externo)

- Envío real de correos (recuperación de contraseña) — decisión de alcance, no de seguridad.
- Verificación de correo institucional por dominio específico.
- Confirmación de cuenta por correo antes de poder iniciar sesión.
- Autenticación de dos factores.
- HTTPS/despliegue de producción real (código y configuración listos; requiere autorización externa de un proveedor de hosting — ver `docs/DEPLOYMENT.md`).
- Escaneo automatizado de dependencias vulnerables (ej. `pip-audit` en CI).

Ninguna de estas limitaciones se presenta aquí como resuelta cuando no lo está.
