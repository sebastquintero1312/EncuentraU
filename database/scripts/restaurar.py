"""Restauración de un respaldo de EncuentraU con pg_restore.

Uso (desde la raíz del proyecto):

    backend\\venv\\Scripts\\python.exe database\\scripts\\restaurar.py database\\respaldos\\encuentrau_20261016_120000.dump --destino URL --confirmar

  --destino   URL del usuario DUEÑO de la base de datos donde se restaura.
              Si se omite, se usa DATABASE_URL_MIGRACIONES de backend/.env.
  --confirmar obligatorio: la restauración BORRA el contenido actual de la
              base de datos destino (--clean) y lo reemplaza por el del respaldo.

Recomendación: probar primero la restauración en una base de datos de
pruebas (por ejemplo, la de TEST_DATABASE_URL_MIGRACIONES), nunca directo
en producción. Un respaldo que nunca se probó restaurar no es un respaldo.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from respaldo import buscar_programa, cargar_env, separar_url  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='Restaurar un respaldo de EncuentraU')
    parser.add_argument('archivo', help='Archivo .dump creado por respaldo.py')
    parser.add_argument('--destino', help='URL (usuario dueño) de la base de datos destino')
    parser.add_argument('--confirmar', action='store_true', help='Confirma que se borrará el contenido actual del destino')
    argumentos = parser.parse_args()

    archivo = Path(argumentos.archivo)
    if not archivo.exists():
        sys.exit(f'No existe el archivo {archivo}')
    if not argumentos.confirmar:
        sys.exit('La restauración reemplaza TODO el contenido de la base destino. Vuelve a ejecutar con --confirmar.')

    cargar_env()
    url = argumentos.destino or os.environ.get('DATABASE_URL_MIGRACIONES')
    if not url:
        sys.exit('Indica --destino o define DATABASE_URL_MIGRACIONES en backend/.env.')

    conexion, clave = separar_url(url)
    entorno = dict(os.environ, PGPASSWORD=clave)
    if 'sslmode=require' in url:
        entorno['PGSSLMODE'] = 'require'

    comando = [
        buscar_programa('pg_restore'), *conexion,
        '--clean', '--if-exists', '--no-owner', '--no-privileges', '--single-transaction', '--exit-on-error',
        str(archivo),
    ]
    print(f'Restaurando {archivo.name} ...')
    resultado = subprocess.run(comando, env=entorno, capture_output=True, text=True)
    if resultado.returncode != 0:
        sys.exit(f'pg_restore falló (no se aplicó ningún cambio, se usó --single-transaction):\n{resultado.stderr.strip()}')
    print('Restauración completa.')
    print('IMPORTANTE: vuelve a ejecutar backend/migrations/sql/06_permisos.sql como dueño para '
          'restablecer los permisos de encuentrau_app (el respaldo se crea sin privilegios).')


if __name__ == '__main__':
    main()
