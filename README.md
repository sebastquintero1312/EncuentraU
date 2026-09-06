# EncuentraU

Plataforma universitaria para gestionar objetos perdidos y encontrados.

Versión actual: **v1.0** — Backend Flask + SQLAlchemy con base de datos real, frontend conectado por completo (sin datos simulados), autenticación y autorización reales, seguridad verificada con pruebas automatizadas y de extremo a extremo.

Documentación completa en `docs/`: `ARQUITECTURA.md`, `API.md`, `BACKEND.md`, `FRONTEND.md`, `DATABASE.md`, `AUTHENTICATION.md`, `AUTHORIZATION.md`, `TESTING.md`, `DEPLOYMENT.md`, `MATRIZ_SEGURIDAD.md`, `REGLAS_100.md`, `VERSION_1.0.md` (informe final). `SECURITY.md` y `CHANGELOG.md` están en la raíz.

## Requisitos

- Python 3.10+ (probado con 3.12).

## Cómo ejecutar en desarrollo

```bash
cd backend
python -m venv venv
venv\Scripts\activate              # Windows; en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env             # Windows; en Linux/Mac: cp .env.example .env
# Edita .env y define un SECRET_KEY propio, por ejemplo:
#   python -c "import secrets; print(secrets.token_hex(32))"

set FLASK_APP=app.py               # Windows; en Linux/Mac: export FLASK_APP=app.py
flask db upgrade                   # crea backend/instance/encuentrau_dev.db con el esquema completo

python app.py
```

Abre **http://127.0.0.1:5000** — el mismo servidor sirve el frontend y la API (mismo origen, sin necesidad de CORS ni de un segundo servidor).

## Crear el primer usuario administrador

```bash
# 1. Regístrate normalmente desde la web (http://127.0.0.1:5000/registro.html)
# 2. Desde la terminal del servidor (backend/), promuévelo:
flask crear-admin tu-correo@sanmateo.edu.co
```

No existe ninguna forma de volverse administrador desde la propia web — es intencional (evita escalamiento de privilegios).

## Qué puedes hacer

- Registrarte, iniciar sesión, recuperar contraseña.
- Reportar un objeto perdido o encontrado.
- Buscar y filtrar reportes (por tipo, categoría, texto, ubicación).
- Ver posibles coincidencias entre tus reportes y los de otros.
- Solicitar la recuperación de un objeto (con verificación por un administrador).
- Como administrador: gestionar reportes, solicitudes y usuarios.

## Pruebas

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v                                     # 88 pruebas automatizadas
python tests/e2e/verificacion_navegador.py    # verificación con navegador real (requiere servidor corriendo)
```

Ver `docs/TESTING.md` para el detalle y `docs/evidencia/` para los resultados de la última ejecución.

## Estado del proyecto

Ver `docs/VERSION_1.0.md` para el informe completo de cierre de esta versión, incluyendo qué está desplegado en producción, qué sigue pendiente y por qué.
