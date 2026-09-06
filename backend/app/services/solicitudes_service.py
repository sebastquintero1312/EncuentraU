# Reglas de negocio del proceso de reclamación (solicitudes).
#
# Ver skill objetos-perdidos, sección 6 "Solicitudes de reclamación":
# - Un usuario no puede reclamar su propio reporte.
# - Solo puede haber una solicitud abierta (pendiente/en_revision) por
#   objeto por usuario.
# - Aprobar una solicitud marca el objeto como 'resuelto' y rechaza
#   automáticamente las demás solicitudes abiertas sobre el mismo objeto.
# - Rechazar/cancelar la única solicitud abierta regresa el objeto a 'activo'.

from app.extensions import db
from app.models.objeto import Objeto
from app.models.solicitud import Solicitud, ESTADOS_ABIERTOS

LONGITUD_MIN_MENSAJE = 15
LONGITUD_MAX_MENSAJE = 400
LONGITUD_MIN_CONTACTO = 5
LONGITUD_MAX_CONTACTO = 150


def _texto(valor):
    return (valor or '').strip() if isinstance(valor, str) else ''


def crear_solicitud(objeto_id, solicitante, contacto, mensaje):
    """Devuelve (errores: dict, solicitud | None)."""
    errores = {}
    contacto = _texto(contacto)
    mensaje = _texto(mensaje)

    if not (LONGITUD_MIN_CONTACTO <= len(contacto) <= LONGITUD_MAX_CONTACTO):
        errores['contacto'] = f'El contacto debe tener entre {LONGITUD_MIN_CONTACTO} y {LONGITUD_MAX_CONTACTO} caracteres'
    if not (LONGITUD_MIN_MENSAJE <= len(mensaje) <= LONGITUD_MAX_MENSAJE):
        errores['mensaje'] = f'El mensaje debe tener entre {LONGITUD_MIN_MENSAJE} y {LONGITUD_MAX_MENSAJE} caracteres'

    objeto = db.session.get(Objeto, objeto_id)
    if not objeto:
        return {'objeto_id': 'El reporte no existe'}, None
    if objeto.estado not in ('activo', 'en_proceso'):
        return {'objeto_id': 'Este reporte ya no admite solicitudes'}, None
    if objeto.usuario_id == solicitante.id:
        return {'objeto_id': 'No puedes reclamar tu propio reporte'}, None

    ya_existe = Solicitud.query.filter(
        Solicitud.objeto_id == objeto_id,
        Solicitud.solicitante_id == solicitante.id,
        Solicitud.estado.in_(ESTADOS_ABIERTOS),
    ).first()
    if ya_existe:
        return {'objeto_id': 'Ya tienes una solicitud abierta para este reporte'}, None

    if errores:
        return errores, None

    solicitud = Solicitud(
        objeto_id=objeto_id,
        solicitante_id=solicitante.id,
        contacto=contacto,
        mensaje=mensaje,
        estado='pendiente',
    )
    db.session.add(solicitud)
    if objeto.estado == 'activo':
        objeto.estado = 'en_proceso'
    db.session.commit()
    return {}, solicitud


def revisar_solicitud(solicitud, nuevo_estado, respuesta_admin=None):
    if nuevo_estado not in ('aprobada', 'rechazada'):
        return False, 'Estado inválido: solo se puede aprobar o rechazar'
    if solicitud.estado not in ESTADOS_ABIERTOS:
        return False, 'Esta solicitud ya fue resuelta'

    objeto = solicitud.objeto
    solicitud.estado = nuevo_estado
    solicitud.respuesta_admin = _texto(respuesta_admin) or None

    if nuevo_estado == 'aprobada':
        objeto.estado = 'resuelto'
        # Las demás solicitudes abiertas sobre el mismo objeto quedan rechazadas.
        otras = Solicitud.query.filter(
            Solicitud.objeto_id == objeto.id,
            Solicitud.id != solicitud.id,
            Solicitud.estado.in_(ESTADOS_ABIERTOS),
        ).all()
        for otra in otras:
            otra.estado = 'rechazada'
            otra.respuesta_admin = 'Rechazada automáticamente: otra solicitud fue aprobada para este objeto'
    else:
        _reabrir_objeto_si_no_hay_mas_abiertas(objeto)

    db.session.commit()
    return True, None


def cancelar_solicitud(solicitud):
    if solicitud.estado not in ESTADOS_ABIERTOS:
        return False
    solicitud.estado = 'cancelada'
    _reabrir_objeto_si_no_hay_mas_abiertas(solicitud.objeto)
    db.session.commit()
    return True


def _reabrir_objeto_si_no_hay_mas_abiertas(objeto):
    if objeto.estado != 'en_proceso':
        return
    quedan_abiertas = Solicitud.query.filter(
        Solicitud.objeto_id == objeto.id,
        Solicitud.estado.in_(ESTADOS_ABIERTOS),
    ).count()
    if quedan_abiertas == 0:
        objeto.estado = 'activo'
