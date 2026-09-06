# Instancias compartidas de las extensiones de Flask.
# Se crean aquí (sin la app todavía) y se conectan a la app en app/__init__.py
# Esto evita importaciones circulares entre los módulos.

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Limitador de peticiones: por defecto identifica al cliente por su IP
limiter = Limiter(key_func=get_remote_address)

# Protección CSRF para las rutas que dependen de la cookie de sesión
csrf = CSRFProtect()

# Base de datos (SQLAlchemy) y control de migraciones (Alembic vía Flask-Migrate)
db = SQLAlchemy()
migrate = Migrate()
