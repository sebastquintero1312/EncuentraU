# Controladores de autenticación: leen la petición, llaman a los servicios
# y devuelven una respuesta JSON. No exponen detalles internos en los errores.

from flask import request, jsonify, session
from flask_wtf.csrf import generate_csrf

from app.extensions import db
from app.models.usuario import crear_usuario, buscar_por_correo, buscar_por_id, usuario_publico
from app.services import auth_service
from app.services.recuperacion_service import generar_token_para_usuario, obtener_usuario_id_si_token_valido, confirmar_uso_token


def _campo_vacio(valor):
    return valor is None or str(valor).strip() == ''


def registrar():
    datos = request.get_json(silent=True) or {}

    primer_nombre = (datos.get('primer_nombre') or '').strip()
    primer_apellido = (datos.get('primer_apellido') or '').strip()
    correo = (datos.get('correo') or '').strip().lower()
    password = datos.get('contrasena') or ''
    confirmar = datos.get('confirmar_contrasena') or ''

    errores = {}

    if _campo_vacio(primer_nombre):
        errores['primer_nombre'] = 'El primer nombre es obligatorio'
    if _campo_vacio(primer_apellido):
        errores['primer_apellido'] = 'El primer apellido es obligatorio'
    if _campo_vacio(correo):
        errores['correo'] = 'El correo es obligatorio'
    elif not auth_service.correo_valido(correo):
        errores['correo'] = 'El correo no tiene un formato válido'
    elif buscar_por_correo(correo):
        errores['correo'] = 'Este correo ya está registrado'

    if password != confirmar:
        errores['confirmar_contrasena'] = 'Las contraseñas no coinciden'

    errores_password = auth_service.validar_contrasena(password, correo=correo, nombre=primer_nombre)
    if errores_password:
        errores['contrasena'] = errores_password

    if errores:
        return jsonify({'mensaje': 'No fue posible completar el registro', 'errores': errores}), 400

    password_hash = auth_service.crear_hash(password)
    usuario = crear_usuario(datos, password_hash)

    return jsonify({'mensaje': 'Cuenta creada correctamente', 'usuario': usuario_publico(usuario)}), 201


def iniciar_sesion():
    datos = request.get_json(silent=True) or {}
    correo = (datos.get('correo') or '').strip().lower()
    password = datos.get('contrasena') or ''

    # Mensaje genérico a propósito: no decimos si el correo existe o no
    mensaje_error = 'Correo o contraseña incorrectos'

    if _campo_vacio(correo) or _campo_vacio(password):
        return jsonify({'mensaje': mensaje_error}), 401

    usuario = buscar_por_correo(correo)
    if not usuario or not usuario.activo or not auth_service.verificar_password(password, usuario.password_hash):
        return jsonify({'mensaje': mensaje_error}), 401

    session.clear()
    session['usuario_id'] = usuario.id
    session.permanent = False

    # session.clear() también borra el csrf_token que vivía en la sesión
    # anterior (protección anti session-fixation). Se genera uno nuevo y se
    # devuelve al frontend para que pueda seguir haciendo peticiones
    # protegidas inmediatamente, sin tener que pedirlo de nuevo aparte.
    nuevo_csrf_token = generate_csrf()

    return jsonify({
        'mensaje': 'Sesión iniciada',
        'usuario': usuario_publico(usuario),
        'csrf_token': nuevo_csrf_token,
    }), 200


def cerrar_sesion():
    session.clear()
    nuevo_csrf_token = generate_csrf()
    return jsonify({'mensaje': 'Sesión cerrada', 'csrf_token': nuevo_csrf_token}), 200


def sesion_actual():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'usuario': None}), 200
    usuario = buscar_por_id(usuario_id)
    if not usuario or not usuario.activo:
        session.clear()
        return jsonify({'usuario': None}), 200
    return jsonify({'usuario': usuario_publico(usuario)}), 200


def solicitar_recuperacion():
    datos = request.get_json(silent=True) or {}
    correo = (datos.get('correo') or '').strip().lower()

    # IMPORTANTE: siempre devolvemos el mismo mensaje, exista o no el correo,
    # para no permitir que alguien detecte qué correos están registrados.
    mensaje_generico = {'mensaje': 'Si el correo está registrado, recibirás instrucciones para continuar.'}

    if _campo_vacio(correo) or not auth_service.correo_valido(correo):
        return jsonify(mensaje_generico), 200

    usuario = buscar_por_correo(correo)
    if usuario and usuario.activo:
        token = generar_token_para_usuario(usuario.id)
        # Todavía no hay envío de correo real (fase futura).
        # Por ahora solo lo dejamos en el log del servidor para poder probar el flujo.
        print(f'[EncuentraU] Token de recuperación para {correo}: {token}')

    return jsonify(mensaje_generico), 200


def restablecer_contrasena():
    datos = request.get_json(silent=True) or {}
    token = datos.get('token') or ''
    password = datos.get('contrasena') or ''
    confirmar = datos.get('confirmar_contrasena') or ''

    if _campo_vacio(token):
        return jsonify({'mensaje': 'El enlace no es válido o expiró'}), 400

    if password != confirmar:
        return jsonify({'mensaje': 'Las contraseñas no coinciden'}), 400

    usuario_id, registro = obtener_usuario_id_si_token_valido(token)
    if usuario_id is None:
        return jsonify({'mensaje': 'El enlace no es válido o expiró'}), 400

    usuario = buscar_por_id(usuario_id)
    if not usuario:
        return jsonify({'mensaje': 'El enlace no es válido o expiró'}), 400

    errores_password = auth_service.validar_contrasena(password, correo=usuario.correo, nombre=usuario.primer_nombre)
    if errores_password:
        # El token NO se invalida aquí: la persona debe poder reintentar
        # con una contraseña válida usando el mismo enlace.
        return jsonify({'mensaje': 'La contraseña no cumple los requisitos', 'errores': errores_password}), 400

    usuario.password_hash = auth_service.crear_hash(password)
    db.session.commit()
    confirmar_uso_token(registro)

    return jsonify({'mensaje': 'Contraseña actualizada correctamente'}), 200
