# Reclamaciones del lado del ESTUDIANTE: reclamar un objeto, ver el estado,
# cancelar y generar el código de retiro.
#
# Cómo se evita que alguien reclame algo ajeno (resumen; ver
# docs/AUTHORIZATION.md para el detalle):
#   1. Verificación a ciegas: el estudiante describe el objeto sin haber
#      visto los detalles privados; el encargado compara.
#   2. Límites: una reclamación abierta por objeto, máximo N abiertas a la
#      vez, y la cuenta queda en revisión tras N rechazos. Lo aplica la
#      base de datos (trigger), no solo Python.
#   3. Aprobar no es entregar: tras la pre-aprobación el estudiante genera
#      un código de un solo uso y debe presentarse con su carné.
#   4. Todo queda en la auditoría.

from datetime import datetime, timezone

from app.extensions import db
from app.models.catalogo import valor_parametro
from app.models.objeto import Objeto, TIPO_PERDIDO
from app.models.solicitud import ESTADOS_ABIERTOS, Solicitud
from app.models.usuario import ROL_ENCARGADO
from app import seguridad
from app.services import notificaciones_service
from app.utils import entero_o_none, texto, validar_fecha_pasada

LONGITUD_MIN_DESCRIPCION = 20
LONGITUD_MAX_DESCRIPCION = 500
LONGITUD_MIN_LUGAR = 3
LONGITUD_MAX_LUGAR = 150
LONGITUD_MAX_EVIDENCIA = 300


def _validar(datos):
    errores = {}
    limpio = {}

    descripcion = texto(datos.get('descripcion'))
    if not (LONGITUD_MIN_DESCRIPCION <= len(descripcion) <= LONGITUD_MAX_DESCRIPCION):
        errores['descripcion'] = (f'Describe el objeto con detalle: entre {LONGITUD_MIN_DESCRIPCION} '
                                  f'y {LONGITUD_MAX_DESCRIPCION} caracteres')
    limpio['descripcion'] = descripcion

    lugar = texto(datos.get('lugar_perdida'))
    if not (LONGITUD_MIN_LUGAR <= len(lugar) <= LONGITUD_MAX_LUGAR):
        errores['lugar_perdida'] = f'Indica dónde lo perdiste (entre {LONGITUD_MIN_LUGAR} y {LONGITUD_MAX_LUGAR} caracteres)'
    limpio['lugar_perdida'] = lugar

    limpio['fecha_perdida'] = validar_fecha_pasada(datos.get('fecha_perdida'), errores, 'fecha_perdida')

    evidencia = texto(datos.get('evidencia'))
    if len(evidencia) > LONGITUD_MAX_EVIDENCIA:
        errores['evidencia'] = f'Máximo {LONGITUD_MAX_EVIDENCIA} caracteres'
    limpio['evidencia'] = evidencia
    return errores, limpio


def crear_solicitud(estudiante, datos):
    """Devuelve (errores, solicitud). Las reglas se revisan aquí para dar
    mensajes claros, y la base de datos las vuelve a exigir en el trigger
    trg_solicitudes_validar_nueva (por si dos peticiones llegan a la vez)."""
    objeto = db.session.get(Objeto, entero_o_none(datos.get('objeto_id')) or 0)
    if objeto is None or not objeto.disponible_para_reclamar:
        return {'objeto_id': 'Este objeto no está disponible para reclamar'}, None
    if objeto.usuario_id == estudiante.id:
        return {'objeto_id': 'No puedes reclamar un objeto que tú mismo reportaste como encontrado'}, None
    if estudiante.marcado_revision:
        return {'cuenta': 'Tu cuenta está en revisión por reclamaciones rechazadas. Comunícate con la oficina'}, None

    abiertas = Solicitud.query.filter(
        Solicitud.solicitante_id == estudiante.id, Solicitud.estado.in_(ESTADOS_ABIERTOS),
    ).all()
    if any(s.objeto_id == objeto.id for s in abiertas):
        return {'objeto_id': 'Ya tienes una reclamación abierta para este objeto'}, None
    maximo = valor_parametro('max_solicitudes_abiertas')
    if len(abiertas) >= maximo:
        return {'cuenta': f'Ya tienes {len(abiertas)} reclamaciones abiertas, que es el máximo permitido'}, None

    errores, limpio = _validar(datos)

    reporte_perdida_id = None
    if datos.get('reporte_perdida_id') not in (None, '', 0):
        reporte = db.session.get(Objeto, entero_o_none(datos.get('reporte_perdida_id')) or 0)
        # IDOR: solo se puede vincular un reporte de pérdida PROPIO.
        if reporte is None or reporte.tipo != TIPO_PERDIDO or reporte.usuario_id != estudiante.id:
            errores['reporte_perdida_id'] = 'Selecciona uno de tus reportes de pérdida'
        else:
            reporte_perdida_id = reporte.id

    if errores:
        return errores, None

    solicitud = Solicitud(
        objeto_id=objeto.id,
        solicitante_id=estudiante.id,
        reporte_perdida_id=reporte_perdida_id,
        descripcion=limpio['descripcion'],
        lugar_perdida=limpio['lugar_perdida'],
        fecha_perdida=limpio['fecha_perdida'],
        evidencia=limpio['evidencia'],
    )
    db.session.add(solicitud)
    db.session.flush()  # aquí corre el trigger; si una regla falla, se lanza el error

    notificaciones = [notificaciones_service.crear(
        estudiante, 'reclamacion_recibida', 'Recibimos tu reclamación',
        f'Tu reclamación de "{objeto.nombre}" quedó registrada. Un encargado comparará tu descripción '
        'con los detalles del objeto y te avisaremos el resultado.',
        'mis-reclamaciones.html',
    )]
    notificaciones += notificaciones_service.crear_para_rol(
        ROL_ENCARGADO, 'reclamacion_nueva', 'Nueva reclamación por revisar',
        f'{estudiante.nombre_completo} reclamó "{objeto.nombre}".',
        'encargado-reclamaciones.html',
    )
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return {}, solicitud


def mis_solicitudes(estudiante, pagina, por_pagina):
    query = Solicitud.query.filter(Solicitud.solicitante_id == estudiante.id)
    query = query.order_by(Solicitud.created_at.desc(), Solicitud.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def _bloquear_para_modificar(solicitud):
    """Concurrencia PESIMISTA desde el ORM: SELECT ... FOR UPDATE, en el mismo
    orden que los procedimientos almacenados (primero el objeto, después la
    solicitud) para no provocar deadlocks."""
    db.session.query(Objeto).filter(Objeto.id == solicitud.objeto_id).with_for_update().populate_existing().one()
    return db.session.query(Solicitud).filter(Solicitud.id == solicitud.id).with_for_update().populate_existing().one()


def cancelar_solicitud(solicitud):
    """Devuelve True si se pudo cancelar."""
    solicitud = _bloquear_para_modificar(solicitud)
    if solicitud.estado not in ESTADOS_ABIERTOS:
        return False
    estaba_preaprobada = solicitud.estado == 'preaprobada'
    solicitud.estado = 'cancelada'
    solicitud.codigo_hash = None
    solicitud.codigo_generado_en = None
    if estaba_preaprobada and solicitud.objeto.estado == 'reservado':
        solicitud.objeto.estado = 'en_oficina'  # el objeto vuelve a estar disponible
    db.session.commit()
    return True


def generar_codigo_retiro(solicitud):
    """Genera un código NUEVO (invalida el anterior). Devuelve
    (codigo_en_claro | None, mensaje_error). El código en claro se muestra
    una sola vez: en la base de datos queda solo su HMAC."""
    solicitud = _bloquear_para_modificar(solicitud)
    if solicitud.estado != 'preaprobada':
        return None, 'Solo puedes generar un código cuando tu reclamación está pre-aprobada'
    if solicitud.vence_en is None or solicitud.vence_en < datetime.now(timezone.utc):
        return None, 'El plazo para retirar este objeto ya venció'

    codigo = seguridad.generar_codigo_retiro()
    solicitud.codigo_hash = seguridad.hash_codigo_retiro(codigo)
    solicitud.codigo_generado_en = datetime.now(timezone.utc)
    solicitud.intentos_codigo = 0
    db.session.commit()
    return codigo, None
