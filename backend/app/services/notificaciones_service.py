# Notificaciones: dentro de la aplicación y, opcionalmente, por correo.
#
# Patrón en dos pasos para respetar la atomicidad (ACID):
#   1. crear(...) agrega la notificación a la MISMA transacción del cambio
#      que la provoca. Si ese cambio falla y se deshace, la notificación
#      también desaparece: nunca se avisa de algo que no ocurrió.
#   2. Después del commit, enviar_correos(...) envía los correos. Un correo
#      no se puede "deshacer", por eso se envía solo cuando el cambio ya es
#      definitivo.

from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.notificacion import Notificacion
from app.models.usuario import usuarios_activos_con_rol
from app.services.correo_service import enviar_correo, pie_de_correo


def crear(usuario, tipo, titulo, mensaje, enlace='', correo=True):
    notificacion = Notificacion(
        usuario_id=usuario.id,
        tipo=tipo,
        titulo=titulo[:120],
        mensaje=mensaje[:500],
        enlace=enlace,
    )
    # Atributo temporal (no es una columna): indica si hay que mandar correo.
    notificacion.enviar_por_correo = correo
    db.session.add(notificacion)
    return notificacion


def crear_para_rol(rol, tipo, titulo, mensaje, enlace='', correo=False):
    return [crear(u, tipo, titulo, mensaje, enlace, correo) for u in usuarios_activos_con_rol(rol)]


def enviar_correos(notificaciones):
    """Llamar SOLO después de db.session.commit()."""
    url_publica = current_app.config['URL_PUBLICA']
    enviadas = False
    for notificacion in notificaciones:
        if not getattr(notificacion, 'enviar_por_correo', False):
            continue
        usuario = notificacion.usuario
        if usuario is None or not usuario.activo:
            continue
        texto = f'Hola {usuario.primer_nombre},\n\n{notificacion.mensaje}'
        if notificacion.enlace:
            texto += f'\n\nVer en EncuentraU: {url_publica}/{notificacion.enlace}'
        texto += pie_de_correo()
        if enviar_correo(usuario.correo, usuario.nombre_completo, f'EncuentraU: {notificacion.titulo}', texto):
            notificacion.correo_enviado_en = datetime.now(timezone.utc)
            enviadas = True
    if enviadas:
        db.session.commit()


def listar(usuario, solo_no_leidas, limite=50):
    query = Notificacion.query.filter(Notificacion.usuario_id == usuario.id)
    if solo_no_leidas:
        query = query.filter(Notificacion.leida_en.is_(None))
    return query.order_by(Notificacion.created_at.desc(), Notificacion.id.desc()).limit(limite).all()


def contar_no_leidas(usuario):
    return Notificacion.query.filter(
        Notificacion.usuario_id == usuario.id, Notificacion.leida_en.is_(None),
    ).count()


def marcar_leida(usuario, notificacion_id):
    """Devuelve False si no existe o no es del usuario (IDOR)."""
    notificacion = db.session.get(Notificacion, notificacion_id)
    if notificacion is None or notificacion.usuario_id != usuario.id:
        return False
    if notificacion.leida_en is None:
        notificacion.leida_en = datetime.now(timezone.utc)
        db.session.commit()
    return True


def marcar_todas_leidas(usuario):
    Notificacion.query.filter(
        Notificacion.usuario_id == usuario.id, Notificacion.leida_en.is_(None),
    ).update({Notificacion.leida_en: datetime.now(timezone.utc)}, synchronize_session=False)
    db.session.commit()
