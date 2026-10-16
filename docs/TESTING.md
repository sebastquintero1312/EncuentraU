# TESTING.md — Pruebas de EncuentraU v2.0

## Resumen

| Tipo | Herramienta | Dónde | Evidencia |
|---|---|---|---|
| Unitarias | pytest | `tests/unit/` | `docs/evidencia/pytest_v2.0.txt` |
| Integración (API + PostgreSQL real) | pytest + Flask test client | `tests/integration/` | ídem |
| Base de datos (esquema, triggers, permisos, RLS, índices) | pytest + conexión directa | `tests/integration/test_esquema_bd.py` | ídem |
| Concurrencia (dos conexiones simultáneas) | pytest + psycopg2 + hilos | `tests/integration/test_concurrencia.py` | ídem |
| Seguridad ofensiva | pytest | `tests/security/` | ídem |
| Extremo a extremo con navegador real | Playwright + Microsoft Edge | `tests/e2e/verificacion_navegador.py` | `docs/evidencia/e2e_navegador_v2.0.txt` + `capturas_v2/` |
| Respaldo y restauración | `respaldo.py` / `restaurar.py` | `database/scripts/` | `docs/evidencia/respaldo_restauracion_v2.0.txt` |

El número exacto de pruebas y su resultado está al final de `docs/evidencia/pytest_v2.0.txt` (no se copia aquí para que no quede desactualizado).

## Cómo ejecutar

```powershell
cd backend
venv\Scripts\python.exe -m pytest -q                         # suite completa
venv\Scripts\python.exe tests\e2e\verificacion_navegador.py  # navegador real (levanta el servidor solo)
```

Requisitos: las bases `encuentrau_test` (pytest) y `encuentrau_dev` migrada (E2E), creadas con `database/scripts/crear_bd_local.sql` (ver README).

## Cómo funciona el aislamiento

- **PostgreSQL real**, el mismo esquema que producción, en una base aparte (`TEST_DATABASE_URL`). `conftest.py` se niega a correr si esa URL no apunta a una base cuyo nombre contenga "test" o si coincide con la de desarrollo: las pruebas **borran** todo.
- Al empezar: `DROP SCHEMA public CASCADE` y la migración real en ambos sentidos (`upgrade` → `downgrade` → `upgrade`), así se prueba también `00_eliminar.sql`.
- Antes de cada prueba: `TRUNCATE` de las tablas y recarga de `05_datos_iniciales.sql`. Para vaciar la auditoría, el dueño desactiva un momento el trigger que lo impide (la aplicación no puede hacerlo: `test_la_aplicacion_no_tiene_permiso`).
- **La aplicación corre con el usuario de permisos mínimos** (`encuentrau_app`), igual que en producción: si faltara un permiso, las pruebas fallarían.
- No se deja un `app_context` abierto durante la prueba: cada petición crea su propio contexto y su propia sesión de base de datos, como en producción.
- Los usuarios de prueba se crean por el camino real (registro → correo → enlace de verificación → login). Los correos van a la lista `CORREOS_ENVIADOS` (proveedor `memoria`) y las pruebas leen los enlaces de ahí.
- CSRF y límites de peticiones están desactivados salvo en `tests/security/test_csrf_rate_limit.py`, que crea su propia app con ellos activos.

## Qué cubre

| Archivo | Cubre |
|---|---|
| `unit/test_auth_service.py` | contraseñas, dominio institucional, Argon2id |
| `unit/test_seguridad_y_utilidades.py` | tokens, HMAC del código, validación de enteros/fechas, escape de comodines, celdas CSV |
| `unit/test_config.py` | guardrails de configuración y de producción, modo debug |
| `unit/test_documentacion_api.py` | `docs/API.md` coincide con las rutas reales |
| `integration/test_auth.py` | registro sin enumeración, verificación de correo, login, sesión, cookie, recuperación |
| `integration/test_roles.py` | matriz de permisos ruta por ruta para los tres roles |
| `integration/test_objetos.py` | reportes, visibilidad pública/privada, versión (409), ownership, coincidencias |
| `integration/test_reclamaciones.py` | flujo completo y medidas contra reclamaciones falsas (límites, rechazos, código, vencimiento, cierres, auditoría) |
| `integration/test_admin.py` | usuarios/roles, catálogos, parámetros, auditoría, estadísticas, CSV |
| `integration/test_notificaciones.py` | avisos, correo, IDOR, enlaces internos |
| `integration/test_esquema_bd.py` | esquema, CHECK/FK, triggers, auditoría inmutable, permisos mínimos, RLS, índices (incluye `EXPLAIN`) |
| `integration/test_concurrencia.py` | bloqueo de filas con dos conexiones reales, índice único parcial, atomicidad, concurrencia optimista |
| `security/test_ofensivas.py` | inyección SQL, XSS, payloads grandes o con tipos inesperados, mass assignment, IDOR, fuga de hashes, cabeceras |
| `security/test_csrf_rate_limit.py` | CSRF, regeneración de sesión, límites de peticiones |
| `e2e/verificacion_navegador.py` | el flujo completo con los tres roles en un navegador real, sin errores de JavaScript/CSP, XSS, open redirect, vista móvil |

## Bugs reales que encontraron las pruebas en v2.0

1. **Nombre repetido** en `solicitudes_service.py`: la función `generar_codigo_retiro(solicitud)` tapaba a la utilidad importada con el mismo nombre (`TypeError` al generar un código). Lo detectaron 12 pruebas de reclamaciones.
2. **Debug activado por defecto** (heredado de v1.0): `app.py` activaba el debugger interactivo cuando `FLASK_ENV` **no** estaba definida, al revés de lo que decía su comentario. Corregido con `modo_debug_permitido()` y `test_debug_solo_con_development_explicito`.

## Limitaciones

- Todas las pruebas se ejecutaron en un servidor PostgreSQL 18.6 local temporal creado con los mismos scripts del proyecto. Falta repetirlas en el servidor PostgreSQL del propietario y en Supabase (versión 15/17).
- El flujo de GitHub Actions (`.github/workflows/pruebas.yml`) está escrito pero no se ha ejecutado: el código todavía no se ha subido.
- El envío real por Brevo y el despliegue (HTTPS, Gunicorn, ProxyFix detrás de Render) no se han probado.
- No hay pruebas de carga.
