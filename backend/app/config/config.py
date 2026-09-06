# Configuración de la aplicación Flask.
# Todo lo sensible sale del ".env", nunca queda escrito directamente en el código.

import os


class Config:
    # Clave secreta usada para firmar la sesión y los tokens CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-insegura-solo-para-desarrollo')

    # Entorno actual: development o production
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    ES_PRODUCCION = FLASK_ENV == 'production'

    # Origen permitido para CORS (el frontend)
    FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:5500')

    # --- Configuración de la cookie de sesión ---
    SESSION_COOKIE_HTTPONLY = True          # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE = 'Lax'         # protege contra CSRF básico entre sitios
    SESSION_COOKIE_SECURE = ES_PRODUCCION   # solo por HTTPS en producción (en dev por HTTP no aplica)

    # --- Política de contraseñas ---
    LONGITUD_MINIMA_PASSWORD = 12

    # --- Recuperación de contraseña ---
    MINUTOS_EXPIRACION_TOKEN = 30
