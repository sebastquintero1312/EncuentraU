"""Prueba de regresión de esquema: confirma que `flask db upgrade` (el
camino real que se usa en desarrollo y producción) produce un esquema
compatible con los modelos actuales.

Por qué existe: el resto de la suite (ver conftest.py) usa
`db.create_all()` para crear el esquema de pruebas, que es rápido pero
genera las tablas DIRECTAMENTE desde las clases de SQLAlchemy — nunca
ejercita las migraciones de Alembic en migrations/versions/. Si alguien
agrega o cambia una columna en un modelo sin generar la migración
correspondiente, esa suite seguiría en verde mientras un despliegue real
(que sí corre `flask db upgrade`) fallaría o quedaría con un esquema
desactualizado. Esta prueba corre el camino real para detectar ese drift
(hallazgo de la revisión final independiente antes de v1.0).
"""

import os
import subprocess
import sys
import tempfile

import pytest


@pytest.fixture()
def base_de_datos_migrada():
    fd, ruta_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    directorio_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entorno = dict(os.environ)
    entorno['FLASK_APP'] = 'app.py'
    entorno['FLASK_ENV'] = 'testing'
    entorno['SECRET_KEY'] = 'clave-de-pruebas-no-usar-en-produccion-0123456789'
    entorno['DATABASE_URL'] = f'sqlite:///{ruta_db}'

    resultado = subprocess.run(
        [sys.executable, '-m', 'flask', 'db', 'upgrade'],
        cwd=directorio_backend, env=entorno,
        capture_output=True, text=True,
    )
    assert resultado.returncode == 0, (
        f'flask db upgrade falló (esto indicaría un esquema de migración roto '
        f'o desincronizado con los modelos):\n{resultado.stdout}\n{resultado.stderr}'
    )

    yield ruta_db
    os.remove(ruta_db)


def test_migracion_real_crea_un_esquema_utilizable_por_los_modelos(base_de_datos_migrada):
    """Tras `flask db upgrade` (el comando real usado en desarrollo/producción,
    no db.create_all()), confirma que se puede crear y leer un usuario real
    a través del ORM, usando exactamente esa base de datos migrada.

    IMPORTANTE: el override de la URL de la base de datos se pasa como
    config_overrides de create_app(), no como app.config[...] = ... después
    de crear la app. Flask-SQLAlchemy fija el engine dentro de db.init_app()
    (llamado por create_app()); cambiar app.config después de eso no tiene
    ningún efecto real (bug real encontrado durante la revisión final de
    v1.0 — ver el comentario en create_app())."""
    from app import create_app
    from app.extensions import db as _db

    aplicacion = create_app(config_overrides={
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{base_de_datos_migrada}',
    })

    with aplicacion.app_context():
        from app.models.usuario import crear_usuario, buscar_por_correo
        from app.services import auth_service

        datos = {
            'primer_nombre': 'Test', 'primer_apellido': 'Migracion',
            'correo': 'migracion@sanmateo.edu.co',
        }
        crear_usuario(datos, auth_service.crear_hash('ClaveDePrueba!2026'))

        encontrado = buscar_por_correo('migracion@sanmateo.edu.co')
        assert encontrado is not None
        assert encontrado.rol == 'ciudadano'

        _db.session.remove()
        _db.engine.dispose()  # libera el archivo antes de que el fixture lo borre (Windows)
