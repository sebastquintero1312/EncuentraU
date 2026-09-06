# Fixtures compartidas para toda la suite de pruebas.
#
# IMPORTANTE: las variables de entorno de prueba se fijan ANTES de importar
# app.config.config (que las lee al definirse la clase Config), por eso los
# imports de la aplicación están después de setear os.environ.

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'clave-de-pruebas-no-usar-en-produccion-0123456789'
os.environ['DATABASE_URL'] = ''  # se sobreescribe por prueba con un archivo temporal

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402


@pytest.fixture()
def app():
    fd, ruta_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    aplicacion = create_app()
    aplicacion.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{ruta_db}',
        WTF_CSRF_ENABLED=False,   # las pruebas de CSRF activan esto aparte
        RATELIMIT_ENABLED=False,  # las pruebas de rate limit activan esto aparte
    )

    with aplicacion.app_context():
        _db.create_all()
        yield aplicacion
        _db.session.remove()
        _db.drop_all()

    os.remove(ruta_db)


@pytest.fixture()
def client(app):
    return app.test_client()


def _registrar_y_loguear(client, correo, contrasena='ClaveDePrueba!2026', nombre='Test', apellido='Usuario'):
    client.post('/api/auth/registro', json={
        'primer_nombre': nombre,
        'primer_apellido': apellido,
        'correo': correo,
        'contrasena': contrasena,
        'confirmar_contrasena': contrasena,
    })
    respuesta = client.post('/api/auth/login', json={'correo': correo, 'contrasena': contrasena})
    return respuesta.get_json()['usuario']


@pytest.fixture()
def usuario_a(client):
    """Un ciudadano autenticado en la sesión del `client`."""
    return _registrar_y_loguear(client, 'usuario.a@sanmateo.edu.co', nombre='Ana', apellido='A')


@pytest.fixture()
def cliente_admin(app):
    """Un segundo test client, autenticado como administrador."""
    admin_client = app.test_client()
    usuario = _registrar_y_loguear(admin_client, 'admin@sanmateo.edu.co', nombre='Admin', apellido='EncuentraU')
    with app.app_context():
        from app.models.usuario import buscar_por_correo
        u = buscar_por_correo('admin@sanmateo.edu.co')
        u.rol = 'administrador'
        _db.session.commit()
    return admin_client


@pytest.fixture()
def cliente_b(app):
    """Un segundo test client, autenticado como un ciudadano distinto (usuario B)."""
    otro_client = app.test_client()
    _registrar_y_loguear(otro_client, 'usuario.b@sanmateo.edu.co', nombre='Beto', apellido='B')
    return otro_client
