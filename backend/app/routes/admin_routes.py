# Rutas del ADMINISTRADOR. Todas exigen el rol administrador.

from flask import Blueprint

from app.controllers import admin_controller
from app.middlewares.autorizacion import admin_requerido

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# --- Usuarios
@admin_bp.route('/usuarios', methods=['GET'])
@admin_requerido
def listar_usuarios(admin):
    return admin_controller.listar_usuarios(admin)


@admin_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@admin_requerido
def actualizar_usuario(admin, usuario_id):
    return admin_controller.actualizar_usuario(admin, usuario_id)


@admin_bp.route('/usuarios/<int:usuario_id>/quitar-revision', methods=['POST'])
@admin_requerido
def quitar_revision(admin, usuario_id):
    return admin_controller.quitar_revision(admin, usuario_id)


# --- Catálogos y parámetros
@admin_bp.route('/categorias', methods=['GET'])
@admin_requerido
def listar_categorias(admin):
    return admin_controller.listar_categorias(admin)


@admin_bp.route('/categorias', methods=['POST'])
@admin_requerido
def crear_categoria(admin):
    return admin_controller.crear_categoria(admin)


@admin_bp.route('/categorias/<int:categoria_id>', methods=['PUT'])
@admin_requerido
def actualizar_categoria(admin, categoria_id):
    return admin_controller.actualizar_categoria(admin, categoria_id)


@admin_bp.route('/ubicaciones', methods=['GET'])
@admin_requerido
def listar_ubicaciones(admin):
    return admin_controller.listar_ubicaciones(admin)


@admin_bp.route('/ubicaciones', methods=['POST'])
@admin_requerido
def crear_ubicacion(admin):
    return admin_controller.crear_ubicacion(admin)


@admin_bp.route('/ubicaciones/<int:ubicacion_id>', methods=['PUT'])
@admin_requerido
def actualizar_ubicacion(admin, ubicacion_id):
    return admin_controller.actualizar_ubicacion(admin, ubicacion_id)


@admin_bp.route('/parametros', methods=['GET'])
@admin_requerido
def listar_parametros(admin):
    return admin_controller.listar_parametros(admin)


@admin_bp.route('/parametros/<clave>', methods=['PUT'])
@admin_requerido
def actualizar_parametro(admin, clave):
    return admin_controller.actualizar_parametro(admin, clave)


# --- Consulta: objetos, auditoría, estadísticas y exportación (solo lectura)
@admin_bp.route('/objetos', methods=['GET'])
@admin_requerido
def listar_objetos(admin):
    return admin_controller.listar_objetos(admin)


@admin_bp.route('/objetos/<int:objeto_id>', methods=['GET'])
@admin_requerido
def detalle_objeto(admin, objeto_id):
    return admin_controller.detalle_objeto(admin, objeto_id)


@admin_bp.route('/auditoria', methods=['GET'])
@admin_requerido
def listar_auditoria(admin):
    return admin_controller.listar_auditoria(admin)


@admin_bp.route('/estadisticas', methods=['GET'])
@admin_requerido
def estadisticas(admin):
    return admin_controller.estadisticas(admin)


@admin_bp.route('/exportar/objetos.csv', methods=['GET'])
@admin_requerido
def exportar_objetos(admin):
    return admin_controller.exportar_objetos(admin)


@admin_bp.route('/exportar/estadisticas-mensuales.csv', methods=['GET'])
@admin_requerido
def exportar_estadisticas(admin):
    return admin_controller.exportar_estadisticas(admin)
