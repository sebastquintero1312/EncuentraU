# Rutas del proceso de reclamación (solicitudes).

from flask import Blueprint

from app.controllers import solicitudes_controller
from app.extensions import limiter
from app.middlewares.autorizacion import login_requerido, admin_requerido

solicitudes_bp = Blueprint('solicitudes', __name__, url_prefix='/api')

LIMITE_CREACION = '20 per hour'


@solicitudes_bp.route('/solicitudes', methods=['POST'])
@limiter.limit(LIMITE_CREACION)
@login_requerido
def crear_solicitud(usuario_actual):
    return solicitudes_controller.crear(usuario_actual)


@solicitudes_bp.route('/mis-solicitudes', methods=['GET'])
@login_requerido
def mis_solicitudes(usuario_actual):
    return solicitudes_controller.mis_solicitudes(usuario_actual)


@solicitudes_bp.route('/solicitudes/<int:solicitud_id>', methods=['DELETE'])
@login_requerido
def cancelar_solicitud(usuario_actual, solicitud_id):
    return solicitudes_controller.cancelar(usuario_actual, solicitud_id)


@solicitudes_bp.route('/admin/solicitudes', methods=['GET'])
@admin_requerido
def listar_solicitudes_admin(usuario_actual):
    return solicitudes_controller.listar_admin()


@solicitudes_bp.route('/admin/solicitudes/<int:solicitud_id>', methods=['PUT'])
@admin_requerido
def revisar_solicitud_admin(usuario_actual, solicitud_id):
    return solicitudes_controller.revisar_admin(solicitud_id)
