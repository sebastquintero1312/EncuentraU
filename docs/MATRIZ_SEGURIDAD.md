# MATRIZ_SEGURIDAD.md — Revisión defensiva OWASP Top 10 (2021) para EncuentraU v1.0

**Metodología**: para cada riesgo del OWASP Top 10, se documenta si aplica a EncuentraU, qué medida se tomó, dónde está implementada, cómo se probó y el resultado real. Ver `docs/REGLAS_100.md` para el detalle regla por regla y `docs/evidencia/` para las ejecuciones citadas.

**Advertencia honesta** (regla de seguridad realista, `CLAUDE.md`): esta matriz documenta controles implementados y probados, no una garantía de "100% seguro" ni "imposible de vulnerar". Ningún sistema lo es.

---

## A01:2021 — Broken Access Control

- **Aplicabilidad**: Alta (el sistema tiene roles, ownership de reportes, datos privados de verificación).
- **Medida**: Decoradores `login_requerido`/`admin_requerido` que releen el rol desde la BD en cada petición; verificación de ownership explícita antes de modificar/cancelar un reporte o ver solicitudes; whitelist de campos editables; un admin no puede modificar su propia cuenta.
- **Implementación**: `backend/app/middlewares/autorizacion.py`, `backend/app/controllers/*.py`.
- **Prueba**: `tests/integration/test_objetos.py` (IDOR), `tests/integration/test_admin.py`, `tests/integration/test_solicitudes.py` (información privada), `tests/security/test_ofensivas.py::test_no_se_puede_acceder_a_recurso_de_otro_usuario_cambiando_el_id`.
- **Resultado**: Todos los intentos de acceso no autorizado probados devuelven 401/403 correctamente; ninguno permitió el acceso.
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS.

## A02:2021 — Cryptographic Failures

- **Aplicabilidad**: Alta (contraseñas, tokens de sesión y de recuperación).
- **Medida**: Contraseñas con Argon2id; tokens de recuperación con `secrets.token_urlsafe(32)` (CSPRNG); `SECRET_KEY` desde variable de entorno con guardrail que impide un valor inseguro en producción; cookies `HttpOnly`+`SameSite`+`Secure` (en producción).
- **Implementación**: `backend/app/services/auth_service.py`, `backend/app/services/recuperacion_service.py`, `backend/app/config/config.py`.
- **Prueba**: `tests/unit/test_auth_service.py`, inspección directa de cabecera `Set-Cookie` real (ver `docs/REGLAS_100.md` RU-011/012).
- **Resultado**: Hash confirmado en formato `$argon2id$`; cookie confirmada con `HttpOnly; SameSite=Lax`.
- **Limitación conocida**: HTTPS/`Secure` real en producción no verificado todavía (bloqueado por no existir despliegue — RU-013, RU-085).
- **Estado**: CONTROLES IMPLEMENTADOS; VERIFICACIÓN PARCIAL (falta el entorno de producción real).

## A03:2021 — Injection

- **Aplicabilidad**: Alta (formularios de texto libre en registro, reportes, solicitudes, búsqueda).
- **Medida**: SQLAlchemy ORM en el 100% de las consultas (sin SQL crudo concatenado); validación de tipos/longitudes/formatos en cada `service`.
- **Implementación**: `backend/app/models/`, `backend/app/services/`.
- **Prueba**: `tests/security/test_ofensivas.py::test_sql_injection_en_busqueda_no_rompe_nada`, `test_sql_injection_intento_drop_table`.
- **Resultado**: Los payloads de inyección SQL se tratan como texto literal; no se observó ejecución de SQL malicioso ni error 500.
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS.

## A04:2021 — Insecure Design

- **Aplicabilidad**: Media.
- **Medida**: Máquina de estados explícita para reportes y solicitudes (no cualquier transición es válida); una "posible coincidencia" nunca transfiere propiedad automáticamente — siempre requiere una solicitud y aprobación humana de un administrador; un usuario no puede reclamar su propio reporte; solo puede existir una solicitud abierta por usuario por objeto.
- **Implementación**: `backend/app/models/objeto.py` (`TRANSICIONES_VALIDAS`), `backend/app/services/solicitudes_service.py`, `backend/app/services/coincidencias_service.py`.
- **Prueba**: `tests/integration/test_objetos.py::test_coincidencia_no_cambia_estado_del_objeto`, `tests/integration/test_solicitudes.py` (7 pruebas del flujo completo).
- **Resultado**: El diseño del flujo de negocio fue verificado punta a punta, incluyendo con navegador real.
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS.

## A05:2021 — Security Misconfiguration

- **Aplicabilidad**: Alta.
- **Medida**: `DEBUG` deny-by-default (solo activo si `FLASK_ENV=development` explícito); la app rehúsa arrancar en producción con `SECRET_KEY` insegura o sin `DATABASE_URL`; cabeceras de seguridad (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS en producción); `MAX_CONTENT_LENGTH` configurado; mensajes de error sin detalles internos.
- **Implementación**: `backend/app.py`, `backend/app/config/config.py`, `backend/app/__init__.py`, `backend/app/middlewares/manejo_errores.py`.
- **Prueba**: Cabeceras reales inspeccionadas con curl; `tests/security/test_ofensivas.py` (JSON malformado, payload oversized); `tests/security/test_csrf_rate_limit.py::test_csrf_error_devuelve_400_no_500`.
- **Resultado**: Todas las cabeceras presentes y correctas en una respuesta real; el bug real de "CSRFError devuelve 500" (config. de manejo de errores incompleta) fue encontrado y corregido.
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS (salvo la config. de producción real — ver A02).

## A06:2021 — Vulnerable and Outdated Components

- **Aplicabilidad**: Media.
- **Medida**: Todas las dependencias en `requirements.txt`/`requirements-dev.txt` están pineadas a una versión exacta (`==`), versiones razonablemente recientes al momento de escribir esto (Flask 3.0.3, SQLAlchemy 2.0.35, Argon2-cffi 23.1.0, etc.).
- **Implementación**: `backend/requirements.txt`, `backend/requirements-dev.txt`.
- **Prueba**: Instalación real ejecutada (`pip install -r requirements.txt`), sin conflictos de versiones.
- **Resultado**: Instalación limpia confirmada.
- **Limitación conocida**: no hay un proceso automatizado de escaneo de vulnerabilidades (ej. `pip-audit`) configurado — fuera del alcance de esta fase.
- **Estado**: CONTROLES IMPLEMENTADOS; ESCANEO AUTOMATIZADO PENDIENTE.

## A07:2021 — Identification and Authentication Failures
- **Aplicabilidad**: Alta.
- **Medida**: Política de contraseñas fuerte, rate limiting en login/registro/recuperación, mensajes anti-enumeración, `session.clear()` anti session-fixation, tokens de recuperación de un solo uso con expiración de 30 minutos.
- **Implementación**: `backend/app/services/auth_service.py`, `backend/app/controllers/auth_controller.py`, `backend/app/routes/auth_routes.py`.
- **Prueba**: `tests/integration/test_auth.py` (14 pruebas), `tests/security/test_csrf_rate_limit.py::test_rate_limit_login`, `tests/security/test_ofensivas.py::test_token_recuperacion_expirado_es_rechazado`.
- **Resultado**: Todos los casos de abuso probados (fuerza bruta, reutilización de token, token expirado, enumeración de usuarios) fueron rechazados correctamente.
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS.

## A08:2021 — Software and Data Integrity Failures

- **Aplicabilidad**: Media.
- **Medida**: Migraciones de esquema versionadas con Alembic (nunca se edita el esquema a mano); `CheckConstraint` a nivel de base de datos además de validación en Python para los campos de valores fijos (rol, tipo, estado).
- **Implementación**: `backend/migrations/`, `backend/app/models/*.py`.
- **Prueba**: `flask db migrate` + `flask db upgrade` ejecutados realmente; inspección de `__table_args__` en los modelos.
- **Resultado**: Esquema reproducible desde cero confirmado (usado en cada corrida de pytest, que crea la BD desde cero).
- **Estado**: CONTROLES IMPLEMENTADOS Y VERIFICADOS.

## A09:2021 — Security Logging and Monitoring Failures

- **Aplicabilidad**: Media.
- **Medida**: Los errores 500 se registran server-side con `app.logger.exception` (traceback completo solo en el log, nunca en la respuesta al cliente).
- **Implementación**: `backend/app/middlewares/manejo_errores.py`.
- **Prueba**: Inspección de código; observado en la práctica en los logs del servidor de desarrollo durante esta migración (cada error 500 dejó un traceback completo en `/tmp/flask_server.log` durante las pruebas).
- **Limitación conocida**: no hay un sistema de monitoreo/alertas centralizado (ej. Sentry) ni logging estructurado — razonable para el alcance de un proyecto académico, pero es una limitación real para producción a escala.
- **Estado**: CONTROLES BÁSICOS IMPLEMENTADOS; MONITOREO AVANZADO NO_APLICA (fuera de alcance).

## A10:2021 — Server-Side Request Forgery (SSRF)

- **Aplicabilidad**: Baja. El único campo que acepta una URL es `imagen_url` (opcional, en un reporte), y el backend **nunca la descarga ni la solicita** — solo la guarda como texto y el frontend la usa como atributo `src` de una etiqueta `<img>` en el navegador del usuario final, no en una petición del servidor.
- **Medida**: Validación de formato (debe empezar con `http://` o `https://`, longitud máxima 500) sin que el servidor haga ninguna petición saliente a esa URL.
- **Implementación**: `backend/app/services/objetos_service.py` (`validar_datos_objeto`).
- **Prueba**: `tests/unit/test_objetos_service.py::test_imagen_url_no_http_rechazada`.
- **Resultado**: No existe una ruta de código en el backend que haga un `requests.get()`/similar sobre una URL provista por el usuario.
- **Estado**: NO_APLICA (superficie de ataque inexistente en el diseño actual).

---

## Resumen

| Riesgo | Estado |
|---|---|
| A01 Broken Access Control | Verificado |
| A02 Cryptographic Failures | Implementado, verificación de producción pendiente |
| A03 Injection | Verificado |
| A04 Insecure Design | Verificado |
| A05 Security Misconfiguration | Verificado (salvo config. de producción real) |
| A06 Vulnerable Components | Implementado, escaneo automatizado pendiente |
| A07 Auth Failures | Verificado |
| A08 Data Integrity Failures | Verificado |
| A09 Logging Failures | Básico implementado, monitoreo avanzado fuera de alcance |
| A10 SSRF | No aplica |

Ningún riesgo del Top 10 quedó sin analizar. Las limitaciones reales (marcadas arriba) están documentadas explícitamente, no ocultas.
