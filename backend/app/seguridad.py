# Utilidades criptográficas pequeñas y compartidas.
#
# Reglas: los valores secretos se generan SIEMPRE con el módulo "secrets"
# (generador criptográficamente seguro del sistema operativo), nunca con
# "random". En la base de datos se guarda solo su hash.

import hashlib
import hmac
import secrets

from flask import current_app

LONGITUD_CODIGO_RETIRO = 6


def generar_token():
    """Token largo para enlaces de correo (verificación, recuperación)."""
    return secrets.token_urlsafe(32)


def hash_token(token):
    """SHA-256 basta para un token de 32 bytes aleatorios: es imposible
    adivinarlo probando valores."""
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


def generar_codigo_retiro():
    """Código de 6 dígitos que el estudiante dicta en la oficina."""
    return f'{secrets.randbelow(10 ** LONGITUD_CODIGO_RETIRO):0{LONGITUD_CODIGO_RETIRO}d}'


def hash_codigo_retiro(codigo):
    """Un código de 6 dígitos tiene solo un millón de valores posibles: con
    un SHA-256 simple, quien robara la base de datos lo descubriría probando
    todos. Por eso se usa HMAC con la SECRET_KEY del servidor como clave:
    sin esa clave, el hash no sirve para nada. (Además, en la oficina solo
    se permiten unos pocos intentos por código.)"""
    clave = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(clave, (codigo or '').encode('utf-8'), hashlib.sha256).hexdigest()


def codigo_retiro_con_formato_valido(codigo):
    return isinstance(codigo, str) and len(codigo) == LONGITUD_CODIGO_RETIRO and codigo.isdigit()
