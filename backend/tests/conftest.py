# Fixtures compartidas para toda la suite de pruebas.
#
# Las pruebas corren contra una base de datos PostgreSQL REAL y separada
# (TEST_DATABASE_URL en backend/.env), con el mismo esquema, los mismos
# triggers, procedimientos y permisos que producción:
#
#   * Al empezar la ejecución se borra el esquema de pruebas y se aplica la
#     migración real (upgrade -> downgrade -> upgrade, para probar ambas).
#   * Antes de CADA prueba se vacían las tablas y se recargan los datos
#     iniciales: ninguna prueba depende de otra.
#   * La aplicación se conecta con el usuario de permisos mínimos
#     (encuentrau_app), igual que en producción. El usuario dueño solo se usa
#     para preparar y limpiar la base de datos.
#
# IMPORTANTE: las variables de entorno se fijan ANTES de importar la
# aplicación (Config las lee al importarse).

import os
import sys

import pytest
from dotenv import load_dotenv

DIRECTORIO_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIRECTORIO_BACKEND)
load_dotenv(os.path.join(DIRECTORIO_BACKEND, '.env'))

URL_PRUEBAS = os.environ.get('TEST_DATABASE_URL', '')
URL_PRUEBAS_DUENO = os.environ.get('TEST_DATABASE_URL_MIGRACIONES', '') or URL_PRUEBAS

if not URL_PRUEBAS:
    raise RuntimeError('Define TEST_DATABASE_URL en backend/.env (ver README.md, sección Pruebas).')
# Protección: las pruebas BORRAN todo el contenido de la base de datos.
# Nunca deben apuntar a la base de desarrollo ni a producción.
for url in (URL_PRUEBAS, URL_PRUEBAS_DUENO):
    nombre_bd = url.rsplit('/', 1)[-1].split('?')[0]
    if 'test' not in nombre_bd or url in (os.environ.get('DATABASE_URL'), os.environ.get('DATABASE_URL_MIGRACIONES')):
        raise RuntimeError(f'TEST_DATABASE_URL debe apuntar a una base de datos de pruebas, no a "{nombre_bd}".')

os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'clave-de-pruebas-no-usar-en-produccion-0123456789'
os.environ['DATABASE_URL'] = URL_PRUEBAS
os.environ['DATABASE_URL_MIGRACIONES'] = URL_PRUEBAS_DUENO
os.environ['CORREO_PROVEEDOR'] = 'memoria'

import flask_migrate  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.services.correo_service import CORREOS_ENVIADOS  # noqa: E402
from tests.ayudantes import crear_cliente  # noqa: E402

DIRECTORIO_MIGRACIONES = os.path.join(DIRECTORIO_BACKEND, 'migrations')
ARCHIVO_DATOS_INICIALES = os.path.join(DIRECTORIO_MIGRACIONES, 'sql', '05_datos_iniciales.sql')

CONFIG_PRUEBAS = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': URL_PRUEBAS,
    'URL_BD_MIGRACIONES': URL_PRUEBAS_DUENO,
    'WTF_CSRF_ENABLED': False,   # las pruebas de CSRF lo activan aparte
    'RATELIMIT_ENABLED': False,  # las pruebas de rate limit lo activan aparte
    'CORREO_PROVEEDOR': 'memoria',
    'URL_PUBLICA': 'http://localhost',
}

TABLAS_A_LIMPIAR = (
    'auditoria, notificaciones, entregas, solicitudes, objetos, tokens_usuario, '
    'usuarios, categorias, ubicaciones, parametros'
)


def _ejecutar_sql_crudo(conexion, sql):
    with conexion.connection.cursor() as cursor:
        cursor.execute(sql)


@pytest.fixture(scope='session')
def motor_dueno():
    """Conexión con el usuario DUEÑO (solo para preparar/limpiar y para las
    pruebas que verifican qué puede y qué no puede hacer cada usuario)."""
    motor = create_engine(URL_PRUEBAS_DUENO, poolclass=NullPool)
    with motor.begin() as conexion:
        _ejecutar_sql_crudo(conexion, 'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;')

    aplicacion = create_app(CONFIG_PRUEBAS)
    with aplicacion.app_context():
        # La migración real, en ambos sentidos: si 00_eliminar.sql olvidara
        # algún objeto, el segundo upgrade fallaría por "ya existe".
        flask_migrate.upgrade(directory=DIRECTORIO_MIGRACIONES)
        flask_migrate.downgrade(directory=DIRECTORIO_MIGRACIONES, revision='base')
        flask_migrate.upgrade(directory=DIRECTORIO_MIGRACIONES)
        _db.engine.dispose()

    yield motor
    motor.dispose()


@pytest.fixture(scope='session')
def motor_app():
    """Conexión directa con el usuario de la APLICACIÓN (permisos mínimos)."""
    motor = create_engine(URL_PRUEBAS, poolclass=NullPool)
    yield motor
    motor.dispose()


@pytest.fixture()
def app(motor_dueno):
    with open(ARCHIVO_DATOS_INICIALES, encoding='utf-8') as archivo:
        datos_iniciales = archivo.read()
    with motor_dueno.begin() as conexion:
        # Solo el dueño puede desactivar el trigger que protege la auditoría
        # (la aplicación no puede: ver tests/integration/test_esquema_bd.py).
        _ejecutar_sql_crudo(conexion, 'ALTER TABLE auditoria DISABLE TRIGGER trg_auditoria_sin_vaciar')
        _ejecutar_sql_crudo(conexion, f'TRUNCATE {TABLAS_A_LIMPIAR} RESTART IDENTITY CASCADE')
        _ejecutar_sql_crudo(conexion, 'ALTER TABLE auditoria ENABLE TRIGGER trg_auditoria_sin_vaciar')
        _ejecutar_sql_crudo(conexion, datos_iniciales)
    CORREOS_ENVIADOS.clear()

    aplicacion = create_app(CONFIG_PRUEBAS)
    aplicacion.motor_dueno = motor_dueno
    aplicacion.config_pruebas = dict(CONFIG_PRUEBAS)
    # A propósito NO se deja un app_context abierto durante la prueba: así
    # cada petición del test client crea su propio contexto (y su propia
    # sesión de base de datos), exactamente como en producción.
    yield aplicacion
    with aplicacion.app_context():
        _db.session.remove()
        _db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()



@pytest.fixture()
def estudiante_a(app):
    return crear_cliente(app, 'ana.a@sanmateo.edu.co', nombre='Ana', apellido='Acosta')


@pytest.fixture()
def estudiante_b(app):
    return crear_cliente(app, 'beto.b@sanmateo.edu.co', nombre='Beto', apellido='Bernal')


@pytest.fixture()
def estudiante_c(app):
    return crear_cliente(app, 'carla.c@sanmateo.edu.co', nombre='Carla', apellido='Castro')


@pytest.fixture()
def encargado(app):
    return crear_cliente(app, 'elena.encargada@sanmateo.edu.co', rol='encargado', nombre='Elena', apellido='Encargada')


@pytest.fixture()
def encargado_2(app):
    return crear_cliente(app, 'esteban.encargado@sanmateo.edu.co', rol='encargado', nombre='Esteban', apellido='Encargado')


@pytest.fixture()
def admin(app):
    return crear_cliente(app, 'admin@sanmateo.edu.co', rol='administrador', nombre='Adriana', apellido='Admin')
