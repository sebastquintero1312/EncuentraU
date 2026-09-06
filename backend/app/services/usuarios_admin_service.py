# Reglas de negocio de administración de usuarios.
#
# Solo accesible para administradores (verificado en el decorador
# admin_requerido de las rutas, no aquí). Este servicio solo aplica los
# cambios permitidos con una whitelist explícita: nunca se acepta cualquier
# campo que el cliente decida mandar (protección contra mass assignment).

from app.extensions import db
from app.models.usuario import Usuario, ROLES_VALIDOS


def listar_usuarios(filtros, pagina, por_pagina):
    query = Usuario.query

    q = (filtros.get('q') or '').strip()
    if q:
        patron = f'%{q}%'
        query = query.filter(db.or_(
            Usuario.correo.ilike(patron),
            Usuario.primer_nombre.ilike(patron),
            Usuario.primer_apellido.ilike(patron),
        ))

    rol = filtros.get('rol')
    if rol in ROLES_VALIDOS:
        query = query.filter(Usuario.rol == rol)

    query = query.order_by(Usuario.created_at.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def actualizar_usuario(usuario_objetivo, admin_actual, datos):
    """Aplica solo 'rol' y/o 'activo'. Un admin no puede quitarse a sí mismo
    el rol de admin ni desactivar su propia cuenta (evita bloqueo accidental
    del sistema sin ningún administrador activo)."""
    errores = {}

    if usuario_objetivo.id == admin_actual.id:
        errores['usuario_id'] = 'No puedes modificar tu propio rol o estado desde este panel'
        return errores

    if 'rol' in datos:
        rol = datos.get('rol')
        if rol not in ROLES_VALIDOS:
            errores['rol'] = 'Rol inválido'
        else:
            usuario_objetivo.rol = rol

    if 'activo' in datos:
        activo = datos.get('activo')
        if not isinstance(activo, bool):
            errores['activo'] = 'El campo "activo" debe ser verdadero o falso'
        else:
            usuario_objetivo.activo = activo

    if errores:
        db.session.rollback()
        return errores

    db.session.commit()
    return {}
