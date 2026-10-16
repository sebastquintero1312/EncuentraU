"""Respaldo (backup) de la base de datos de EncuentraU con pg_dump.

Uso (desde la raíz del proyecto, con el entorno virtual del backend):

    backend\\venv\\Scripts\\python.exe database\\scripts\\respaldo.py
    backend\\venv\\Scripts\\python.exe database\\scripts\\respaldo.py --conservar 10

Qué hace:
  1. Lee la URL del usuario DUEÑO (DATABASE_URL_MIGRACIONES; si no existe,
     DATABASE_URL) desde backend/.env o desde las variables de entorno.
  2. Ejecuta pg_dump en formato "custom" (-Fc): un solo archivo comprimido
     que se restaura con pg_restore (ver restaurar.py), incluidos los
     triggers, procedimientos, vistas y datos.
  3. Guarda el archivo en database/respaldos/encuentrau_AAAAMMDD_HHMMSS.dump
     (carpeta ignorada por git: un respaldo contiene datos personales).
  4. Borra los respaldos más viejos y deja solo los N más recientes.

La contraseña nunca se escribe en la línea de comandos (sería visible para
otros procesos): se le pasa a pg_dump por la variable de entorno PGPASSWORD.

Supabase gratuito no ofrece respaldos descargables; este script (o el flujo
.github/workflows/respaldo-bd.yml, que lo ejecuta en la nube cada día) es la
forma de tener una copia propia.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_RESPALDOS = RAIZ / 'database' / 'respaldos'
RUTAS_POSTGRES_WINDOWS = sorted(Path('C:/Program Files/PostgreSQL').glob('*/bin'), reverse=True)


def cargar_env():
    """Carga backend/.env sin depender de python-dotenv (el script también
    corre en la nube, donde las variables vienen del entorno)."""
    archivo = RAIZ / 'backend' / '.env'
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding='utf-8-sig').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        os.environ.setdefault(clave.strip(), valor.strip())


def buscar_programa(nombre):
    """Busca pg_dump/pg_restore en el PATH o en la instalación típica de Windows."""
    encontrado = shutil.which(nombre)
    if encontrado:
        return encontrado
    for carpeta in RUTAS_POSTGRES_WINDOWS:
        candidato = carpeta / f'{nombre}.exe'
        if candidato.exists():
            return str(candidato)
    sys.exit(f'No se encontró {nombre}. Instala PostgreSQL o agrega su carpeta bin al PATH.')


def separar_url(url):
    """Devuelve (argumentos de conexión sin contraseña, contraseña)."""
    partes = urlparse(url.replace('postgres://', 'postgresql://', 1))
    if partes.scheme != 'postgresql':
        sys.exit('La URL de la base de datos debe empezar por postgresql://')
    argumentos = [
        '--host', partes.hostname or 'localhost',
        '--port', str(partes.port or 5432),
        '--username', unquote(partes.username or ''),
        '--dbname', partes.path.lstrip('/'),
    ]
    return argumentos, unquote(partes.password or '')


def main():
    parser = argparse.ArgumentParser(description='Respaldo de la base de datos de EncuentraU')
    parser.add_argument('--conservar', type=int, default=7, help='Cuántos respaldos guardar (los más recientes)')
    parser.add_argument('--carpeta', default=str(CARPETA_RESPALDOS), help='Carpeta donde guardar el respaldo')
    argumentos = parser.parse_args()

    cargar_env()
    url = os.environ.get('DATABASE_URL_MIGRACIONES') or os.environ.get('DATABASE_URL')
    if not url:
        sys.exit('Falta DATABASE_URL_MIGRACIONES (o DATABASE_URL) en backend/.env o en el entorno.')

    conexion, clave = separar_url(url)
    carpeta = Path(argumentos.carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"encuentrau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"

    entorno = dict(os.environ, PGPASSWORD=clave)
    if 'sslmode=require' in url:
        entorno['PGSSLMODE'] = 'require'

    comando = [buscar_programa('pg_dump'), *conexion, '--format=custom', '--no-owner', '--no-privileges', '--file', str(destino)]
    print(f'Respaldando en {destino} ...')
    resultado = subprocess.run(comando, env=entorno, capture_output=True, text=True)
    if resultado.returncode != 0:
        destino.unlink(missing_ok=True)
        sys.exit(f'pg_dump falló:\n{resultado.stderr.strip()}')

    print(f'Respaldo creado: {destino.name} ({destino.stat().st_size / 1024:.1f} KB)')

    respaldos = sorted(carpeta.glob('encuentrau_*.dump'), reverse=True)
    for viejo in respaldos[max(argumentos.conservar, 1):]:
        viejo.unlink()
        print(f'Borrado respaldo antiguo: {viejo.name}')


if __name__ == '__main__':
    main()
