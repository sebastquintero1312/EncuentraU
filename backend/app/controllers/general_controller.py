# Controladores comunes a todos los roles: catálogos para los formularios,
# notificaciones propias y estadísticas públicas de la página de inicio.

from flask import request, jsonify

from app.models import reportes
from app.models.catalogo import categorias_activas, ubicaciones_activas
from app.services import notificaciones_service, objetos_service


def catalogos(usuario):
    return jsonify({
        'categorias': [c.a_dict() for c in categorias_activas()],
        'ubicaciones': [u.a_dict() for u in ubicaciones_activas()],
        'estados': objetos_service.estados_por_tipo(),
    }), 200


def estadisticas_publicas():
    """Solo números agregados: sin nombres, correos ni detalles de objetos."""
    generales = reportes.estadisticas_generales()
    return jsonify({
        'en_custodia': generales.get('en_custodia', 0),
        'entregados': generales.get('entregados', 0),
    }), 200


def listar_notificaciones(usuario):
    solo_no_leidas = request.args.get('no_leidas') in ('1', 'true')
    notificaciones = notificaciones_service.listar(usuario, solo_no_leidas)
    return jsonify({
        'datos': [n.a_dict() for n in notificaciones],
        'no_leidas': notificaciones_service.contar_no_leidas(usuario),
    }), 200


def marcar_leida(usuario, notificacion_id):
    if not notificaciones_service.marcar_leida(usuario, notificacion_id):
        return jsonify({'mensaje': 'Notificación no encontrada'}), 404
    return jsonify({'mensaje': 'Notificación marcada como leída'}), 200


def marcar_todas_leidas(usuario):
    notificaciones_service.marcar_todas_leidas(usuario)
    return jsonify({'mensaje': 'Todas las notificaciones quedaron como leídas'}), 200
