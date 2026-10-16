# Rutas de reportes de objetos (perdidos/encontrados) del lado del ESTUDIANTE.
# Cada ruta solo define URL, método HTTP y protección (auth/rol/rate limit).
# La lógica vive en objetos_controller.py.
#
# Deny by default: reportar, editar, cancelar y buscar es exclusivo del rol
# estudiante. El encargado y el administrador tienen sus propias rutas (de
# consulta y operación) en oficina_routes.py y admin_routes.py.

from flask import Blueprint

from app.controllers import objetos_controller
from app.extensions import limiter
from app.middlewares.autorizacion import estudiante_requerido, login_requerido

objetos_bp = Blueprint('objetos', __name__, url_prefix='/api')

LIMITE_CREACION = '20 per hour'


@objetos_bp.route('/objetos', methods=['GET'])
@estudiante_requerido
def buscar_objetos(estudiante):
    return objetos_controller.buscar(estudiante)


@objetos_bp.route('/objetos', methods=['POST'])
@limiter.limit(LIMITE_CREACION)
@estudiante_requerido
def crear_objeto(estudiante):
    return objetos_controller.crear(estudiante)


@objetos_bp.route('/objetos/<int:objeto_id>', methods=['GET'])
@login_requerido
def detalle_objeto(usuario, objeto_id):
    return objetos_controller.detalle(usuario, objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>', methods=['PUT'])
@estudiante_requerido
def actualizar_objeto(estudiante, objeto_id):
    return objetos_controller.actualizar(estudiante, objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>/cancelar', methods=['POST'])
@estudiante_requerido
def cancelar_objeto(estudiante, objeto_id):
    return objetos_controller.cancelar(estudiante, objeto_id)


@objetos_bp.route('/objetos/<int:objeto_id>/coincidencias', methods=['GET'])
@estudiante_requerido
def coincidencias_objeto(estudiante, objeto_id):
    return objetos_controller.coincidencias(estudiante, objeto_id)


@objetos_bp.route('/mis-reportes', methods=['GET'])
@estudiante_requerido
def mis_reportes(estudiante):
    return objetos_controller.mis_reportes(estudiante)
