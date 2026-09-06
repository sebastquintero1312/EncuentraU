# ESTADO_V025.md — Auditoría real de EncuentraU v0.25

**Fecha de auditoría:** 2026-09-06
**Método:** Lectura completa de todos los archivos de código y documentación. Ningún archivo fue modificado durante esta auditoría. No se ejecutó el servidor ni se corrieron pruebas — todo lo marcado como "funciona" es análisis estático de código (**IMPLEMENTADO**), no ejecución comprobada (**VERIFICADO**), salvo que se indique lo contrario.

---

## 1. Resumen ejecutivo

v0.25 tiene un backend Flask real, pero **solo para autenticación**. Todo lo demás (objetos perdidos, objetos encontrados, búsqueda, coincidencias, reclamaciones, administración) es **100% simulado en el navegador** mediante `frontend/public/js/datos-temporales.js` — no existe backend, no existe base de datos, no existe persistencia real para el núcleo funcional de la aplicación.

No existe base de datos real de ningún tipo (todo vive en listas de Python en memoria o en constantes JavaScript del navegador). No existen pruebas automatizadas. La documentación de arquitectura (`ARCHITECTURE.md`) describe un stack Node.js/MySQL que ya no existe. `docs/REGLAS_100.md` solo contiene 50 de las 100 reglas prometidas.

## 2. Backend (`backend/`)

Estructura: `app.py` → `app/__init__.py` (factory) → `config/config.py`, `extensions.py`, `routes/auth_routes.py` → `controllers/auth_controller.py` → `services/{auth_service,recuperacion_service}.py` → `models/{usuario,token_recuperacion}.py` → `middlewares/manejo_errores.py`.

### Endpoints existentes (único blueprint: `/api/auth`)

| Método | Ruta | Auth | Rate limit | Estado |
|---|---|---|---|---|
| GET | `/api/auth/csrf-token` | No | — | IMPLEMENTADO |
| POST | `/api/auth/registro` | No | 5/min | IMPLEMENTADO |
| POST | `/api/auth/login` | No | 10/min | IMPLEMENTADO |
| POST | `/api/auth/logout` | No | — | IMPLEMENTADO |
| GET | `/api/auth/sesion` | No | — | IMPLEMENTADO |
| POST | `/api/auth/recuperar` | No | 5/min | IMPLEMENTADO |
| POST | `/api/auth/restablecer` | No | 5/min | IMPLEMENTADO |

**No existen endpoints de negocio** (objetos perdidos/encontrados, búsqueda, coincidencias, reclamaciones, administración). Deben construirse desde cero para v1.0.

### Hallazgos de seguridad ya implementados (lectura de código)

- `session.clear()` antes de fijar sesión en login (`auth_controller.py:68`) — anti session-fixation.
- Mensajes de error genéricos en login y recuperación — anti user-enumeration.
- Tokens de recuperación con `secrets.token_urlsafe(32)` (CSPRNG), un solo uso, expiración de 30 min.
- Password hashing con Werkzeug (`scrypt`) — **no Argon2id** como exige la meta de v1.0.
- Rate limiting con Flask-Limiter por IP en endpoints sensibles.
- CSRF con Flask-WTF (`CSRFProtect`).
- Manejo de errores centralizado sin fuga de tracebacks (404/405/429/500).
- Cookies de sesión `HttpOnly`, `SameSite=Lax`, `Secure` ligado a `ES_PRODUCCION`.

### Riesgos detectados

1. `SECRET_KEY` tiene default inseguro hardcodeado (`config.py`) sin guardrail que impida arrancar en producción sin una clave real definida por entorno.
2. `app.py` corre con `debug=True` por defecto salvo que `FLASK_ENV=production` esté explícitamente definido — riesgo de exponer el debugger de Werkzeug.
3. `SECURITY.md` afirma que Flask-Limiter "no se pudo instalar/probar de punta a punta" en un entorno anterior — contradice su presencia y uso activo en el código actual; debe verificarse con ejecución real, no asumirse.
4. `.gitignore` no cubre `*.db`, `instance/`, `.pytest_cache/` — relevante en cuanto se agregue SQLite/pytest.
5. Password hashing es `scrypt`, no Argon2id (brecha respecto a meta v1.0).

### Persistencia

**100% en memoria de proceso** (`usuarios = []`, `tokens_recuperacion = []` en `models/`). El propio código lo declara en comentarios. Se pierde al reiniciar el servidor. No hay SQLAlchemy, no hay ORM, no hay conexión a base de datos real.

### Dependencias (`requirements.txt`, versiones pineadas)

Flask 3.0.3, Flask-Limiter 3.8.0, Flask-WTF 1.2.1, Flask-CORS 4.0.1, python-dotenv 1.0.1. **Faltan** (necesarias para v1.0): Flask-SQLAlchemy, Flask-Migrate, argon2-cffi, gunicorn, psycopg2-binary.

## 3. Frontend (`frontend/public/`)

15 páginas HTML. Solo 4 usan el backend real vía `js/api.js`: `login.html`, `registro.html`, `recuperar-contrasena.html`, `restablecer-contrasena.html`.

Las **9 restantes** (`buscar-objetos`, `detalle-objeto`, `gestion-reportes`, `gestion-usuarios`, `mis-reportes`, `panel-admin`, `panel-ciudadano`, `solicitud-recuperacion`) dependen de `js/datos-temporales.js` — datos hardcodeados en el navegador, sin persistencia real, declarados como simulados en sus propios comentarios.

`reportar-perdido.html` y `reportar-encontrado.html` **no persisten nada en absoluto** — ni siquiera usan `datos-temporales.js`; solo validan el formulario visualmente y muestran un mensaje de confirmación falso.

`js/api.js`: `API_BASE` hardcodeado a `http://127.0.0.1:5000/api` — no configurable por entorno, debe corregirse antes de despliegue.

`gestion-usuarios.html` permite cambiar el rol de un usuario a "administrador" desde un `<select>` en el navegador — hoy es cosmético (no hay backend detrás), pero es exactamente el patrón de escalamiento de privilegios que debe bloquearse en el backend real (RU-016/RU-017).

`usuarioActualId = 1` está hardcodeado en `datos-temporales.js` — el frontend no usa la sesión real de Flask para saber quién es el usuario actual en ninguna de las páginas simuladas.

## 4. Base de datos

No existe. `database/scripts/` solo contiene un `.gitkeep`. No hay modelos ORM, no hay SQLAlchemy, no hay conexión a ningún motor de base de datos en ningún archivo del proyecto.

## 5. Documentación

- `README.md`: coherente con el código real.
- `ARCHITECTURE.md`: **desactualizado** — describe un backend Node.js/Express/MySQL que fue reemplazado por Flask (según el propio `CHANGELOG.md`). Debe corregirse.
- `CHANGELOG.md`: alineado con el código real.
- `SECURITY.md`: honesto y detallado, con una nota potencialmente obsoleta sobre Flask-Limiter (ver riesgo #3).
- `docs/REGLAS_100.md`: solo contiene RU-001 a RU-050 (categorías A–D: autenticación, autorización, inyección/XSS, CSRF/sesiones). **Faltan RU-051 a RU-100.** Las 50 reglas existentes están todas en estado `PENDIENTE` (plantilla sin rellenar), aunque varias ya están satisfechas por el código de v0.25 (ej. RU-010, RU-011–013, RU-014–015).
- `docs/ESTADO_V025.md` y `docs/ARQUITECTURA.md` no existían antes de esta auditoría (este documento crea el primero).

## 6. Pruebas

No existe ningún archivo de test en el repositorio. No hay evidencia de ejecución de pruebas de ningún tipo.

## 7. Secretos

No se encontraron secretos reales filtrados. `.env.example` solo tiene placeholders. El único hallazgo es el default inseguro de `SECRET_KEY` (riesgo de diseño, no fuga de secreto real).

## 8. Control de versiones

El proyecto **no es un repositorio git** al momento de esta auditoría.

## 9. Qué existe vs. qué falta para v1.0

| Componente | v0.25 | Falta para v1.0 |
|---|---|---|
| Autenticación (registro/login/logout/sesión/recuperación) | Real, en memoria | Migrar a BD real, Argon2id |
| Autorización por roles | No existe | Construir desde cero |
| Objetos perdidos/encontrados | Simulado en frontend | Backend + BD real completos |
| Búsqueda/filtros | Simulado en frontend (JS) | Backend real con paginación |
| Coincidencias | No existe | Construir desde cero |
| Reclamaciones | No existe (solo un formulario que no persiste) | Construir desde cero |
| Administración | Simulado en frontend | Backend real con autorización de rol |
| Base de datos | Ninguna | SQLAlchemy + SQLite (dev) / PostgreSQL (prod) |
| Migraciones | No existe | Flask-Migrate |
| Tests | No existen | Suite pytest funcional + seguridad |
| Deployment | No existe | Proveedor real, HTTPS, variables de entorno |
| Documentación de arquitectura | Desactualizada (Node.js) | Reescribir para reflejar Flask+SQLAlchemy |

## 10. Conclusión

v0.25 es una base sólida para el subsistema de autenticación, con buenas prácticas de seguridad ya presentes (anti-fixation, anti-enumeration, CSRF, rate limiting, tokens seguros). Pero el núcleo funcional del producto (gestión de objetos perdidos y encontrados) no existe como sistema real — es una simulación de frontend. La transición a v1.0 requiere construir la mayor parte del backend de negocio desde cero, no solo "conectar" lo existente.
