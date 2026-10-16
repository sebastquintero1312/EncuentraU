# Reglas de negocio de administración de usuarios.
#
# Solo accesible para administradores (verificado en el decorador
# admin_requerido de las rutas, no aquí). Este servicio solo aplica los
# cambios permitidos con una whitelist explícita: nunca se acepta cualquier
# campo que el cliente decida mandar (protección contra mass assignment).
#
# Separación de funciones:
#   * Desde la web solo se puede asignar el rol estudiante o encargado.
#     Un administrador nuevo solo se crea desde la terminal del servidor
#     (flask crear-admin): así, una cuenta de administrador robada no puede
#     fabricar más administradores.
#   * Un administrador no puede modificarse a sí mismo ni a otro administrador.
#   * Solo una cuenta con el correo verificado puede ser encargado.

from app.extensions import db
from app.models.usuario import ROL_ADMINISTRADOR, ROL_ENCARGADO, ROL_ESTUDIANTE, ROLES_VALIDOS, Usuario
from app.services import notificaciones_service
from app.services.objetos_service import patron_busqueda
from app.utils import texto

ROLES_ASIGNABLES_DESDE_LA_WEB = (ROL_ESTUDIANTE, ROL_ENCARGADO)
NOMBRES_ROL = {ROL_ESTUDIANTE: 'estudiante', ROL_ENCARGADO: 'encargado', ROL_ADMINISTRADOR: 'administrador'}


def listar_usuarios(filtros, pagina, por_pagina):
    query = Usuario.query

    if texto(filtros.get('q')):
        patron = patron_busqueda(filtros.get('q'))
        query = query.filter(db.or_(
            Usuario.correo.ilike(patron, escape='\\'),
            Usuario.primer_nombre.ilike(patron, escape='\\'),
            Usuario.primer_apellido.ilike(patron, escape='\\'),
        ))

    rol = filtros.get('rol')
    if rol in ROLES_VALIDOS:
        query = query.filter(Usuario.rol == rol)
    if filtros.get('marcados') in ('1', 'true'):
        query = query.filter(Usuario.marcado_revision.is_(True))

    query = query.order_by(Usuario.created_at.desc(), Usuario.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def actualizar_usuario(usuario_objetivo, admin_actual, datos):
    """Aplica solo 'rol' y/o 'activo'. Devuelve un diccionario de errores."""
    errores = {}

    if usuario_objetivo.id == admin_actual.id:
        return {'usuario_id': 'No puedes modificar tu propio rol o estado desde este panel'}
    if usuario_objetivo.rol == ROL_ADMINISTRADOR:
        return {'usuario_id': 'Las cuentas de administrador solo se gestionan desde la terminal del servidor'}

    rol_anterior = usuario_objetivo.rol
    if 'rol' in datos:
        rol = datos.get('rol')
        if rol not in ROLES_ASIGNABLES_DESDE_LA_WEB:
            errores['rol'] = 'Rol inválido: desde la web solo se puede asignar estudiante o encargado'
        elif rol == ROL_ENCARGADO and not usuario_objetivo.correo_verificado:
            errores['rol'] = 'Solo una cuenta con el correo verificado puede ser encargado'
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

    notificaciones = []
    if usuario_objetivo.rol != rol_anterior:
        notificaciones.append(notificaciones_service.crear(
            usuario_objetivo, 'rol_cambiado', 'Cambió tu rol en EncuentraU',
            f'Un administrador cambió tu rol a {NOMBRES_ROL[usuario_objetivo.rol]}. '
            'Cierra sesión y vuelve a entrar para ver tus nuevas opciones.',
        ))
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return {}


def quitar_revision(usuario_objetivo):
    """El administrador revisó el caso y levanta la marca de la cuenta."""
    if not usuario_objetivo.marcado_revision:
        return False
    usuario_objetivo.marcado_revision = False
    usuario_objetivo.motivo_revision = ''
    notificacion = notificaciones_service.crear(
        usuario_objetivo, 'revision_levantada', 'Tu cuenta ya no está en revisión',
        'Un administrador revisó tu cuenta. Ya puedes volver a reclamar objetos.',
    )
    db.session.commit()
    notificaciones_service.enviar_correos([notificacion])
    return True
