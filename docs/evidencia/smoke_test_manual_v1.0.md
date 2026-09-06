# Evidencia: prueba manual de integración completa (servidor real, local)

**Fecha:** 2026-09-06
**Entorno:** Flask dev server real corriendo en `http://127.0.0.1:5000`, base de datos SQLite real (`backend/instance/encuentrau_dev.db`), peticiones HTTP reales vía `curl` (no mocks, no simulación).

Este documento complementa la suite de pytest (`docs/evidencia/pytest_run_v1.0.txt`): pytest usa el test client de Flask, esta prueba usó el servidor real levantado con `python app.py` y `curl` como cliente HTTP externo, para verificar que el sistema funciona de punta a punta tal como lo haría un usuario real.

## Flujo probado y resultado

| # | Prueba | Resultado |
|---|--------|-----------|
| 1 | Registro de usuario real (Laura) vía `POST /api/auth/registro` | 201, usuario creado |
| 2 | Login real, cookie de sesión recibida | 200 |
| 3 | Crear reporte "perdido" (mochila azul) | 201, guardado en SQLite real |
| 4 | Segundo usuario (Carlos) crea reporte "encontrado" similar | 201 |
| 5 | Motor de coincidencias encuentra el reporte de Carlos al ver el detalle del de Laura | Coincidencia encontrada, `posible_coincidencia: true`, `puntaje_coincidencia: 8` |
| 6 | Búsqueda pública `/api/objetos?q=mochila` | Devuelve ambos reportes |
| 7 | IDOR: Carlos intenta editar (`PUT`) el reporte de Laura | 403 |
| 8 | IDOR: Carlos intenta cancelar (`DELETE`) el reporte de Laura | 403 |
| 9 | Carlos envía solicitud de reclamación sobre el reporte de Laura | 201, objeto pasa a `en_proceso` |
| 10 | Carlos intenta reclamar su **propio** reporte | 400, rechazado |
| 11 | Laura (dueña) ve la información privada de verificación de la solicitud | 200 |
| 12 | Carlos (no dueño, no admin) intenta ver esa misma información | 403 |
| 13 | Carlos (ciudadano) intenta acceder a `/api/admin/usuarios` | 403 |
| 14 | Petición a `/api/mis-reportes` sin sesión | 401 |
| 15 | Registro enviando `"rol": "administrador"` en el body | Ignorado; usuario creado como `ciudadano` (protección mass assignment) |
| 16 | Rate limiting real: 5+ registros seguidos desde la misma IP | Los primeros pasan, luego `429` |
| 17 | Inyección SQL básica (`' OR '1'='1`) en el parámetro de búsqueda | Tratado como texto literal (SQLAlchemy parametrizado); sin error, sin fuga de datos |
| 18 | XSS almacenado: crear un reporte con `<script>alert(1)</script>` como nombre | Se guarda tal cual (texto plano); la responsabilidad de escapar al mostrar es del frontend — ver `docs/SECURITY.md` |
| 19 | Path traversal sobre archivos estáticos (`/../../../etc/passwd`, variantes `%2e%2e`) | 404 |
| 20 | Promoción real de Laura a administradora vía `flask crear-admin` (CLI de servidor, no HTTP) | Confirmado por consulta posterior a `/api/admin/usuarios` |
| 21 | Laura (ya admin) aprueba la solicitud de Carlos | 200, objeto pasa a `resuelto` |
| 22 | Admin intenta modificar su propio rol/estado desde el panel | 400, bloqueado (autoprotección) |
| 23 | Admin desactiva la cuenta de Carlos | 200 |
| 24 | Carlos (desactivado) intenta iniciar sesión | 401, login rechazado |

## Bugs reales encontrados y corregidos durante esta prueba

1. **CSRF token invalidado tras login/logout.** `session.clear()` (protección anti session-fixation) borraba también el `csrf_token` guardado en la sesión, por lo que cualquier petición protegida inmediatamente después de iniciar sesión fallaba. Corregido: el backend genera y devuelve un nuevo `csrf_token` en la respuesta de login/logout, y el frontend (`api.js`) lo captura automáticamente. Ver `backend/app/controllers/auth_controller.py` y `frontend/public/js/api.js`.
2. **Errores CSRF devolvían 500 en vez de 400.** El manejador de errores solo tenía casos específicos para 404/405/429 y un manejador genérico de `Exception` para todo lo demás; como `CSRFError` no tenía manejador propio, cualquier fallo de CSRF cambiaba de código 400 a 500 y ocultaba el motivo real. Este bug ya existía en v0.25 (nadie lo detectó porque nunca se probó una petición con CSRF ausente/inválido). Corregido con un manejador para `werkzeug.exceptions.HTTPException` en `backend/app/middlewares/manejo_errores.py`.
3. **`recuperacion_service.py` seguía tratando `TokenRecuperacion` como diccionario** (`registro['usuario_id']`) después de migrar el modelo a SQLAlchemy, causando `TypeError` (500) en cualquier restablecimiento de contraseña. Corregido a `registro.usuario_id`. Detectado por la suite de pytest, no por esta prueba manual.

## Limitación de esta evidencia

Esta prueba se ejecutó en `localhost`, no contra una URL pública en Internet. La prueba equivalente sobre la URL pública desplegada (cuando exista) debe repetirse y documentarse por separado — ver `docs/DEPLOYMENT.md`.
