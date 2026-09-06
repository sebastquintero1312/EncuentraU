# Decoradores de autenticación y autorización.
#
# Regla de oro (ver skill "autorizacion"): el backend SIEMPRE verifica sesión
# y rol aquí. El frontend puede ocultar botones, pero eso nunca es seguridad
# real. El rol nunca se toma del cliente (body/header/cookie propia): siempre
# se relee de la base de datos usando el id guardado en la sesión del servidor.

from functools import wraps

from flask import session, jsonify

from app.models.usuario import buscar_por_id


def login_requerido(f):
    """Exige una sesión válida. Pasa el usuario autenticado como primer
    argumento posicional a la función decorada."""
    @wraps(f)
    def decorador(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        usuario = buscar_por_id(usuario_id)
        if not usuario or not usuario.activo:
            session.clear()
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        return f(usuario, *args, **kwargs)
    return decorador


def admin_requerido(f):
    """Exige una sesión válida Y rol de administrador. El rol se lee de la
    base de datos, nunca de lo que envía el cliente."""
    @wraps(f)
    def decorador(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        usuario = buscar_por_id(usuario_id)
        if not usuario or not usuario.activo:
            session.clear()
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        if usuario.rol != 'administrador':
            return jsonify({'mensaje': 'Acceso no autorizado'}), 403
        return f(usuario, *args, **kwargs)
    return decorador
