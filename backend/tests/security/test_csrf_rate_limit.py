"""Pruebas de seguridad: CSRF y rate limiting.

Estas pruebas activan explícitamente lo que conftest.py desactiva por
defecto para el resto de la suite (CSRF y rate limiting), porque son
justamente lo que están verificando.

Nota sobre RATELIMIT_ENABLED: a diferencia de WTF_CSRF_ENABLED (que
Flask-WTF sí lee dinámicamente de app.config en cada petición), Flask-
Limiter fija su estado "enabled" en el momento de `limiter.init_app(app)`
— cambiar app.config['RATELIMIT_ENABLED'] DESPUÉS de crear la app no tiene
ningún efecto real (confirmado empíricamente durante la revisión final de
v1.0). Por eso las pruebas de rate limiting crean su propia app con
`config_overrides` en vez de reusar el fixture `app` compartido.
"""

import json
from contextlib import contextmanager

from app import create_app
from app.extensions import db as _db
from tests.ayudantes import CONTRASENA

DATOS_REGISTRO = {
    'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
    'contrasena': CONTRASENA, 'confirmar_contrasena': CONTRASENA,
}


def test_csrf_requerido_en_registro(app):
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    respuesta = client.post('/api/auth/registro', json=dict(DATOS_REGISTRO, correo='sincsrf@sanmateo.edu.co'))
    assert respuesta.status_code == 400
    assert 'CSRF' in respuesta.get_json()['mensaje']


def test_csrf_token_valido_permite_la_peticion(app):
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    token = client.get('/api/auth/csrf-token').get_json()['csrf_token']
    respuesta = client.post(
        '/api/auth/registro',
        data=json.dumps(dict(DATOS_REGISTRO, correo='concsrf@sanmateo.edu.co')),
        headers={'Content-Type': 'application/json', 'X-CSRFToken': token},
    )
    assert respuesta.status_code == 201


def test_csrf_tambien_protege_las_acciones_del_encargado(app, encargado):
    app.config['WTF_CSRF_ENABLED'] = True
    respuesta = encargado.post('/api/encargado/objetos/1/recepcion', json={})
    assert respuesta.status_code == 400


def test_login_regenera_la_sesion(app, estudiante_a):
    """Anti session-fixation: iniciar sesión borra la sesión anterior, así
    que el token CSRF que existía antes deja de servir y el servidor entrega
    uno nuevo."""
    from tests.ayudantes import crear_cliente
    crear_cliente(app, 'laura@sanmateo.edu.co', iniciar_sesion=False)
    app.config['WTF_CSRF_ENABLED'] = True
    cliente = app.test_client()
    token_anterior = cliente.get('/api/auth/csrf-token').get_json()['csrf_token']
    respuesta = cliente.post('/api/auth/login', json={'correo': 'laura@sanmateo.edu.co', 'contrasena': CONTRASENA},
                             headers={'X-CSRFToken': token_anterior})
    assert respuesta.status_code == 200
    token_nuevo = respuesta.get_json()['csrf_token']
    assert token_nuevo != token_anterior
    viejo = cliente.post('/api/notificaciones/leer-todas', headers={'X-CSRFToken': token_anterior})
    nuevo = cliente.post('/api/notificaciones/leer-todas', headers={'X-CSRFToken': token_nuevo})
    assert viejo.status_code == 400
    assert nuevo.status_code == 200


def test_csrf_error_devuelve_400_no_500(app):
    """Regresión: un CSRFError sin manejador específico caía en el handler
    genérico de Exception y se devolvía como 500 en vez de 400 (bug
    encontrado y corregido durante la migración a v1.0, ver CHANGELOG)."""
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    respuesta = client.post('/api/auth/registro', json={'correo': 'x@x.com'})
    assert respuesta.status_code == 400


@contextmanager
def _app_con_rate_limit_activo(app):
    aplicacion = create_app(dict(app.config_pruebas, RATELIMIT_ENABLED=True))
    try:
        yield aplicacion
    finally:
        with aplicacion.app_context():
            _db.session.remove()
            _db.engine.dispose()


def test_rate_limit_registro(app):
    with _app_con_rate_limit_activo(app) as aplicacion:
        client = aplicacion.test_client()
        respuestas = [client.post('/api/auth/registro', json=dict(DATOS_REGISTRO, correo=f'rl{i}@sanmateo.edu.co'))
                      for i in range(7)]
    assert respuestas[0].status_code == 201
    assert respuestas[-1].status_code == 429


def test_rate_limit_login(app):
    with _app_con_rate_limit_activo(app) as aplicacion:
        client = aplicacion.test_client()
        ultima = None
        for _ in range(12):
            ultima = client.post('/api/auth/login', json={'correo': 'no.existe@sanmateo.edu.co', 'contrasena': 'Cualquiera$123'})
    assert ultima.status_code == 429


def test_rate_limit_reenvio_de_verificacion(app):
    with _app_con_rate_limit_activo(app) as aplicacion:
        client = aplicacion.test_client()
        codigos = [client.post('/api/auth/reenviar-verificacion', json={'correo': 'x@sanmateo.edu.co'}).status_code
                   for _ in range(4)]
    assert codigos == [200, 200, 200, 429]
