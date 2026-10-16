# Controladores del ADMINISTRADOR: usuarios, catálogos, parámetros,
# auditoría, estadísticas y exportación. Todas las rutas que los usan están
# protegidas con @admin_requerido (ver routes/admin_routes.py).
#
# El administrador ve todo pero NO opera: no reporta, no reclama, no aprueba
# ni entrega objetos (separación de funciones con el encargado).

from flask import Response, request, jsonify

from app.extensions import db
from app.models import reportes
from app.models.catalogo import Categoria, Parametro, Ubicacion
from app.models.objeto import Objeto
from app.models.usuario import buscar_por_id, usuario_para_admin
from app.services import auditoria_service, catalogos_service, objetos_service, oficina_service, usuarios_admin_service
from app.utils import parametros_paginacion, respuesta_paginada


def _datos():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


# --- Usuarios -------------------------------------------------------------

def listar_usuarios(admin):
    pagina, por_pagina = parametros_paginacion(request)
    paginado = usuarios_admin_service.listar_usuarios(request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, usuario_para_admin)), 200


def actualizar_usuario(admin, usuario_id):
    usuario_objetivo = buscar_por_id(usuario_id)
    if not usuario_objetivo:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404

    datos = _datos()
    # Whitelist explícita: solo 'rol' y 'activo' pueden cambiar, y solo esos
    # dos campos se leen del body.
    permitido = {campo: datos.get(campo) for campo in ('rol', 'activo') if campo in datos}

    errores = usuarios_admin_service.actualizar_usuario(usuario_objetivo, admin, permitido)
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar el usuario', 'errores': errores}), 400
    return jsonify({'mensaje': 'Usuario actualizado correctamente', 'usuario': usuario_para_admin(usuario_objetivo)}), 200


def quitar_revision(admin, usuario_id):
    usuario_objetivo = buscar_por_id(usuario_id)
    if not usuario_objetivo:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404
    if not usuarios_admin_service.quitar_revision(usuario_objetivo):
        return jsonify({'mensaje': 'Esta cuenta no está en revisión'}), 400
    return jsonify({'mensaje': 'Revisión levantada', 'usuario': usuario_para_admin(usuario_objetivo)}), 200


# --- Catálogos ------------------------------------------------------------

def listar_categorias(admin):
    return jsonify({'datos': [c.a_dict() for c in catalogos_service.listar(Categoria)]}), 200


def crear_categoria(admin):
    errores, categoria = catalogos_service.crear_categoria(_datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible crear la categoría', 'errores': errores}), 400
    return jsonify({'mensaje': 'Categoría creada', 'categoria': categoria.a_dict()}), 201


def actualizar_categoria(admin, categoria_id):
    categoria = db.session.get(Categoria, categoria_id)
    if categoria is None:
        return jsonify({'mensaje': 'Categoría no encontrada'}), 404
    errores = catalogos_service.actualizar_categoria(categoria, _datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar la categoría', 'errores': errores}), 400
    return jsonify({'mensaje': 'Categoría actualizada', 'categoria': categoria.a_dict()}), 200


def listar_ubicaciones(admin):
    return jsonify({'datos': [u.a_dict() for u in catalogos_service.listar(Ubicacion)]}), 200


def crear_ubicacion(admin):
    errores, ubicacion = catalogos_service.crear_ubicacion(_datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible crear la ubicación', 'errores': errores}), 400
    return jsonify({'mensaje': 'Ubicación creada', 'ubicacion': ubicacion.a_dict()}), 201


def actualizar_ubicacion(admin, ubicacion_id):
    ubicacion = db.session.get(Ubicacion, ubicacion_id)
    if ubicacion is None:
        return jsonify({'mensaje': 'Ubicación no encontrada'}), 404
    errores = catalogos_service.actualizar_ubicacion(ubicacion, _datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar la ubicación', 'errores': errores}), 400
    return jsonify({'mensaje': 'Ubicación actualizada', 'ubicacion': ubicacion.a_dict()}), 200


def listar_parametros(admin):
    return jsonify({'datos': [p.a_dict() for p in catalogos_service.listar_parametros()]}), 200


def actualizar_parametro(admin, clave):
    parametro = db.session.get(Parametro, clave)
    if parametro is None:
        return jsonify({'mensaje': 'Parámetro no encontrado'}), 404
    errores = catalogos_service.actualizar_parametro(parametro, _datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible actualizar el parámetro', 'errores': errores}), 400
    return jsonify({'mensaje': 'Parámetro actualizado', 'parametro': parametro.a_dict()}), 200


# --- Consulta (solo lectura) ----------------------------------------------

def listar_objetos(admin):
    pagina, por_pagina = parametros_paginacion(request)
    paginado = objetos_service.listar_para_oficina(request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda o: o.vista_oficina())), 200


def detalle_objeto(admin, objeto_id):
    objeto = db.session.get(Objeto, objeto_id)
    if objeto is None:
        return jsonify({'mensaje': 'Objeto no encontrado'}), 404
    return jsonify(oficina_service.detalle_objeto(objeto)), 200


def listar_auditoria(admin):
    pagina, por_pagina = parametros_paginacion(request)
    paginado = auditoria_service.listar(request.args, pagina, por_pagina)
    return jsonify(respuesta_paginada(paginado, pagina, por_pagina, lambda a: a.a_dict())), 200


def estadisticas(admin):
    return jsonify({
        'generales': reportes.estadisticas_generales(),
        'mensuales': reportes.estadisticas_mensuales(meses=12),
        'encargados': reportes.desempeno_encargados(),
    }), 200


def _descarga_csv(contenido, nombre_archivo):
    return Response(
        contenido,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{nombre_archivo}"'},
    )


def exportar_objetos(admin):
    return _descarga_csv(auditoria_service.csv_objetos(), 'encuentrau_objetos.csv')


def exportar_estadisticas(admin):
    return _descarga_csv(auditoria_service.csv_estadisticas_mensuales(), 'encuentrau_estadisticas_mensuales.csv')
