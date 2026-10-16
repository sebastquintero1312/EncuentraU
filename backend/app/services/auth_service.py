# Reglas de negocio de autenticación: validar y guardar contraseñas, validar
# correos institucionales.
#
# IMPORTANTE: esta es la validación DEFINITIVA. El frontend valida solo
# para dar una buena experiencia al usuario, pero nunca hay que confiar
# en lo que llega del navegador: aquí se repite todo.

import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from flask import current_app

LONGITUD_MINIMA = 12
LONGITUD_MAXIMA = 128  # evita hashear textos gigantes a propósito (abuso de CPU)

_hasher = PasswordHasher()

# Lista corta de contraseñas comunes a bloquear (se puede ampliar más adelante)
CONTRASENAS_COMUNES = {
    '12345678', '123456789', '1234567890', 'password', 'password123',
    'qwerty', 'qwerty123', 'admin123', 'contrasena', 'contraseña123',
    '11111111', '00000000', 'abc12345',
}

PATRON_MAYUSCULA = re.compile(r'[A-Z]')
PATRON_MINUSCULA = re.compile(r'[a-z]')
PATRON_NUMERO = re.compile(r'[0-9]')
PATRON_ESPECIAL = re.compile(r'[!@#$%^&*()_\-+=]')
PATRON_CORREO = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def validar_contrasena(password, correo='', nombre=''):
    """Devuelve una lista de errores. Lista vacía = contraseña válida."""
    errores = []
    if not isinstance(password, str):
        password = ''

    if len(password) < LONGITUD_MINIMA:
        errores.append(f'La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres')
    if len(password) > LONGITUD_MAXIMA:
        errores.append(f'La contraseña no puede tener más de {LONGITUD_MAXIMA} caracteres')
    if not PATRON_MAYUSCULA.search(password):
        errores.append('Debe incluir al menos una letra mayúscula')
    if not PATRON_MINUSCULA.search(password):
        errores.append('Debe incluir al menos una letra minúscula')
    if not PATRON_NUMERO.search(password):
        errores.append('Debe incluir al menos un número')
    if not PATRON_ESPECIAL.search(password):
        errores.append('Debe incluir al menos un carácter especial (! @ # $ % ^ & * ( ) _ - + =)')
    if password and password.lower() in CONTRASENAS_COMUNES:
        errores.append('Esta contraseña es demasiado común, elige otra')

    # No debe contener el usuario ni el nombre de la persona
    if password:
        password_min = password.lower()
        if correo:
            parte_correo = correo.split('@')[0].lower()
            if len(parte_correo) >= 4 and parte_correo in password_min:
                errores.append('La contraseña no debe contener tu correo')
        if nombre and len(nombre) >= 4 and nombre.lower() in password_min:
            errores.append('La contraseña no debe contener tu nombre')

    return errores


def correo_valido(correo):
    return isinstance(correo, str) and len(correo) <= 255 and bool(PATRON_CORREO.match(correo))


def correo_institucional(correo):
    """Solo se aceptan correos del dominio de la universidad
    (DOMINIO_CORREO_INSTITUCIONAL, por defecto sanmateo.edu.co)."""
    dominio = current_app.config['DOMINIO_CORREO_INSTITUCIONAL']
    return correo_valido(correo) and correo.lower().endswith('@' + dominio)


def crear_hash(password):
    # Argon2id (parámetros por defecto de argon2-cffi: seguros para 2026,
    # ganador del Password Hashing Competition, recomendado sobre scrypt/bcrypt).
    return _hasher.hash(password)


def verificar_password(password, password_hash):
    if not isinstance(password, str) or len(password) > LONGITUD_MAXIMA:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
