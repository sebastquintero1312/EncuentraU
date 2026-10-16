# Seguridad de EncuentraU

Versión: **v2.0**

Resumen honesto de las medidas de seguridad, cómo se probaron y qué falta. Detalle en:
- `docs/AUTHORIZATION.md`: roles, permisos y cómo se evita que alguien reclame algo ajeno.
- `docs/AUTHENTICATION.md`: registro, verificación del correo institucional, sesión y recuperación.
- `docs/DATABASE.md`: triggers, auditoría, permisos mínimos, RLS, concurrencia y respaldos.
- `docs/MATRIZ_SEGURIDAD.md`: revisión OWASP Top 10.
- `docs/REGLAS_100.md`: las 100 reglas con su estado y evidencia.

## Medidas principales

| Capa | Medida |
|---|---|
| Identidad | Solo correos `@sanmateo.edu.co` y verificados por enlace; Argon2id; respuestas sin enumeración de cuentas |
| Sesión | Cookie `HttpOnly` + `SameSite=Lax` (+ `Secure` en producción); se regenera al iniciar sesión; CSRF en todo POST/PUT; límites de peticiones |
| Permisos | Tres roles separados (estudiante, encargado, administrador); el rol se relee de la BD en cada petición; ownership; whitelists |
| Proceso | Verificación a ciegas, código de retiro de un solo uso con intentos limitados y vencimiento, entrega presencial con carné y prueba, límites de reclamaciones y cuentas en revisión |
| Base de datos | Reglas en triggers y procedimientos; usuario de la app sin `DELETE`, sin permisos sobre columnas sensibles ni sobre la auditoría; RLS; auditoría inmutable |
| Navegador | CSP estricta (`script-src 'self'`, `style-src 'self'`, sin recursos externos); nunca `innerHTML`; protección contra open redirect |
| Datos | Tokens y códigos guardados solo como hash; la auditoría nunca guarda hashes; respaldos en la nube cifrados; CSV sin datos personales |

## Cómo reportar un problema

Escribe al responsable del proyecto con los pasos para reproducirlo. No pruebes ataques contra el sistema desplegado de otras personas: las pruebas ofensivas del proyecto se ejecutan solo contra la base de datos de pruebas local (`backend/tests/security/`).

## Limitaciones conocidas

- No hay despliegue en producción todavía: HTTPS, HSTS, `Secure`, Gunicorn, ProxyFix detrás de Render y el envío real por Brevo están implementados pero sin verificar.
- El límite de peticiones guarda los contadores en memoria: se reinician al reiniciar el servidor y no se comparten entre varios procesos.
- Si la aplicación se conectara a Supabase con el usuario `postgres` (dueño) en vez de `encuentrau_app`, ese usuario sí podría desactivar triggers; por eso se recomienda el usuario de permisos mínimos también en producción.
- Sin segundo factor de autenticación, sin escaneo automático de dependencias y sin monitoreo centralizado.
