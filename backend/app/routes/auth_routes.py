# Rutas de autenticación.
# Cada ruta solo define la URL y el método HTTP, y aplica el límite de
# peticiones correspondiente. La lógica real vive en el controlador.

from flask import Blueprint
from flask_wtf.csrf import generate_csrf

from app.controllers import auth_controller
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Límites pensados para proteger fuerza bruta sin molestar pruebas normales
LIMITE_LOGIN = '10 per minute'
LIMITE_REGISTRO = '5 per minute'
LIMITE_RECUPERACION = '5 per minute'


@auth_bp.route('/csrf-token', methods=['GET'])
def csrf_token():
    # El frontend pide este token antes de enviar login/registro/recuperación
    # y lo manda de vuelta en el header X-CSRFToken. Así el backend puede
    # confirmar que la petición viene realmente de nuestro frontend.
    return {'csrf_token': generate_csrf()}, 200


@auth_bp.route('/registro', methods=['POST'])
@limiter.limit(LIMITE_REGISTRO)
def registro():
    return auth_controller.registrar()


@auth_bp.route('/login', methods=['POST'])
@limiter.limit(LIMITE_LOGIN)
def login():
    return auth_controller.iniciar_sesion()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return auth_controller.cerrar_sesion()


@auth_bp.route('/sesion', methods=['GET'])
def sesion():
    return auth_controller.sesion_actual()


@auth_bp.route('/recuperar', methods=['POST'])
@limiter.limit(LIMITE_RECUPERACION)
def recuperar():
    return auth_controller.solicitar_recuperacion()


@auth_bp.route('/restablecer', methods=['POST'])
@limiter.limit(LIMITE_RECUPERACION)
def restablecer():
    return auth_controller.restablecer_contrasena()
