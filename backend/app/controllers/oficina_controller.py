# Controladores del ENCARGADO de la oficina. Todas las rutas que los usan
# están protegidas con @encargado_requerido (ver routes/oficina_routes.py).

from flask import request, jsonify

from app.extensions import db
from app.models import reportes
from app.models.objeto import Objeto
from app.models.solicitud import Solicitud
from app.services import objetos_service, oficina_service
from app.utils import parametros_paginacion, respuesta_paginada, texto


def _datos():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def listar_objetos(encargado):
    oficina_service.vencer_reservas()
    pagina, por_pagina = parametros_paginacion(request)
    paginado = objetos_service.listar_para_oficina(request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda o: o.vista_oficina())), 200


def detalle_objeto(encargado, objeto_id):
    oficina_service.vencer_reservas()
    objeto = db.session.get(Objeto, objeto_id)
    if objeto is None:
        return jsonify({'mensaje': 'Objeto no encontrado'}), 404
    return jsonify(oficina_service.detalle_objeto(objeto)), 200


def recibir(encargado, objeto_id):
    objeto, error = oficina_service.recibir_objeto(encargado, objeto_id, _datos().get('observaciones'))
    if error:
        return jsonify({'mensaje': error}), 400
    return jsonify({'mensaje': 'Objeto recibido en la oficina', 'objeto': objeto.vista_oficina()}), 200


def cerrar(encargado, objeto_id):
    objeto, error = oficina_service.cerrar_objeto(encargado, objeto_id, _datos().get('motivo'))
    if error:
        return jsonify({'mensaje': error}), 400
    return jsonify({'mensaje': 'Reporte cerrado', 'objeto': objeto.vista_oficina()}), 200


def entregar(encargado, objeto_id):
    ok, mensaje, entrega = oficina_service.entregar(encargado, objeto_id, _datos())
    if not ok:
        return jsonify({'mensaje': mensaje}), 400
    return jsonify({'mensaje': mensaje, 'entrega': entrega.a_dict()}), 200


def listar_solicitudes(encargado):
    oficina_service.vencer_reservas()
    pagina, por_pagina = parametros_paginacion(request)
    estado = texto(request.args.get('estado')) or 'pendiente'
    if estado == 'todas':
        estado = None
    paginado = oficina_service.listar_solicitudes(estado, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda s: s.vista_oficina())), 200


def detalle_solicitud(encargado, solicitud_id):
    solicitud = db.session.get(Solicitud, solicitud_id)
    if solicitud is None:
        return jsonify({'mensaje': 'Reclamación no encontrada'}), 404
    otras = Solicitud.query.filter(
        Solicitud.objeto_id == solicitud.objeto_id, Solicitud.id != solicitud.id,
    ).order_by(Solicitud.created_at.asc()).all()
    return jsonify({
        'solicitud': solicitud.vista_oficina(),
        'otras_solicitudes': [s.vista_oficina() for s in otras],
    }), 200


def preaprobar(encargado, solicitud_id):
    solicitud, error = oficina_service.preaprobar(encargado, solicitud_id, _datos().get('respuesta'))
    if error:
        return jsonify({'mensaje': error}), 400
    return jsonify({'mensaje': 'Reclamación pre-aprobada', 'solicitud': solicitud.vista_oficina()}), 200


def rechazar(encargado, solicitud_id):
    solicitud, error = oficina_service.rechazar(encargado, solicitud_id, _datos().get('motivo'))
    if error:
        return jsonify({'mensaje': error}), 400
    return jsonify({'mensaje': 'Reclamación rechazada', 'solicitud': solicitud.vista_oficina()}), 200


def estadisticas(encargado):
    oficina_service.vencer_reservas()
    return jsonify({'generales': reportes.estadisticas_generales()}), 200
