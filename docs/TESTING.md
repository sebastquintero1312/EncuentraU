# TESTING.md — Pruebas de EncuentraU v1.0

## Resumen

| Tipo | Herramienta | Cantidad | Evidencia |
|---|---|---|---|
| Unitarias | pytest | 17 | `docs/evidencia/pytest_run_v1.0.txt` |
| Integración | pytest + Flask test client | 55 | ídem |
| Seguridad | pytest + Flask test client | 16 | ídem |
| Extremo a extremo (E2E) | Playwright + Chromium real | 14 verificaciones | `docs/evidencia/e2e_navegador_v1.0.txt` |
| Manual (servidor real + curl) | curl | 24 verificaciones | `docs/evidencia/smoke_test_manual_v1.0.md` |

**88 pruebas de pytest, todas ejecutadas y pasando**, más las verificaciones manuales/E2E. Ninguna se marca como exitosa sin haberse ejecutado realmente (regla de verificación, `CLAUDE.md`).

## Cómo ejecutar

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements-dev.txt
set FLASK_APP=app.py
flask db upgrade
pytest -v                                     # suite completa (rápida, ~25s, BD temporal aislada por prueba)
python tests/e2e/verificacion_navegador.py    # requiere: 1) servidor real corriendo (`python app.py`)
                                               #           2) base de datos limpia antes de correr
```

## Estructura

```
backend/tests/
├── conftest.py               # fixtures: app, client, usuario_a, cliente_b, cliente_admin
├── unit/
│   ├── test_auth_service.py       # validación de contraseñas, hashing Argon2id
│   └── test_objetos_service.py    # validación de datos de un reporte
├── integration/
│   ├── test_auth.py               # registro, login, logout, recuperación, restablecimiento
│   ├── test_objetos.py            # CRUD de reportes, búsqueda, coincidencias, IDOR
│   ├── test_solicitudes.py        # proceso completo de reclamación
│   └── test_admin.py              # panel de administración (usuarios y objetos)
├── security/
│   ├── test_csrf_rate_limit.py    # CSRF requerido/válido, rate limiting real
│   └── test_ofensivas.py          # SQLi, XSS, IDOR, tokens, payloads oversized, JSON malformado
└── e2e/
    └── verificacion_navegador.py  # Playwright: flujo completo con un navegador real
```

## Por qué dos niveles (pytest + Playwright)

`pytest` usa el *test client* de Flask: llama directamente a las vistas de Python, sin pasar por un navegador real ni ejecutar JavaScript. Es rápido y perfecto para probar el backend, pero **no puede detectar** un bug de JavaScript, un `id` de elemento mal escrito, una `Content-Security-Policy` que bloquee un script, o que un botón realmente dispare la petición esperada. Por eso además existe `tests/e2e/verificacion_navegador.py`, que abre un Chromium real (vía Playwright), navega, hace clic y escribe como lo haría una persona, contra un servidor Flask real. Esta combinación fue justamente la que reveló los 3 bugs reales corregidos durante esta migración (ver `CHANGELOG.md`): dos los encontró pytest (token tratado como diccionario tras migrar a ORM; CSRF sin manejador específico devolviendo 500), y el tercero (CSRF invalidado tras login) se encontró primero con `curl` contra el servidor real, antes incluso de escribir la suite de pytest.

## Aislamiento

- Cada prueba de pytest usa una base de datos SQLite temporal propia (`tempfile.mkstemp`), creada desde cero y borrada al terminar — ninguna prueba depende de datos dejados por otra.
- `WTF_CSRF_ENABLED` y `RATELIMIT_ENABLED` están desactivados por defecto para no interferir con pruebas que no los están probando específicamente; se activan explícitamente solo en `tests/security/test_csrf_rate_limit.py`.
- La verificación E2E requiere una base de datos limpia (recomendado: borrar `backend/instance/encuentrau_dev.db` antes de correrla) porque usa correos de prueba fijos.

## Cobertura por funcionalidad

Ver `docs/REGLAS_100.md` para el detalle regla por regla con su evidencia específica citada (qué archivo de test o qué inspección de código respalda cada una).

## Limitaciones conocidas

- No se ha probado contra PostgreSQL real (solo SQLite en desarrollo y en la suite de pruebas) — bloqueado por no existir todavía un despliegue en producción (ver `docs/DEPLOYMENT.md`).
- No hay pruebas de carga/rendimiento (fuera del alcance de v1.0 para un proyecto académico).
- La verificación E2E cubre el camino principal de cada flujo; no cubre exhaustivamente cada combinación de error posible (esas sí están cubiertas por pytest).
