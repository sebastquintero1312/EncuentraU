# Controladores de reclamaciones del lado del ESTUDIANTE.

from flask import request, jsonify

from app.extensions import db
from app.models.solicitud import Solicitud
from app.services import oficina_service, solicitudes_service
from app.utils import parametros_paginacion, respuesta_paginada


def _datos():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def _solicitud_propia(estudiante, solicitud_id):
    solicitud = db.session.get(Solicitud, solicitud_id)
    if solicitud is None:
        return None, (jsonify({'mensaje': 'Reclamación no encontrada'}), 404)
    if solicitud.solicitante_id != estudiante.id:
        return None, (jsonify({'mensaje': 'No autorizado'}), 403)
    return solicitud, None


def crear(estudiante):
    errores, solicitud = solicitudes_service.crear_solicitud(estudiante, _datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible enviar la reclamación', 'errores': errores}), 400
    return jsonify({'mensaje': 'Reclamación enviada correctamente', 'solicitud': solicitud.vista_estudiante()}), 201


def mis_solicitudes(estudiante):
    oficina_service.vencer_reservas()
    pagina, por_pagina = parametros_paginacion(request)
    paginado = solicitudes_service.mis_solicitudes(estudiante, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda s: s.vista_estudiante())), 200


def cancelar(estudiante, solicitud_id):
    solicitud, error = _solicitud_propia(estudiante, solicitud_id)
    if error:
        return error
    if not solicitudes_service.cancelar_solicitud(solicitud):
        return jsonify({'mensaje': 'Esta reclamación ya está cerrada'}), 400
    return jsonify({'mensaje': 'Reclamación cancelada', 'solicitud': solicitud.vista_estudiante()}), 200


def generar_codigo(estudiante, solicitud_id):
    oficina_service.vencer_reservas()
    solicitud, error = _solicitud_propia(estudiante, solicitud_id)
    if error:
        return error
    codigo, mensaje_error = solicitudes_service.generar_codigo_retiro(solicitud)
    if mensaje_error:
        return jsonify({'mensaje': mensaje_error}), 400
    return jsonify({
        'mensaje': 'Código generado. Anótalo: por seguridad no se puede volver a mostrar.',
        'codigo': codigo,
        'vence_en': solicitud.vence_en.isoformat(),
    }), 200
