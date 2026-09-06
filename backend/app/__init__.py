# Fábrica de la aplicación Flask.
# Aquí se junta todo: configuración, extensiones de seguridad, rutas y errores.

from flask import Flask
from flask_cors import CORS

from app.config.config import Config
from app.extensions import limiter, csrf
from app.middlewares.manejo_errores import registrar_manejadores_error
from app.routes.auth_routes import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS: el frontend (otro origen) necesita permiso explícito para
    # mandar la cookie de sesión (credentials).
    CORS(
        app,
        supports_credentials=True,
        origins=[Config.FRONTEND_ORIGIN, 'http://localhost:5500', 'http://127.0.0.1:5500'],
    )

    limiter.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    registrar_manejadores_error(app)

    @app.route('/')
    def inicio():
        return {'mensaje': 'API de EncuentraU (Flask) funcionando correctamente'}

    return app
