# Rutas del ENCARGADO de la oficina de objetos perdidos.
# Todas exigen el rol encargado: ni un estudiante ni el administrador pueden
# recibir, aprobar o entregar objetos (separación de funciones).

from flask import Blueprint

from app.controllers import oficina_controller
from app.extensions import limiter
from app.middlewares.autorizacion import encargado_requerido

oficina_bp = Blueprint('oficina', __name__, url_prefix='/api/encargado')

# El código de retiro ya tiene su propio límite de intentos por reclamación;
# este límite adicional frena a quien pruebe códigos en muchos objetos.
LIMITE_ENTREGA = '30 per hour'


@oficina_bp.route('/objetos', methods=['GET'])
@encargado_requerido
def listar_objetos(encargado):
    return oficina_controller.listar_objetos(encargado)


@oficina_bp.route('/objetos/<int:objeto_id>', methods=['GET'])
@encargado_requerido
def detalle_objeto(encargado, objeto_id):
    return oficina_controller.detalle_objeto(encargado, objeto_id)


@oficina_bp.route('/objetos/<int:objeto_id>/recepcion', methods=['POST'])
@encargado_requerido
def recibir_objeto(encargado, objeto_id):
    return oficina_controller.recibir(encargado, objeto_id)


@oficina_bp.route('/objetos/<int:objeto_id>/cerrar', methods=['POST'])
@encargado_requerido
def cerrar_objeto(encargado, objeto_id):
    return oficina_controller.cerrar(encargado, objeto_id)


@oficina_bp.route('/objetos/<int:objeto_id>/entrega', methods=['POST'])
@limiter.limit(LIMITE_ENTREGA)
@encargado_requerido
def entregar_objeto(encargado, objeto_id):
    return oficina_controller.entregar(encargado, objeto_id)


@oficina_bp.route('/solicitudes', methods=['GET'])
@encargado_requerido
def listar_solicitudes(encargado):
    return oficina_controller.listar_solicitudes(encargado)


@oficina_bp.route('/solicitudes/<int:solicitud_id>', methods=['GET'])
@encargado_requerido
def detalle_solicitud(encargado, solicitud_id):
    return oficina_controller.detalle_solicitud(encargado, solicitud_id)


@oficina_bp.route('/solicitudes/<int:solicitud_id>/preaprobar', methods=['POST'])
@encargado_requerido
def preaprobar_solicitud(encargado, solicitud_id):
    return oficina_controller.preaprobar(encargado, solicitud_id)


@oficina_bp.route('/solicitudes/<int:solicitud_id>/rechazar', methods=['POST'])
@encargado_requerido
def rechazar_solicitud(encargado, solicitud_id):
    return oficina_controller.rechazar(encargado, solicitud_id)


@oficina_bp.route('/estadisticas', methods=['GET'])
@encargado_requerido
def estadisticas(encargado):
    return oficina_controller.estadisticas(encargado)
