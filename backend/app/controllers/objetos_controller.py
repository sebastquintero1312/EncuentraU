# Controladores de reportes de objetos del lado del ESTUDIANTE.
# Solo leen la petición, verifican ownership y delegan la lógica a
# objetos_service. Los decoradores de middlewares/autorizacion.py ya
# garantizan sesión y rol antes de llegar aquí.

from flask import request, jsonify

from app.extensions import db
from app.models.objeto import Objeto, TIPO_PERDIDO
from app.models.solicitud import ESTADOS_ABIERTOS, Solicitud
from app.models.usuario import ROL_ESTUDIANTE
from app.services import coincidencias_service, objetos_service
from app.utils import parametros_paginacion, respuesta_paginada


def _datos():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def _reporte_propio(estudiante, objeto_id):
    """Devuelve (objeto, respuesta_error). Verifica ownership (IDOR):
    nadie puede modificar el reporte de otra persona cambiando el id."""
    objeto = db.session.get(Objeto, objeto_id)
    if objeto is None:
        return None, (jsonify({'mensaje': 'Reporte no encontrado'}), 404)
    if objeto.usuario_id != estudiante.id:
        return None, (jsonify({'mensaje': 'No autorizado'}), 403)
    return objeto, None


def buscar(estudiante):
    pagina, por_pagina = parametros_paginacion(request)
    paginado = objetos_service.buscar_disponibles(request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda o: o.vista_publica())), 200


def crear(estudiante):
    errores, objeto = objetos_service.crear_objeto(estudiante, _datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible crear el reporte', 'errores': errores}), 400
    return jsonify({'mensaje': 'Reporte creado correctamente', 'objeto': objeto.vista_propietario()}), 201


def detalle(usuario, objeto_id):
    """Un mismo objeto se muestra distinto según quién pregunta:
    - quien lo reportó: con su descripción privada
    - otro estudiante: solo la parte pública, y solo si está en la oficina
    - encargado o administrador: completo (vista de oficina)"""
    objeto = db.session.get(Objeto, objeto_id)
    if objeto is None:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404

    if usuario.rol != ROL_ESTUDIANTE:
        return jsonify({'objeto': objeto.vista_oficina()}), 200

    if objeto.usuario_id == usuario.id:
        return jsonify({'objeto': objeto.vista_propietario(), 'es_propio': True}), 200

    if not objeto.disponible_para_reclamar:
        return jsonify({'mensaje': 'No autorizado'}), 403

    reclamacion_abierta = Solicitud.query.filter(
        Solicitud.objeto_id == objeto.id,
        Solicitud.solicitante_id == usuario.id,
        Solicitud.estado.in_(ESTADOS_ABIERTOS),
    ).first()
    return jsonify({
        'objeto': objeto.vista_publica(),
        'es_propio': False,
        'reclamacion_abierta_id': reclamacion_abierta.id if reclamacion_abierta else None,
    }), 200


def actualizar(estudiante, objeto_id):
    objeto, error = _reporte_propio(estudiante, objeto_id)
    if error:
        return error
    errores, conflicto = objetos_service.actualizar_objeto(objeto, _datos())
    if conflicto:
        return jsonify({'mensaje': 'El reporte cambió mientras lo editabas. Recarga la página e inténtalo de nuevo.'}), 409
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar el reporte', 'errores': errores}), 400
    return jsonify({'mensaje': 'Reporte actualizado correctamente', 'objeto': objeto.vista_propietario()}), 200


def cancelar(estudiante, objeto_id):
    objeto, error = _reporte_propio(estudiante, objeto_id)
    if error:
        return error
    if not objetos_service.cancelar_objeto(objeto):
        return jsonify({'mensaje': f'No se puede cancelar un reporte en estado "{objeto.nombre_estado()}"'}), 400
    return jsonify({'mensaje': 'Reporte cancelado correctamente', 'objeto': objeto.vista_propietario()}), 200


def mis_reportes(estudiante):
    pagina, por_pagina = parametros_paginacion(request)
    paginado = objetos_service.mis_reportes(estudiante, request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda o: o.vista_propietario())), 200


def coincidencias(estudiante, objeto_id):
    """Objetos de la oficina que podrían ser el que el estudiante perdió
    (solo su parte pública)."""
    objeto, error = _reporte_propio(estudiante, objeto_id)
    if error:
        return error
    if objeto.tipo != TIPO_PERDIDO:
        return jsonify({'datos': []}), 200
    pares = coincidencias_service.encontrados_para_perdido(objeto)
    return jsonify({'datos': [dict(o.vista_publica(), puntaje=p) for o, p in pares]}), 200
