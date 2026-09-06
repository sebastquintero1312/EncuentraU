# Punto de entrada del backend Flask.
# Ejecutar con: python app.py

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    modo_debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(host='127.0.0.1', port=puerto, debug=modo_debug)
