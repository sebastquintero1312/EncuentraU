# Cuentas de usuario: registro, verificación del correo institucional y
# recuperación de contraseña.
#
# Seguridad:
#   * Solo correos del dominio institucional pueden registrarse.
#   * Registrarse NO basta: hay que abrir el enlace que llega al correo.
#     Así se demuestra que la persona es dueña de ese buzón y cada
#     reclamación queda asociada a alguien identificable.
#   * Las respuestas no revelan si un correo ya está registrado (evita que
#     alguien arme una lista de correos válidos). Si el correo ya existía,
#     se le avisa al dueño por correo en vez de decirlo en pantalla.
#   * Los enlaces llevan un token de un solo uso; en la base de datos se
#     guarda solo su hash.

from datetime import datetime, timedelta, timezone

from flask import current_app

from app.extensions import db
from app.models.token_usuario import (
    PROPOSITO_RECUPERACION, PROPOSITO_VERIFICACION, buscar_token, crear_token, invalidar_tokens_pendientes,
)
from app.models.usuario import buscar_por_correo, crear_usuario
from app.seguridad import generar_token, hash_token
from app.services import auth_service
from app.services.correo_service import enviar_correo, pie_de_correo
from app.utils import texto

LONGITUD_MAXIMA_NOMBRE = 80


def _emitir_token(usuario, proposito, duracion):
    invalidar_tokens_pendientes(usuario.id, proposito)
    token = generar_token()
    crear_token(usuario.id, proposito, hash_token(token), datetime.now(timezone.utc) + duracion)
    return token


def _correo_verificacion(usuario, token):
    enlace = f"{current_app.config['URL_PUBLICA']}/verificar-correo.html?token={token}"
    horas = current_app.config['HORAS_EXPIRACION_VERIFICACION']
    enviar_correo(
        usuario.correo, usuario.nombre_completo, 'EncuentraU: confirma tu correo institucional',
        f'Hola {usuario.primer_nombre},\n\n'
        f'Para activar tu cuenta de EncuentraU abre este enlace (vence en {horas} horas):\n\n{enlace}\n\n'
        'Si no creaste esta cuenta, ignora este mensaje.' + pie_de_correo(),
    )


def validar_registro(datos):
    """Devuelve (errores, datos_limpios)."""
    limpio = {
        'primer_nombre': texto(datos.get('primer_nombre')),
        'segundo_nombre': texto(datos.get('segundo_nombre')),
        'primer_apellido': texto(datos.get('primer_apellido')),
        'segundo_apellido': texto(datos.get('segundo_apellido')),
        'correo': texto(datos.get('correo')).lower(),
    }
    password = datos.get('contrasena') if isinstance(datos.get('contrasena'), str) else ''
    confirmar = datos.get('confirmar_contrasena') if isinstance(datos.get('confirmar_contrasena'), str) else ''
    errores = {}

    for campo, etiqueta in (('primer_nombre', 'El primer nombre'), ('primer_apellido', 'El primer apellido')):
        if not limpio[campo]:
            errores[campo] = f'{etiqueta} es obligatorio'
    for campo in ('primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido'):
        if len(limpio[campo]) > LONGITUD_MAXIMA_NOMBRE:
            errores[campo] = f'Máximo {LONGITUD_MAXIMA_NOMBRE} caracteres'

    dominio = current_app.config['DOMINIO_CORREO_INSTITUCIONAL']
    if not limpio['correo']:
        errores['correo'] = 'El correo es obligatorio'
    elif not auth_service.correo_valido(limpio['correo']):
        errores['correo'] = 'El correo no tiene un formato válido'
    elif not auth_service.correo_institucional(limpio['correo']):
        errores['correo'] = f'Debes usar tu correo institucional (@{dominio})'

    if password != confirmar:
        errores['confirmar_contrasena'] = 'Las contraseñas no coinciden'
    errores_password = auth_service.validar_contrasena(password, correo=limpio['correo'], nombre=limpio['primer_nombre'])
    if errores_password:
        errores['contrasena'] = errores_password

    limpio['password'] = password
    return errores, limpio


def registrar(datos):
    """Devuelve el diccionario de errores (vacío si los datos son válidos).
    Con datos válidos, la respuesta es la misma exista o no la cuenta."""
    errores, limpio = validar_registro(datos)
    if errores:
        return errores

    # El hash se calcula SIEMPRE, exista o no la cuenta: Argon2 tarda a
    # propósito, y si solo se calculara para cuentas nuevas, el tiempo de
    # respuesta delataría qué correos ya están registrados.
    password_hash = auth_service.crear_hash(limpio['password'])

    existente = buscar_por_correo(limpio['correo'])
    if existente:
        enviar_correo(
            existente.correo, existente.nombre_completo, 'EncuentraU: intento de registro con tu correo',
            f'Hola {existente.primer_nombre},\n\n'
            'Alguien intentó crear una cuenta en EncuentraU con tu correo, pero ya tienes una. '
            'Si fuiste tú, inicia sesión o usa "¿Olvidaste tu contraseña?". Si no fuiste tú, '
            'no tienes que hacer nada: tu cuenta sigue protegida.' + pie_de_correo(),
        )
        return {}

    usuario = crear_usuario(limpio, password_hash)
    token = _emitir_token(usuario, PROPOSITO_VERIFICACION,
                          timedelta(hours=current_app.config['HORAS_EXPIRACION_VERIFICACION']))
    db.session.commit()
    _correo_verificacion(usuario, token)
    return {}


def verificar_correo(token):
    """Devuelve True si el token era válido y el correo quedó verificado."""
    token = texto(token)
    if not token or len(token) > 200:
        return False
    registro = buscar_token(hash_token(token), PROPOSITO_VERIFICACION)
    if registro is None or not registro.es_valido():
        return False
    ahora = datetime.now(timezone.utc)
    registro.usado_en = ahora
    if registro.usuario.correo_verificado_en is None:
        registro.usuario.correo_verificado_en = ahora
    db.session.commit()
    return True


def reenviar_verificacion(correo):
    """Siempre responde lo mismo (no revela si el correo existe)."""
    usuario = buscar_por_correo(texto(correo))
    if usuario and usuario.activo and not usuario.correo_verificado:
        token = _emitir_token(usuario, PROPOSITO_VERIFICACION,
                              timedelta(hours=current_app.config['HORAS_EXPIRACION_VERIFICACION']))
        db.session.commit()
        _correo_verificacion(usuario, token)


def solicitar_recuperacion(correo):
    """Siempre responde lo mismo (no revela si el correo existe)."""
    correo = texto(correo).lower()
    if not auth_service.correo_valido(correo):
        return
    usuario = buscar_por_correo(correo)
    if not usuario or not usuario.activo:
        return
    minutos = current_app.config['MINUTOS_EXPIRACION_TOKEN']
    token = _emitir_token(usuario, PROPOSITO_RECUPERACION, timedelta(minutes=minutos))
    db.session.commit()
    enlace = f"{current_app.config['URL_PUBLICA']}/restablecer-contrasena.html?token={token}"
    enviar_correo(
        usuario.correo, usuario.nombre_completo, 'EncuentraU: restablecer tu contraseña',
        f'Hola {usuario.primer_nombre},\n\n'
        f'Para crear una contraseña nueva abre este enlace (vence en {minutos} minutos y sirve una sola vez):\n\n'
        f'{enlace}\n\nSi no lo pediste, ignora este mensaje: tu contraseña actual sigue funcionando.'
        + pie_de_correo(),
    )


def restablecer_contrasena(token, password, confirmar):
    """Devuelve (ok, mensaje, errores)."""
    token = texto(token)
    if not token or len(token) > 200:
        return False, 'El enlace no es válido o expiró', None
    if not isinstance(password, str) or password != confirmar:
        return False, 'Las contraseñas no coinciden', None

    registro = buscar_token(hash_token(token), PROPOSITO_RECUPERACION)
    if registro is None or not registro.es_valido() or not registro.usuario.activo:
        return False, 'El enlace no es válido o expiró', None

    usuario = registro.usuario
    errores = auth_service.validar_contrasena(password, correo=usuario.correo, nombre=usuario.primer_nombre)
    if errores:
        # El token NO se invalida: la persona puede reintentar con una
        # contraseña válida usando el mismo enlace.
        return False, 'La contraseña no cumple los requisitos', errores

    ahora = datetime.now(timezone.utc)
    usuario.password_hash = auth_service.crear_hash(password)
    registro.usado_en = ahora
    # Recibir el enlace en el buzón también demuestra que el correo es suyo.
    if usuario.correo_verificado_en is None:
        usuario.correo_verificado_en = ahora
    db.session.commit()
    return True, 'Contraseña actualizada correctamente', None
