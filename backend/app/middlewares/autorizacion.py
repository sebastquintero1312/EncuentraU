# Decoradores de autenticación y autorización.
#
# Regla de oro (ver skill "autorizacion"): el backend SIEMPRE verifica sesión
# y rol aquí. El frontend puede ocultar botones, pero eso nunca es seguridad
# real. El rol nunca se toma del cliente (body/header/cookie propia): siempre
# se relee de la base de datos usando el id guardado en la sesión del servidor.
#
# v2.0: tres roles con permisos SEPARADOS (deny by default). Cada ruta declara
# exactamente qué rol puede usarla:
#   @estudiante_requerido   reportar, buscar, reclamar
#   @encargado_requerido    recibir, verificar, entregar
#   @admin_requerido        usuarios, catálogos, auditoría
#   @login_requerido        cualquier rol (notificaciones, catálogos de lectura)

from functools import wraps

from flask import session, jsonify

from app.auditoria_contexto import fijar_usuario_auditoria
from app.models.usuario import buscar_por_id, ROL_ESTUDIANTE, ROL_ENCARGADO, ROL_ADMINISTRADOR


def _usuario_de_la_sesion():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return None
    usuario = buscar_por_id(usuario_id)
    if not usuario or not usuario.activo:
        session.clear()
        return None
    fijar_usuario_auditoria(usuario.id)
    return usuario


def login_requerido(f):
    """Exige una sesión válida (cualquier rol). Pasa el usuario autenticado
    como primer argumento posicional a la función decorada."""
    @wraps(f)
    def decorador(*args, **kwargs):
        usuario = _usuario_de_la_sesion()
        if usuario is None:
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        return f(usuario, *args, **kwargs)
    return decorador


def rol_requerido(*roles_permitidos):
    """Exige sesión válida Y que el rol (leído de la base de datos) sea uno
    de los indicados. Sin sesión: 401. Con otro rol: 403."""
    def decorador_externo(f):
        @wraps(f)
        def decorador(*args, **kwargs):
            usuario = _usuario_de_la_sesion()
            if usuario is None:
                return jsonify({'mensaje': 'Autenticación requerida'}), 401
            if usuario.rol not in roles_permitidos:
                return jsonify({'mensaje': 'No tienes permiso para realizar esta acción'}), 403
            return f(usuario, *args, **kwargs)
        return decorador
    return decorador_externo


estudiante_requerido = rol_requerido(ROL_ESTUDIANTE)
encargado_requerido = rol_requerido(ROL_ENCARGADO)
admin_requerido = rol_requerido(ROL_ADMINISTRADOR)
