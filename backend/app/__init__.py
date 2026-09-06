# Fábrica de la aplicación Flask.
# Aquí se junta todo: configuración, base de datos, extensiones de
# seguridad, rutas, manejo de errores y (en el mismo origen) el frontend.

import os

import click
from flask import Flask, send_from_directory
from flask_cors import CORS

from app.config.config import Config
from app.extensions import limiter, csrf, db, migrate
from app.middlewares.manejo_errores import registrar_manejadores_error
from app.routes.auth_routes import auth_bp
from app.routes.objetos_routes import objetos_bp
from app.routes.solicitudes_routes import solicitudes_bp
from app.routes.admin_routes import admin_bp

# El frontend estático (HTML/CSS/JS) vive en frontend/public, un nivel arriba
# de backend/. Se sirve desde el mismo origen que la API para evitar CORS
# innecesario y para que exista una única URL pública para toda la app.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_FRONTEND = os.path.join(RAIZ_PROYECTO, 'frontend', 'public')


def create_app():
    Config.validar_configuracion_produccion()

    app = Flask(__name__, static_folder=CARPETA_FRONTEND, static_url_path='')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Solo se activa CORS "cross-origin" real si FRONTEND_ORIGIN se configuró
    # explícitamente distinto del propio dominio (caso de desarrollo con dos
    # servidores). En producción, frontend y API viven en el mismo origen y
    # no hace falta CORS.
    CORS(
        app,
        supports_credentials=True,
        origins=[Config.FRONTEND_ORIGIN, 'http://localhost:5500', 'http://127.0.0.1:5500'],
    )

    limiter.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(objetos_bp)
    app.register_blueprint(solicitudes_bp)
    app.register_blueprint(admin_bp)
    registrar_manejadores_error(app)

    @app.after_request
    def agregar_cabeceras_seguridad(response):
        # Defensa en profundidad a nivel de navegador. No reemplaza la
        # validación del backend, es una capa adicional.
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        if Config.ES_PRODUCCION:
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
        return response

    @app.route('/health')
    def health():
        # Health check mínimo: no revela versión, stack ni configuración.
        return {'estado': 'ok'}, 200

    @app.route('/')
    def index():
        return send_from_directory(CARPETA_FRONTEND, 'index.html')

    @app.cli.command('crear-admin')
    @click.argument('correo')
    def crear_admin(correo):
        """Promueve a un usuario ya registrado a rol 'administrador'.
        Se ejecuta manualmente desde el servidor (nunca por HTTP), para que
        no exista ninguna forma de auto-promoverse a admin desde la web.
        Uso: flask crear-admin correo@sanmateo.edu.co
        """
        from app.models.usuario import buscar_por_correo

        correo = correo.strip().lower()
        usuario = buscar_por_correo(correo)
        if not usuario:
            print(f'No existe ningún usuario registrado con el correo {correo}. Debe registrarse primero desde la web.')
            return
        usuario.rol = 'administrador'
        db.session.commit()
        print(f'Usuario {correo} promovido a administrador correctamente.')

    return app
