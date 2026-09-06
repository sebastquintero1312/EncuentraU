# Rutas de administración de usuarios. Todas exigen rol de administrador.

from flask import Blueprint

from app.controllers import usuarios_admin_controller, objetos_controller
from app.middlewares.autorizacion import admin_requerido

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/usuarios', methods=['GET'])
@admin_requerido
def listar_usuarios(usuario_actual):
    return usuarios_admin_controller.listar(usuario_actual)


@admin_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@admin_requerido
def actualizar_usuario(usuario_actual, usuario_id):
    return usuarios_admin_controller.actualizar(usuario_actual, usuario_id)


@admin_bp.route('/objetos', methods=['GET'])
@admin_requerido
def listar_objetos(usuario_actual):
    return objetos_controller.listar_admin()


@admin_bp.route('/objetos/<int:objeto_id>/estado', methods=['PUT'])
@admin_requerido
def cambiar_estado_objeto(usuario_actual, objeto_id):
    return objetos_controller.cambiar_estado_admin(usuario_actual, objeto_id)
