# Fábrica de la aplicación Flask.
# Aquí se junta todo: configuración, base de datos, extensiones de
# seguridad, rutas, manejo de errores y (en el mismo origen) el frontend.

import os

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config.config import Config
from app.extensions import limiter, csrf, db, migrate
from app.auditoria_contexto import registrar_contexto_auditoria
from app.comandos import registrar_comandos
from app.middlewares.manejo_errores import registrar_manejadores_error
from app.routes.auth_routes import auth_bp
from app.routes.objetos_routes import objetos_bp
from app.routes.solicitudes_routes import solicitudes_bp
from app.routes.oficina_routes import oficina_bp
from app.routes.admin_routes import admin_bp
from app.routes.general_routes import general_bp
import app.models  # noqa: F401  (registra todos los modelos en SQLAlchemy)

# El frontend estático (HTML/CSS/JS) vive en frontend/public, un nivel arriba
# de backend/. Se sirve desde el mismo origen que la API para evitar CORS
# innecesario y para que exista una única URL pública para toda la app.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_FRONTEND = os.path.join(RAIZ_PROYECTO, 'frontend', 'public')


def create_app(config_overrides=None):
    """`config_overrides`: usado SOLO por las pruebas, para apuntar a la base
    de datos de pruebas. Debe aplicarse ANTES de db.init_app():
    Flask-SQLAlchemy resuelve y cachea el engine en ese momento a partir de
    app.config, así que cambiar app.config['SQLALCHEMY_DATABASE_URI'] DESPUÉS
    de create_app() no tiene ningún efecto (bug real encontrado durante la
    revisión final de v1.0)."""
    app = Flask(__name__, static_folder=CARPETA_FRONTEND, static_url_path='')
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
    Config.validar_configuracion(app.config)

    # Detrás de un proxy (Render), la IP real del cliente llega en
    # X-Forwarded-For. Sin esto, el límite de peticiones y la auditoría verían
    # a todos los usuarios con la IP del proxy. Solo se activa si NUM_PROXIES
    # lo indica: confiar en ese encabezado sin un proxy real permitiría
    # falsificar la IP.
    if app.config['NUM_PROXIES'] > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['NUM_PROXIES'], x_proto=app.config['NUM_PROXIES'])

    db.init_app(app)
    migrate.init_app(app, db)
    registrar_contexto_auditoria()

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

    for blueprint in (auth_bp, objetos_bp, solicitudes_bp, oficina_bp, admin_bp, general_bp):
        app.register_blueprint(blueprint)
    registrar_manejadores_error(app)
    registrar_comandos(app)

    @app.after_request
    def agregar_cabeceras_seguridad(response):
        # Defensa en profundidad a nivel de navegador. No reemplaza la
        # validación del backend, es una capa adicional.
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # Todo (scripts, estilos, fuentes, íconos) se sirve desde el mismo
        # servidor: no se carga nada de dominios externos.
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        if request.path.startswith('/api/'):
            # Las respuestas de la API contienen datos personales: que ningún
            # navegador ni proxy intermedio las guarde en caché.
            response.headers['Cache-Control'] = 'no-store'
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

    return app
