# BACKEND.md — Backend de EncuentraU v1.0

Python 3.12 + Flask 3.x + SQLAlchemy 2.x. Ver `docs/ARQUITECTURA.md` para el diagrama de capas y `docs/API.md` para el contrato completo de endpoints.

## Estructura

```
backend/
├── app.py                  # punto de entrada (python app.py)
├── app/
│   ├── __init__.py         # create_app(): fábrica de la aplicación
│   ├── extensions.py       # db, migrate, limiter, csrf (compartidas, sin la app)
│   ├── config/config.py    # toda la configuración, desde variables de entorno
│   ├── routes/              # auth, objetos, solicitudes, admin
│   ├── controllers/         # uno por módulo de rutas
│   ├── services/             # lógica de negocio (auth, objetos, solicitudes, coincidencias, usuarios_admin, recuperación)
│   ├── models/               # Usuario, TokenRecuperacion, Objeto, Solicitud (SQLAlchemy)
│   ├── middlewares/           # autorizacion.py (decoradores), manejo_errores.py
│   └── utils.py               # helpers pequeños (paginación)
├── migrations/               # Flask-Migrate / Alembic
├── tests/                    # pytest (unit, integration, security) + e2e/ (Playwright)
├── requirements.txt           # dependencias de producción
├── requirements-dev.txt       # + pytest, playwright
└── .env.example
```

## Arrancar en desarrollo

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows; en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # y define un SECRET_KEY propio
set FLASK_APP=app.py           # Windows; en Linux/Mac: export FLASK_APP=app.py
flask db upgrade               # crea backend/instance/encuentrau_dev.db
python app.py
```

Servidor en `http://127.0.0.1:5000` (sirve también el frontend en la misma URL).

## Crear el primer administrador

No existe ningún mecanismo por HTTP para volverse administrador (por diseño: sería una vulnerabilidad de escalamiento de privilegios). Se hace desde el servidor:

```bash
# 1. Registrarse normalmente desde la web con el correo que será admin
# 2. Promoverlo desde la terminal del servidor:
flask crear-admin correo@sanmateo.edu.co
```

## Dependencias clave

| Paquete | Para qué |
|---|---|
| Flask | Framework web |
| Flask-SQLAlchemy / SQLAlchemy | ORM |
| Flask-Migrate | Migraciones de esquema (Alembic) |
| Flask-Limiter | Rate limiting |
| Flask-WTF | Protección CSRF |
| Flask-CORS | CORS (solo relevante si frontend y API están en dominios distintos) |
| argon2-cffi | Hashing de contraseñas (Argon2id) |
| psycopg2-binary | Driver de PostgreSQL (producción) |
| gunicorn | Servidor WSGI de producción (Linux) |
| python-dotenv | Carga de `.env` en desarrollo |

## Convenciones de código

- Los `services/` nunca importan `flask.request` ni devuelven `jsonify` — reciben datos ya extraídos y devuelven `(errores, resultado)` o lanzan una condición que el controlador traduce a un código HTTP.
- Toda whitelist de campos editables vive en el `service` correspondiente (`CAMPOS_EDITABLES`, etc.), nunca se hace `for campo in request.json: setattr(...)`.
- Todo lo que pueda variar entre entornos (claves, URLs, límites) vive en `config/config.py`, leído de variables de entorno — nunca hardcodeado.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -v                         # 88 pruebas (unit + integration + security)
python tests/e2e/verificacion_navegador.py   # requiere el servidor real corriendo + BD limpia
```

Ver `docs/TESTING.md` para el detalle.
