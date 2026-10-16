# Rutas del proceso de reclamación del lado del ESTUDIANTE.
# (La revisión, pre-aprobación y entrega son del encargado: oficina_routes.py.)

from flask import Blueprint

from app.controllers import solicitudes_controller
from app.extensions import limiter
from app.middlewares.autorizacion import estudiante_requerido

solicitudes_bp = Blueprint('solicitudes', __name__, url_prefix='/api')

LIMITE_CREACION = '10 per hour'
LIMITE_CODIGO = '5 per hour'


@solicitudes_bp.route('/solicitudes', methods=['POST'])
@limiter.limit(LIMITE_CREACION)
@estudiante_requerido
def crear_solicitud(estudiante):
    return solicitudes_controller.crear(estudiante)


@solicitudes_bp.route('/mis-solicitudes', methods=['GET'])
@estudiante_requerido
def mis_solicitudes(estudiante):
    return solicitudes_controller.mis_solicitudes(estudiante)


@solicitudes_bp.route('/solicitudes/<int:solicitud_id>/cancelar', methods=['POST'])
@estudiante_requerido
def cancelar_solicitud(estudiante, solicitud_id):
    return solicitudes_controller.cancelar(estudiante, solicitud_id)


@solicitudes_bp.route('/solicitudes/<int:solicitud_id>/codigo', methods=['POST'])
@limiter.limit(LIMITE_CODIGO)
@estudiante_requerido
def generar_codigo(estudiante, solicitud_id):
    return solicitudes_controller.generar_codigo(estudiante, solicitud_id)
