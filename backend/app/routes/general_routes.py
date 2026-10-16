# Rutas comunes a todos los roles.

from flask import Blueprint

from app.controllers import general_controller
from app.middlewares.autorizacion import login_requerido

general_bp = Blueprint('general', __name__, url_prefix='/api')


@general_bp.route('/catalogos', methods=['GET'])
@login_requerido
def catalogos(usuario):
    return general_controller.catalogos(usuario)


@general_bp.route('/estadisticas/publicas', methods=['GET'])
def estadisticas_publicas():
    return general_controller.estadisticas_publicas()


@general_bp.route('/notificaciones', methods=['GET'])
@login_requerido
def listar_notificaciones(usuario):
    return general_controller.listar_notificaciones(usuario)


@general_bp.route('/notificaciones/<int:notificacion_id>/leida', methods=['POST'])
@login_requerido
def marcar_leida(usuario, notificacion_id):
    return general_controller.marcar_leida(usuario, notificacion_id)


@general_bp.route('/notificaciones/leer-todas', methods=['POST'])
@login_requerido
def marcar_todas_leidas(usuario):
    return general_controller.marcar_todas_leidas(usuario)
