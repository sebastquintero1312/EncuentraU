# Operaciones del ENCARGADO de la oficina de objetos perdidos: recibir
# objetos, revisar reclamaciones, entregar y cerrar casos.
#
# Las operaciones que tocan varias tablas se delegan a procedimientos
# almacenados de PostgreSQL (models/procedimientos.py), que bloquean las
# filas con SELECT ... FOR UPDATE: aunque dos encargados actúen sobre el
# mismo objeto al mismo tiempo, el resultado es siempre consistente.
#
# Patrón de cada operación:
#   1. validar la forma de los datos (aquí)
#   2. llamar al procedimiento (reglas + cambios, en la base de datos)
#   3. crear las notificaciones en la misma transacción
#   4. commit
#   5. enviar los correos (solo después del commit)

from app.config.config import ZONA_HORARIA_COLOMBIA
from app.extensions import db
from app.models import procedimientos
from app.models.catalogo import valor_parametro
from app.models.entrega import Entrega
from app.models.objeto import Objeto
from app.models.solicitud import Solicitud
from app.models.usuario import ROL_ADMINISTRADOR, buscar_por_id
from app.seguridad import codigo_retiro_con_formato_valido, hash_codigo_retiro
from app.services import coincidencias_service, notificaciones_service
from app.utils import texto

LONGITUD_MAX_OBSERVACIONES = 500
LONGITUD_MAX_RESPUESTA = 300
LONGITUD_MIN_MOTIVO = 5
LONGITUD_MAX_MOTIVO = 300
LONGITUD_MIN_PRUEBA = 5
LONGITUD_MAX_PRUEBA = 300


def vencer_reservas():
    """Libera los objetos cuyas reservas vencieron y avisa a cada estudiante.
    Se ejecuta al entrar a las pantallas de la oficina y de reclamaciones
    (también existe el comando "flask vencer-reservas" para programarlo)."""
    vencidas = procedimientos.vencer_reservas()
    if not vencidas:
        return 0
    notificaciones = []
    for fila in vencidas:
        estudiante = buscar_por_id(fila['solicitante_id'])
        objeto = db.session.get(Objeto, fila['objeto_id'])
        notificaciones.append(notificaciones_service.crear(
            estudiante, 'reserva_vencida', 'Venció el plazo de retiro',
            f'Pasó el plazo para retirar "{objeto.nombre}" y la reserva se liberó. '
            'Si todavía crees que es tuyo, comunícate con la oficina.',
            'mis-reclamaciones.html',
        ))
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return len(vencidas)


def _solicitantes_pendientes(objeto_id):
    return [s.solicitante for s in Solicitud.query.filter(
        Solicitud.objeto_id == objeto_id, Solicitud.estado == 'pendiente',
    ).all()]


def recibir_objeto(encargado, objeto_id, observaciones):
    """Devuelve (objeto, mensaje_error)."""
    observaciones = texto(observaciones)
    if len(observaciones) > LONGITUD_MAX_OBSERVACIONES:
        return None, f'Las observaciones admiten máximo {LONGITUD_MAX_OBSERVACIONES} caracteres'

    procedimientos.registrar_recepcion(objeto_id, encargado.id, observaciones)
    objeto = db.session.get(Objeto, objeto_id, populate_existing=True)

    notificaciones = [notificaciones_service.crear(
        objeto.usuario, 'objeto_recibido', 'Recibimos el objeto que encontraste',
        f'La oficina recibió "{objeto.nombre}". Gracias por entregarlo: ya está disponible para que su dueño lo reclame.',
        'mis-reportes.html',
    )]
    # Aviso a los estudiantes con un reporte de pérdida parecido (solo datos públicos)
    for dueno in coincidencias_service.duenos_a_avisar(objeto):
        notificaciones.append(notificaciones_service.crear(
            dueno, 'posible_coincidencia', 'Llegó un objeto que podría ser tuyo',
            f'Llegó a la oficina "{objeto.nombre}" ({objeto.categoria.nombre}), encontrado en '
            f'{objeto.ubicacion.nombre} el {objeto.fecha_evento.isoformat()}. Si es tuyo, reclámalo desde EncuentraU.',
            f'detalle-objeto.html?id={objeto.id}',
        ))
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return objeto, None


def preaprobar(encargado, solicitud_id, respuesta):
    """Devuelve (solicitud, mensaje_error)."""
    respuesta = texto(respuesta)
    if len(respuesta) > LONGITUD_MAX_RESPUESTA:
        return None, f'La respuesta admite máximo {LONGITUD_MAX_RESPUESTA} caracteres'

    procedimientos.preaprobar_solicitud(solicitud_id, encargado.id, respuesta)
    solicitud = db.session.get(Solicitud, solicitud_id, populate_existing=True)
    db.session.refresh(solicitud.objeto)

    vence = solicitud.vence_en.astimezone(ZONA_HORARIA_COLOMBIA).strftime('%d/%m/%Y %I:%M %p')
    notificaciones = [notificaciones_service.crear(
        solicitud.solicitante, 'reclamacion_preaprobada', 'Tu reclamación fue pre-aprobada',
        f'La descripción que diste de "{solicitud.objeto.nombre}" coincide. Para retirarlo: '
        f'1) entra a "Mis reclamaciones" y genera tu código de retiro; 2) ve a la oficina con tu carné '
        f'antes del {vence} y lleva una prueba de que es tuyo (por ejemplo, desbloquearlo o una factura).',
        'mis-reclamaciones.html',
    )]
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return solicitud, None


def rechazar(encargado, solicitud_id, motivo):
    """Devuelve (solicitud, mensaje_error)."""
    motivo = texto(motivo)
    if not (LONGITUD_MIN_MOTIVO <= len(motivo) <= LONGITUD_MAX_MOTIVO):
        return None, f'Escribe el motivo del rechazo (entre {LONGITUD_MIN_MOTIVO} y {LONGITUD_MAX_MOTIVO} caracteres)'

    solicitud = db.session.get(Solicitud, solicitud_id)
    if solicitud is None:
        return None, 'La reclamación no existe'
    estaba_marcado = solicitud.solicitante.marcado_revision

    procedimientos.rechazar_solicitud(solicitud_id, encargado.id, motivo)
    solicitud = db.session.get(Solicitud, solicitud_id, populate_existing=True)
    db.session.refresh(solicitud.solicitante)  # el trigger pudo marcar la cuenta
    db.session.refresh(solicitud.objeto)

    notificaciones = [notificaciones_service.crear(
        solicitud.solicitante, 'reclamacion_rechazada', 'Tu reclamación fue rechazada',
        f'No fue posible verificar que "{solicitud.objeto.nombre}" sea tuyo. Motivo: {motivo}',
        'mis-reclamaciones.html',
    )]
    if solicitud.solicitante.marcado_revision and not estaba_marcado:
        notificaciones += notificaciones_service.crear_para_rol(
            ROL_ADMINISTRADOR, 'cuenta_en_revision', 'Cuenta marcada para revisión',
            f'La cuenta de {solicitud.solicitante.nombre_completo} ({solicitud.solicitante.correo}) quedó en revisión: '
            f'{solicitud.solicitante.motivo_revision}.',
            'admin-usuarios.html', correo=True,
        )
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return solicitud, None


def entregar(encargado, objeto_id, datos):
    """Entrega presencial. Devuelve (ok, mensaje, entrega)."""
    codigo = texto(datos.get('codigo'))
    carne_verificado = datos.get('carne_verificado') is True
    prueba = texto(datos.get('prueba_propiedad'))
    observaciones = texto(datos.get('observaciones'))

    if not codigo_retiro_con_formato_valido(codigo):
        return False, 'El código de retiro tiene 6 dígitos', None
    if not carne_verificado:
        return False, 'Debes verificar el carné del estudiante antes de entregar el objeto', None
    if not (LONGITUD_MIN_PRUEBA <= len(prueba) <= LONGITUD_MAX_PRUEBA):
        return False, (f'Describe la prueba de propiedad que presentó el estudiante (entre '
                       f'{LONGITUD_MIN_PRUEBA} y {LONGITUD_MAX_PRUEBA} caracteres)'), None
    if len(observaciones) > LONGITUD_MAX_RESPUESTA:
        return False, f'Las observaciones admiten máximo {LONGITUD_MAX_RESPUESTA} caracteres', None

    objeto = db.session.get(Objeto, objeto_id)
    if objeto is None:
        return False, 'El objeto no existe', None
    preaprobada = Solicitud.query.filter(
        Solicitud.objeto_id == objeto_id, Solicitud.estado == 'preaprobada',
    ).first()
    otros_pendientes = _solicitantes_pendientes(objeto_id)

    resultado = procedimientos.registrar_entrega(
        objeto_id, encargado.id, hash_codigo_retiro(codigo), carne_verificado, prueba, observaciones,
    )
    # El procedimiento cambió filas por fuera del ORM: se releen.
    db.session.refresh(objeto)
    solicitud = db.session.get(Solicitud, preaprobada.id, populate_existing=True) if preaprobada else None

    if resultado == 'entregado':
        entrega = Entrega.query.filter(Entrega.objeto_id == objeto_id).one()
        notificaciones = [
            notificaciones_service.crear(
                solicitud.solicitante, 'objeto_entregado', 'Retiraste tu objeto',
                f'Se registró la entrega de "{objeto.nombre}" a tu nombre. Si NO fuiste tú quien lo retiró, '
                'comunícate de inmediato con la oficina.',
                'mis-reclamaciones.html',
            ),
            notificaciones_service.crear(
                objeto.usuario, 'objeto_devuelto', 'El objeto que encontraste volvió a su dueño',
                f'"{objeto.nombre}" fue entregado a su dueño después de verificar su propiedad. ¡Gracias por tu ayuda!',
                'mis-reportes.html',
            ),
        ]
        for otro in otros_pendientes:
            notificaciones.append(notificaciones_service.crear(
                otro, 'reclamacion_descartada', 'Tu reclamación se cerró',
                f'"{objeto.nombre}" fue entregado a otra persona después de verificar su propiedad.',
                'mis-reclamaciones.html',
            ))
        db.session.commit()
        notificaciones_service.enviar_correos(notificaciones)
        return True, 'Entrega registrada correctamente', entrega

    # Los demás resultados también se confirman: el intento fallido o el
    # vencimiento deben quedar guardados.
    notificaciones = []
    if resultado == 'codigo_incorrecto':
        restantes = valor_parametro('max_intentos_codigo') - solicitud.intentos_codigo
        mensaje = f'El código no es correcto. Quedan {restantes} intentos antes de invalidarlo.'
    elif resultado == 'codigo_bloqueado':
        mensaje = ('Se agotaron los intentos y el código quedó invalidado. '
                   'El estudiante debe generar uno nuevo desde "Mis reclamaciones".')
        notificaciones.append(notificaciones_service.crear(
            solicitud.solicitante, 'codigo_invalidado', 'Tu código de retiro se invalidó',
            f'Se ingresó un código incorrecto varias veces al intentar retirar "{objeto.nombre}". '
            'Por seguridad lo invalidamos: genera uno nuevo desde "Mis reclamaciones". '
            'Si no estabas intentando retirarlo, avisa a la oficina.',
            'mis-reclamaciones.html',
        ))
    elif resultado == 'sin_codigo':
        mensaje = 'El estudiante todavía no ha generado su código de retiro. Pídele que lo genere desde "Mis reclamaciones".'
    elif resultado == 'vencida':
        mensaje = 'El plazo de retiro ya venció: la reserva se liberó y el objeto volvió a estar disponible.'
        notificaciones.append(notificaciones_service.crear(
            solicitud.solicitante, 'reserva_vencida', 'Venció el plazo de retiro',
            f'Pasó el plazo para retirar "{objeto.nombre}" y la reserva se liberó.',
            'mis-reclamaciones.html',
        ))
    else:
        mensaje = 'No fue posible registrar la entrega'
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return False, mensaje, None


def cerrar_objeto(encargado, objeto_id, motivo):
    """Devuelve (objeto, mensaje_error)."""
    motivo = texto(motivo)
    if not (LONGITUD_MIN_MOTIVO <= len(motivo) <= LONGITUD_MAX_MOTIVO):
        return None, f'Escribe el motivo del cierre (entre {LONGITUD_MIN_MOTIVO} y {LONGITUD_MAX_MOTIVO} caracteres)'
    if db.session.get(Objeto, objeto_id) is None:
        return None, 'El objeto no existe'
    pendientes = _solicitantes_pendientes(objeto_id)

    procedimientos.cerrar_objeto(objeto_id, encargado.id, motivo)
    objeto = db.session.get(Objeto, objeto_id, populate_existing=True)

    notificaciones = [notificaciones_service.crear(
        objeto.usuario, 'reporte_cerrado', 'La oficina cerró tu reporte',
        f'Tu reporte "{objeto.nombre}" fue cerrado. Motivo: {motivo}',
        'mis-reportes.html',
    )]
    for estudiante in pendientes:
        notificaciones.append(notificaciones_service.crear(
            estudiante, 'reclamacion_descartada', 'Tu reclamación se cerró',
            f'La oficina cerró el caso de "{objeto.nombre}". Motivo: {motivo}',
            'mis-reclamaciones.html',
        ))
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return objeto, None


def listar_solicitudes(estado, pagina, por_pagina):
    query = Solicitud.query
    if estado:
        query = query.filter(Solicitud.estado == estado)
    # Las más antiguas primero: se atienden en orden de llegada.
    query = query.order_by(Solicitud.created_at.asc(), Solicitud.id.asc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def detalle_objeto(objeto):
    """Todo lo que el encargado necesita para decidir sobre un objeto."""
    solicitudes = Solicitud.query.filter(Solicitud.objeto_id == objeto.id).order_by(Solicitud.created_at.asc()).all()
    entrega = Entrega.query.filter(Entrega.objeto_id == objeto.id).first()
    if objeto.tipo == 'encontrado':
        coincidencias = coincidencias_service.perdidos_para_encontrado(objeto)
    else:
        coincidencias = coincidencias_service.encontrados_para_perdido(objeto)
    return {
        'objeto': objeto.vista_oficina(),
        'solicitudes': [s.vista_oficina() for s in solicitudes],
        'entrega': entrega.a_dict() if entrega else None,
        'coincidencias': [dict(o.vista_oficina(), puntaje=p) for o, p in coincidencias],
    }
