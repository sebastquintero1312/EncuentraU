# Configuración de la aplicación Flask.
# Todo lo sensible sale del ".env", nunca queda escrito directamente en el código.

import os

CLAVE_INSEGURA_POR_DEFECTO = 'clave-insegura-solo-para-desarrollo'


class Config:
    # Clave secreta usada para firmar la sesión y los tokens CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', CLAVE_INSEGURA_POR_DEFECTO)

    # Entorno actual: development o production
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    ES_PRODUCCION = FLASK_ENV == 'production'

    # Origen(es) permitidos para CORS (el frontend), separados por coma si hay más de uno.
    # Si el frontend se sirve desde el mismo dominio que la API (recomendado), esto no se usa.
    FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:5500')

    # --- Configuración de la cookie de sesión ---
    SESSION_COOKIE_HTTPONLY = True          # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE = 'Lax'         # protege contra CSRF básico entre sitios
    SESSION_COOKIE_SECURE = ES_PRODUCCION   # solo por HTTPS en producción (en dev por HTTP no aplica)

    # --- Política de contraseñas ---
    LONGITUD_MINIMA_PASSWORD = 12

    # --- Recuperación de contraseña ---
    MINUTOS_EXPIRACION_TOKEN = 30

    # --- Base de datos ---
    # En desarrollo, si no se define DATABASE_URL, se usa un archivo SQLite local.
    # En producción se espera DATABASE_URL (PostgreSQL) como variable de entorno,
    # nunca una credencial escrita en el código.
    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url.startswith('postgres://'):
        # Render/Heroku entregan el prefijo antiguo "postgres://"; SQLAlchemy 2.x
        # requiere "postgresql://".
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url or 'sqlite:///' + os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'instance', 'encuentrau_dev.db',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Paginación ---
    RESULTADOS_POR_PAGINA_DEFECTO = 10
    RESULTADOS_POR_PAGINA_MAXIMO = 50

    @staticmethod
    def validar_configuracion_produccion():
        """Se llama al crear la app. Si estamos en producción con configuración
        insegura, preferimos que la aplicación falle al arrancar (deny by default)
        en vez de exponer una clave secreta débil o una base de datos no configurada."""
        if not Config.ES_PRODUCCION:
            return
        if Config.SECRET_KEY == CLAVE_INSEGURA_POR_DEFECTO:
            raise RuntimeError(
                'SECRET_KEY insegura: define una variable de entorno SECRET_KEY '
                'real antes de arrancar en producción (FLASK_ENV=production).'
            )
        if not os.environ.get('DATABASE_URL'):
            raise RuntimeError(
                'DATABASE_URL no definida: en producción se requiere una base de '
                'datos real (PostgreSQL), no SQLite local.'
            )
