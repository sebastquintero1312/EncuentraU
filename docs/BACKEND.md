# BACKEND.md — Backend de EncuentraU v2.0

Python 3.11 + Flask 3 + SQLAlchemy 2 + PostgreSQL. Diagrama de capas en `docs/ARQUITECTURA.md`, contrato de endpoints en `docs/API.md`, base de datos en `docs/DATABASE.md`.

## Estructura

```
backend/
├── app.py                     punto de entrada (python app.py)
├── app/
│   ├── __init__.py            create_app(): configuración, ProxyFix, extensiones, rutas, CSP
│   ├── extensions.py          db, migrate, limiter, csrf
│   ├── config/config.py       variables de entorno + validar_configuracion() al arrancar
│   ├── auditoria_contexto.py  set_config('app.usuario_id') en cada transacción
│   ├── seguridad.py           tokens (secrets), SHA-256, HMAC de códigos de retiro
│   ├── comandos.py            flask crear-admin | verificar-correo | vencer-reservas
│   ├── routes/                auth, objetos, solicitudes (estudiante), oficina (encargado), admin, general
│   ├── controllers/           uno por grupo de rutas
│   ├── services/              cuentas, auth, objetos, coincidencias, solicitudes, oficina,
│   │                          usuarios_admin, catalogos, auditoria, notificaciones, correo
│   ├── models/                usuario, catalogo, token_usuario, objeto, solicitud, entrega,
│   │                          notificacion, auditoria (vista) + procedimientos.py y reportes.py
│   ├── middlewares/           autorizacion.py (decoradores por rol), manejo_errores.py
│   └── utils.py               paginación, texto/enteros/fechas seguros, fecha de Colombia
├── migrations/
│   ├── sql/                   el esquema en SQL (tablas, triggers, procedimientos, vistas, datos, permisos)
│   └── versions/0001_esquema_v2_postgresql.py
├── tests/                     pytest (unit, integration, security) + e2e/ (navegador real)
├── requirements.txt / requirements-dev.txt
└── .env.example
```

## Arrancar en desarrollo

Ver `README.md` (incluye la creación de la base de datos con `database/scripts/crear_bd_local.sql`).

## Variables de entorno

| Variable | Desarrollo | Producción |
|---|---|---|
| `SECRET_KEY` | aleatoria propia | obligatoria (la app no arranca con la de ejemplo) |
| `FLASK_ENV` | `development` (activa el debug) | `production` |
| `DATABASE_URL` | usuario `encuentrau_app` | URL de la app en Supabase (pooler) |
| `DATABASE_URL_MIGRACIONES` | usuario `encuentrau` | URL del dueño (migraciones) |
| `TEST_DATABASE_URL` / `TEST_DATABASE_URL_MIGRACIONES` | base `encuentrau_test` | — |
| `URL_PUBLICA` | `http://127.0.0.1:5000` | `https://…` (obligatorio https) |
| `DOMINIO_CORREO_INSTITUCIONAL` | `sanmateo.edu.co` | ídem |
| `CORREO_PROVEEDOR` | `consola` | `brevo` (obligatorio) |
| `BREVO_API_KEY`, `CORREO_REMITENTE`, `CORREO_REMITENTE_NOMBRE` | — | obligatorios |
| `NUM_PROXIES` | `0` | `1` en Render (IP real para el limitador y la auditoría) |

`Config.validar_configuracion` rechaza arrancar sin PostgreSQL, con un proveedor de correo desconocido y, en producción, con `SECRET_KEY` insegura, sin Brevo o sin `https` (`tests/unit/test_config.py`).

## Convenciones

- Los `services/` nunca importan `flask.request` ni devuelven `jsonify`.
- Whitelists de campos editables en el servicio (`CAMPOS_EDITABLES`) y en el controlador de usuarios.
- SQL escrito a mano solo en `models/procedimientos.py` y `models/reportes.py`, siempre con parámetros (`:nombre`).
- Operaciones que tocan varias tablas → procedimiento almacenado; el servicio valida la forma de los datos, llama al procedimiento, crea las notificaciones en la misma transacción, hace `commit` y después envía los correos.
- Después de un procedimiento, los objetos del ORM se releen (`populate_existing` / `refresh`), porque PostgreSQL los cambió por fuera del ORM.
- Errores de PostgreSQL traducidos en `manejo_errores.py`: `P0001` (regla del negocio) → 409 con el mensaje; `23505` (duplicado) → 409 con mensaje según la restricción; `StaleDataError` (versión vieja) → 409; deadlock → 409 "intenta de nuevo"; CHECK/FK/tipo inválido → 400; `42501` → 403; el resto → 500 sin detalles.

## Comandos de terminal

```powershell
flask crear-admin correo@sanmateo.edu.co     # único camino para crear un administrador
flask verificar-correo correo@sanmateo.edu.co  # verificar a mano (desarrollo o caso excepcional)
flask vencer-reservas                         # liberar reservas vencidas (la app también lo hace sola)
flask db upgrade                              # aplicar la migración (usa DATABASE_URL_MIGRACIONES)
```

## Dependencias

| Paquete | Para qué |
|---|---|
| Flask, Flask-SQLAlchemy, SQLAlchemy | web y ORM |
| Flask-Migrate (Alembic) | migraciones |
| psycopg2-binary | driver de PostgreSQL |
| Flask-Limiter, Flask-WTF, Flask-CORS | límites de peticiones, CSRF, CORS |
| argon2-cffi | Argon2id |
| python-dotenv | carga de `.env` |
| gunicorn | servidor de producción |
| pytest, playwright (solo desarrollo) | pruebas |

El envío por Brevo usa solo la biblioteca estándar (`urllib`): no se agregó ninguna dependencia nueva en v2.0.
