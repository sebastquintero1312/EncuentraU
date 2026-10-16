"""Esquema v2.0 en PostgreSQL: tablas normalizadas, triggers, procedimientos
almacenados, vistas, datos iniciales y permisos mínimos.

Reemplaza por completo el esquema v1.0 (SQLite). No migra datos: el
proyecto no tenía datos reales que conservar.

El SQL vive en archivos separados dentro de migrations/sql/ para que se
pueda leer, explicar y reutilizar (por ejemplo, en el editor SQL de
Supabase) sin pasar por Python.

Revision ID: 0001_esquema_v2
Revises:
Create Date: 2026-10-16
"""
import os

from alembic import op

revision = '0001_esquema_v2'
down_revision = None
branch_labels = None
depends_on = None

CARPETA_SQL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql')

# El orden importa: cada archivo usa objetos creados por los anteriores.
ARCHIVOS_UPGRADE = (
    '01_tablas.sql',
    '02_funciones_triggers.sql',
    '03_procedimientos.sql',
    '04_vistas.sql',
    '05_datos_iniciales.sql',
    '06_permisos.sql',
)


def _ejecutar_archivo_sql(nombre):
    with open(os.path.join(CARPETA_SQL, nombre), encoding='utf-8') as archivo:
        sql = archivo.read()
    # Se usa directamente el cursor del driver (psycopg2) en vez de
    # op.execute(): el SQL contiene funciones PL/pgSQL con ":" y "%", que
    # SQLAlchemy intentaría interpretar como parámetros. Es la misma
    # conexión y la misma transacción de Alembic: si un archivo falla,
    # PostgreSQL deshace TODA la migración (DDL transaccional).
    conexion_dbapi = op.get_bind().connection
    with conexion_dbapi.cursor() as cursor:
        cursor.execute(sql)


def upgrade():
    if op.get_bind().dialect.name != 'postgresql':
        raise RuntimeError(
            'EncuentraU v2.0 necesita PostgreSQL (triggers, procedimientos y '
            'permisos no existen en SQLite). Revisa DATABASE_URL en backend/.env.'
        )
    for nombre in ARCHIVOS_UPGRADE:
        _ejecutar_archivo_sql(nombre)


def downgrade():
    _ejecutar_archivo_sql('00_eliminar.sql')
