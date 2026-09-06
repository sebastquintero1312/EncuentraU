"""Pruebas de seguridad: CSRF y rate limiting.

Estas pruebas activan explícitamente lo que conftest.py desactiva por
defecto para el resto de la suite (CSRF y rate limiting), porque son
justamente lo que están verificando.

Nota sobre RATELIMIT_ENABLED: a diferencia de WTF_CSRF_ENABLED (que
Flask-WTF sí lee dinámicamente de app.config en cada petición), Flask-
Limiter fija su estado "enabled" en el momento de `limiter.init_app(app)`
— cambiar app.config['RATELIMIT_ENABLED'] DESPUÉS de crear la app no tiene
ningún efecto real (confirmado empíricamente durante la revisión final de
v1.0; ver el comentario equivalente sobre SQLALCHEMY_DATABASE_URI en
app/__init__.py). Por eso las pruebas de rate limiting crean su propia app
con `config_overrides` en vez de reusar el fixture `app` compartido.
"""

import json
import os
import tempfile

from app import create_app
from app.extensions import db as _db


def test_csrf_requerido_en_registro(app):
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    respuesta = client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'sincsrf@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    assert respuesta.status_code == 400
    assert 'CSRF' in respuesta.get_json()['mensaje']


def test_csrf_token_valido_permite_la_peticion(app):
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    token = client.get('/api/auth/csrf-token').get_json()['csrf_token']
    respuesta = client.post(
        '/api/auth/registro',
        data=json.dumps({
            'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
            'correo': 'concsrf@sanmateo.edu.co',
            'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
        }),
        headers={'Content-Type': 'application/json', 'X-CSRFToken': token},
    )
    assert respuesta.status_code == 201


def test_csrf_error_devuelve_400_no_500(app):
    """Regresión: un CSRFError sin manejador específico caía en el handler
    genérico de Exception y se devolvía como 500 en vez de 400 (bug
    encontrado y corregido durante la migración a v1.0, ver CHANGELOG)."""
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    respuesta = client.post('/api/auth/registro', json={'correo': 'x@x.com'})
    assert respuesta.status_code == 400
    assert respuesta.status_code != 500


def _app_con_rate_limit_activo():
    fd, ruta_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    aplicacion = create_app(config_overrides={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta_db}',
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': True,
    })
    return aplicacion, ruta_db


def test_rate_limit_registro():
    aplicacion, ruta_db = _app_con_rate_limit_activo()
    with aplicacion.app_context():
        _db.create_all()
        client = aplicacion.test_client()
        ultima = None
        for i in range(7):
            ultima = client.post('/api/auth/registro', json={
                'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
                'correo': f'rl{i}@sanmateo.edu.co',
                'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
            })
        assert ultima.status_code == 429
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()
    os.remove(ruta_db)


def test_rate_limit_login():
    aplicacion, ruta_db = _app_con_rate_limit_activo()
    with aplicacion.app_context():
        _db.create_all()
        client = aplicacion.test_client()
        ultima = None
        for _ in range(12):
            ultima = client.post('/api/auth/login', json={
                'correo': 'no.existe@sanmateo.edu.co', 'contrasena': 'Cualquiera$123',
            })
        assert ultima.status_code == 429
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()
    os.remove(ruta_db)
