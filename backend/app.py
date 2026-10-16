# Punto de entrada del backend Flask.
# Ejecutar con: python app.py

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.config.config import modo_debug_permitido

app = create_app()

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    # Deny by default: el modo debug SOLO se activa si FLASK_ENV vale
    # explícitamente "development". Cualquier otro valor (incluyendo no
    # definirlo) arranca en modo seguro, sin debugger interactivo expuesto.
    # (Corrección de v2.0: antes, NO definir FLASK_ENV activaba el debug.)
    modo_debug = modo_debug_permitido(os.environ)
    # 0.0.0.0 es necesario para que hosts como Render/Railway expongan el
    # puerto; en el equipo local esto solo es alcanzable desde la misma
    # máquina salvo que se abra el firewall explícitamente.
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    app.run(host=host, port=puerto, debug=modo_debug)
