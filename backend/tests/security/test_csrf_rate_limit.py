"""Pruebas de seguridad: CSRF y rate limiting.

Estas pruebas activan explícitamente lo que conftest.py desactiva por
defecto para el resto de la suite (CSRF y rate limiting), porque son
justamente lo que están verificando.
"""

import json


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


def test_rate_limit_registro(app):
    app.config['RATELIMIT_ENABLED'] = True
    client = app.test_client()
    ultima = None
    for i in range(7):
        ultima = client.post('/api/auth/registro', json={
            'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
            'correo': f'rl{i}@sanmateo.edu.co',
            'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
        })
    assert ultima.status_code == 429


def test_rate_limit_login(app):
    app.config['RATELIMIT_ENABLED'] = True
    client = app.test_client()
    ultima = None
    for _ in range(12):
        ultima = client.post('/api/auth/login', json={
            'correo': 'no.existe@sanmateo.edu.co', 'contrasena': 'Cualquiera$123',
        })
    assert ultima.status_code == 429
