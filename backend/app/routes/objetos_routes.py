# Rutas de reportes de objetos (perdidos/encontrados).
# Cada ruta solo define URL, método HTTP y protección (auth/rol/rate limit).
# La lógica vive en objetos_controller.py.

from flask import Blueprint

from app.controllers import objetos_controller
from app.extensions import limiter
from app.middlewares.autorizacion import login_requerido

objetos_bp = Blueprint('objetos', __name__, url_prefix='/api')

LIMITE_CREACION = '20 per hour'


@objetos_bp.route('/objetos', methods=['GET'])
def listar_objetos():
    return objetos_controller.listar()


@objetos_bp.route('/objetos', methods=['POST'])
@limiter.limit(LIMITE_CREACION)
@login_requerido
def crear_objeto(usuario_actual):
    return objetos_controller.crear(usuario_actual)


@objetos_bp.route('/objetos/<int:objeto_id>', methods=['GET'])
def detalle_objeto(objeto_id):
    return objetos_controller.detalle(objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>', methods=['PUT'])
@login_requerido
def actualizar_objeto(usuario_actual, objeto_id):
    return objetos_controller.actualizar(usuario_actual, objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>', methods=['DELETE'])
@login_requerido
def cancelar_objeto(usuario_actual, objeto_id):
    return objetos_controller.cancelar(usuario_actual, objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>/solicitudes', methods=['GET'])
@login_requerido
def solicitudes_del_objeto(usuario_actual, objeto_id):
    return objetos_controller.solicitudes_del_objeto(usuario_actual, objeto_id)


@objetos_bp.route('/mis-reportes', methods=['GET'])
@login_requerido
def mis_reportes(usuario_actual):
    return objetos_controller.mis_reportes(usuario_actual)
