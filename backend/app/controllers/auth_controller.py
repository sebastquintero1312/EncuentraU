# Controladores de autenticación: leen la petición, llaman a los servicios
# y devuelven una respuesta JSON. No exponen detalles internos en los errores.

from flask import request, jsonify, session
from flask_wtf.csrf import generate_csrf

from app.models.usuario import buscar_por_correo, buscar_por_id, usuario_publico
from app.services import auth_service, cuentas_service

MENSAJE_REGISTRO = ('Revisa tu correo institucional: te enviamos un enlace para activar tu cuenta. '
                    'Si no lo ves, busca en la carpeta de spam.')
MENSAJE_GENERICO_CORREO = 'Si el correo está registrado, recibirás instrucciones para continuar.'


def _datos():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def registrar():
    errores = cuentas_service.registrar(_datos())
    if errores:
        return jsonify({'mensaje': 'No fue posible completar el registro', 'errores': errores}), 400
    # Misma respuesta exista o no la cuenta (no revela qué correos están registrados)
    return jsonify({'mensaje': MENSAJE_REGISTRO}), 201


def iniciar_sesion():
    datos = _datos()
    correo = datos.get('correo') if isinstance(datos.get('correo'), str) else ''
    password = datos.get('contrasena') if isinstance(datos.get('contrasena'), str) else ''

    # Mensaje genérico a propósito: no decimos si el correo existe o no
    mensaje_error = 'Correo o contraseña incorrectos'
    if not correo.strip() or not password:
        return jsonify({'mensaje': mensaje_error}), 401

    usuario = buscar_por_correo(correo)
    if not usuario or not usuario.activo or not auth_service.verificar_password(password, usuario.password_hash):
        return jsonify({'mensaje': mensaje_error}), 401

    # Solo quien conoce la contraseña llega a este mensaje, así que no
    # revela nada a un atacante que esté probando correos.
    if not usuario.correo_verificado:
        return jsonify({
            'mensaje': 'Antes de entrar debes confirmar tu correo con el enlace que te enviamos.',
            'codigo': 'correo_no_verificado',
        }), 403

    session.clear()
    session['usuario_id'] = usuario.id
    session.permanent = False

    # session.clear() también borra el csrf_token que vivía en la sesión
    # anterior (protección anti session-fixation). Se genera uno nuevo y se
    # devuelve al frontend para que pueda seguir haciendo peticiones
    # protegidas inmediatamente, sin tener que pedirlo de nuevo aparte.
    return jsonify({
        'mensaje': 'Sesión iniciada',
        'usuario': usuario_publico(usuario),
        'csrf_token': generate_csrf(),
    }), 200


def cerrar_sesion():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada', 'csrf_token': generate_csrf()}), 200


def sesion_actual():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'usuario': None}), 200
    usuario = buscar_por_id(usuario_id)
    if not usuario or not usuario.activo:
        session.clear()
        return jsonify({'usuario': None}), 200
    return jsonify({'usuario': usuario_publico(usuario)}), 200


def verificar_correo():
    if not cuentas_service.verificar_correo(_datos().get('token')):
        return jsonify({'mensaje': 'El enlace no es válido o ya expiró. Pide uno nuevo desde la página de inicio de sesión.'}), 400
    return jsonify({'mensaje': 'Tu correo quedó verificado. Ya puedes iniciar sesión.'}), 200


def reenviar_verificacion():
    cuentas_service.reenviar_verificacion(_datos().get('correo'))
    return jsonify({'mensaje': 'Si la cuenta existe y aún no está verificada, te enviamos un enlace nuevo.'}), 200


def solicitar_recuperacion():
    # IMPORTANTE: siempre devolvemos el mismo mensaje, exista o no el correo,
    # para no permitir que alguien detecte qué correos están registrados.
    cuentas_service.solicitar_recuperacion(_datos().get('correo'))
    return jsonify({'mensaje': MENSAJE_GENERICO_CORREO}), 200


def restablecer_contrasena():
    datos = _datos()
    ok, mensaje, errores = cuentas_service.restablecer_contrasena(
        datos.get('token'), datos.get('contrasena'), datos.get('confirmar_contrasena'),
    )
    if not ok:
        respuesta = {'mensaje': mensaje}
        if errores:
            respuesta['errores'] = errores
        return jsonify(respuesta), 400
    return jsonify({'mensaje': mensaje}), 200
