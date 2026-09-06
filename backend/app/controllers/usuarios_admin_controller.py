# Controladores de administración de usuarios. Todas las rutas que usan
# este controlador están protegidas con @admin_requerido (ver routes/).

from flask import request, jsonify

from app.models.usuario import buscar_por_id, usuario_publico
from app.services import usuarios_admin_service
from app.utils import parametros_paginacion


def listar(usuario_actual):
    pagina, por_pagina = parametros_paginacion(request)
    filtros = {'q': request.args.get('q'), 'rol': request.args.get('rol')}
    paginado = usuarios_admin_service.listar_usuarios(filtros, pagina, por_pagina)
    return jsonify({
        'datos': [usuario_publico(u) for u in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }), 200


def actualizar(usuario_actual, usuario_id):
    usuario_objetivo = buscar_por_id(usuario_id)
    if not usuario_objetivo:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404

    datos = request.get_json(silent=True) or {}
    # Whitelist explícita: solo 'rol' y 'activo' pueden cambiar, y solo esos
    # dos campos se leen del body (ver usuarios_admin_service).
    permitido = {}
    if 'rol' in datos:
        permitido['rol'] = datos.get('rol')
    if 'activo' in datos:
        permitido['activo'] = datos.get('activo')

    errores = usuarios_admin_service.actualizar_usuario(usuario_objetivo, usuario_actual, permitido)
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar el usuario', 'errores': errores}), 400
    return jsonify({'mensaje': 'Usuario actualizado correctamente', 'usuario': usuario_publico(usuario_objetivo)}), 200
