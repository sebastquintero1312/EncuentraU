# Controladores de reportes de objetos (perdidos/encontrados).
# Solo leen la petición, verifican permisos de alto nivel (ownership) y
# delegan la lógica de negocio a objetos_service. Los decoradores de
# middlewares/autorizacion.py ya garantizan sesión/rol antes de llegar aquí.

from flask import request, jsonify

from app.extensions import db
from app.models.objeto import Objeto, TIPOS_VALIDOS, ESTADOS_VALIDOS
from app.models.solicitud import Solicitud
from app.services import objetos_service, coincidencias_service
from app.utils import parametros_paginacion


def _es_dueno_o_admin(objeto, usuario):
    return objeto.usuario_id == usuario.id or usuario.rol == 'administrador'


def listar():
    filtros = {
        'tipo': request.args.get('tipo'),
        'categoria': request.args.get('categoria'),
        'estado': request.args.get('estado'),
        'ubicacion': request.args.get('ubicacion'),
        'q': request.args.get('q'),
    }
    pagina, por_pagina = parametros_paginacion(request)
    paginado = objetos_service.buscar_objetos(filtros, pagina, por_pagina)

    return jsonify({
        'datos': [o.publico() for o in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }), 200


def crear(usuario_actual):
    datos = request.get_json(silent=True) or {}
    errores, objeto = objetos_service.crear_objeto(usuario_actual.id, datos)
    if errores:
        return jsonify({'mensaje': 'No fue posible crear el reporte', 'errores': errores}), 400
    return jsonify({'mensaje': 'Reporte creado correctamente', 'objeto': objeto.publico()}), 201


def detalle(objeto_id):
    objeto = db.session.get(Objeto, objeto_id)
    if not objeto:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404

    respuesta = {'objeto': objeto.publico()}
    if objeto.estado in ('activo', 'en_proceso'):
        respuesta['coincidencias'] = coincidencias_service.encontrar_coincidencias(objeto)
    else:
        respuesta['coincidencias'] = []
    return jsonify(respuesta), 200


def actualizar(usuario_actual, objeto_id):
    objeto = db.session.get(Objeto, objeto_id)
    if not objeto:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404
    if not _es_dueno_o_admin(objeto, usuario_actual):
        return jsonify({'mensaje': 'No autorizado'}), 403

    datos = request.get_json(silent=True) or {}
    errores = objetos_service.actualizar_objeto(objeto, datos)
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar el reporte', 'errores': errores}), 400
    return jsonify({'mensaje': 'Reporte actualizado correctamente', 'objeto': objeto.publico()}), 200


def cancelar(usuario_actual, objeto_id):
    objeto = db.session.get(Objeto, objeto_id)
    if not objeto:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404
    if not _es_dueno_o_admin(objeto, usuario_actual):
        return jsonify({'mensaje': 'No autorizado'}), 403

    if not objetos_service.cancelar_objeto(objeto):
        return jsonify({'mensaje': f'No se puede cancelar un reporte en estado "{objeto.estado}"'}), 400
    return jsonify({'mensaje': 'Reporte cancelado correctamente', 'objeto': objeto.publico()}), 200


def mis_reportes(usuario_actual):
    pagina, por_pagina = parametros_paginacion(request)
    filtros = {
        'estado': request.args.get('estado'),
        'tipo': request.args.get('tipo'),
    }
    query = Objeto.query.filter(Objeto.usuario_id == usuario_actual.id)

    if filtros['tipo'] in TIPOS_VALIDOS:
        query = query.filter(Objeto.tipo == filtros['tipo'])
    if filtros['estado'] in ESTADOS_VALIDOS:
        query = query.filter(Objeto.estado == filtros['estado'])

    query = query.order_by(Objeto.created_at.desc())
    paginado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    return jsonify({
        'datos': [o.publico() for o in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }), 200


def solicitudes_del_objeto(usuario_actual, objeto_id):
    """Información de verificación PRIVADA: solo la ve el dueño del reporte
    o un administrador (ver docstring de models/solicitud.py)."""
    objeto = db.session.get(Objeto, objeto_id)
    if not objeto:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404
    if not _es_dueno_o_admin(objeto, usuario_actual):
        return jsonify({'mensaje': 'No autorizado'}), 403

    solicitudes = objeto.solicitudes.order_by(Solicitud.created_at.desc()).all()
    return jsonify({'datos': [s.publica() for s in solicitudes]}), 200
