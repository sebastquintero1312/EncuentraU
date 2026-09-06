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


def create_app(config_overrides=None):
    """`config_overrides`: usado SOLO por las pruebas, para apuntar a una
    base de datos temporal aislada. Debe aplicarse ANTES de db.init_app():
    Flask-SQLAlchemy resuelve y cachea el engine en ese momento a partir de
    app.config, así que cambiar app.config['SQLALCHEMY_DATABASE_URI'] DESPUÉS
    de create_app() no tiene ningún efecto (bug real encontrado durante la
    revisión final de v1.0 — antes de esta corrección, todas las pruebas de
    pytest terminaban usando silenciosamente backend/instance/encuentrau_dev.db
    en lugar del archivo temporal que creían estar usando)."""
    Config.validar_configuracion_produccion()

    app = Flask(__name__, static_folder=CARPETA_FRONTEND, static_url_path='')
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)

    # Frontend y API viven en el mismo origen (Flask sirve frontend/public),
    # así que en producción no hace falta CORS cross-origin en absoluto. Los
    # orígenes de desarrollo (segundo servidor en :5500) solo se agregan
    # fuera de producción, para no dejar nunca un origen de localhost
    # permitido en un despliegue real.
    origenes_permitidos = [Config.FRONTEND_ORIGIN]
    if not Config.ES_PRODUCCION:
        origenes_permitidos += ['http://localhost:5500', 'http://127.0.0.1:5500']
    CORS(app, supports_credentials=True, origins=origenes_permitidos)

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
