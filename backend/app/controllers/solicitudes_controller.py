# Controladores del proceso de reclamación (solicitudes).

from flask import request, jsonify

from app.extensions import db
from app.models.solicitud import Solicitud, ESTADOS_VALIDOS
from app.services import solicitudes_service
from app.utils import parametros_paginacion


def crear(usuario_actual):
    datos = request.get_json(silent=True) or {}
    objeto_id = datos.get('objeto_id')

    if not isinstance(objeto_id, int):
        try:
            objeto_id = int(objeto_id)
        except (TypeError, ValueError):
            return jsonify({'mensaje': 'objeto_id inválido'}), 400

    errores, solicitud = solicitudes_service.crear_solicitud(
        objeto_id, usuario_actual, datos.get('contacto'), datos.get('mensaje'),
    )
    if errores:
        return jsonify({'mensaje': 'No fue posible enviar la solicitud', 'errores': errores}), 400
    return jsonify({'mensaje': 'Solicitud enviada correctamente', 'solicitud': solicitud.publica()}), 201


def mis_solicitudes(usuario_actual):
    pagina, por_pagina = parametros_paginacion(request)
    query = Solicitud.query.filter(Solicitud.solicitante_id == usuario_actual.id).order_by(Solicitud.created_at.desc())
    paginado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    return jsonify({
        'datos': [s.publica() for s in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }), 200


def cancelar(usuario_actual, solicitud_id):
    solicitud = db.session.get(Solicitud, solicitud_id)
    if not solicitud:
        return jsonify({'mensaje': 'Solicitud no encontrada'}), 404
    if solicitud.solicitante_id != usuario_actual.id:
        return jsonify({'mensaje': 'No autorizado'}), 403
    if not solicitudes_service.cancelar_solicitud(solicitud):
        return jsonify({'mensaje': f'No se puede cancelar una solicitud en estado "{solicitud.estado}"'}), 400
    return jsonify({'mensaje': 'Solicitud cancelada correctamente', 'solicitud': solicitud.publica()}), 200


def listar_admin():
    pagina, por_pagina = parametros_paginacion(request)
    query = Solicitud.query
    estado = request.args.get('estado')
    if estado in ESTADOS_VALIDOS:
        query = query.filter(Solicitud.estado == estado)
    query = query.order_by(Solicitud.created_at.desc())
    paginado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    return jsonify({
        'datos': [s.publica() for s in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }), 200


def revisar_admin(solicitud_id):
    solicitud = db.session.get(Solicitud, solicitud_id)
    if not solicitud:
        return jsonify({'mensaje': 'Solicitud no encontrada'}), 404

    datos = request.get_json(silent=True) or {}
    ok, error = solicitudes_service.revisar_solicitud(
        solicitud, datos.get('estado'), datos.get('respuesta_admin'),
    )
    if not ok:
        return jsonify({'mensaje': error}), 400
    return jsonify({'mensaje': 'Solicitud actualizada correctamente', 'solicitud': solicitud.publica()}), 200
