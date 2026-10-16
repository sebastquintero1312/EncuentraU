# Configuración de la aplicación Flask.
# Todo lo sensible sale del ".env", nunca queda escrito directamente en el código.

import os
from datetime import timedelta, timezone

CLAVE_INSEGURA_POR_DEFECTO = 'clave-insegura-solo-para-desarrollo'

# Colombia no tiene horario de verano: siempre UTC-5. Se define fijo para no
# depender de la base de datos de zonas horarias del sistema operativo
# (Windows no la trae para Python).
ZONA_HORARIA_COLOMBIA = timezone(timedelta(hours=-5), 'America/Bogota')

PROVEEDORES_CORREO = ('consola', 'brevo', 'memoria')


def modo_debug_permitido(entorno):
    """El debugger interactivo de Flask permite ejecutar código en el servidor:
    solo se activa si FLASK_ENV es EXACTAMENTE "development" (deny by default:
    sin definir, o con cualquier otro valor, queda apagado)."""
    return entorno.get('FLASK_ENV') == 'development'


def _normalizar_url_bd(url):
    url = (url or '').strip()
    if url.startswith('postgres://'):
        # Algunos proveedores entregan el prefijo antiguo "postgres://";
        # SQLAlchemy 2.x requiere "postgresql://".
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    # Clave secreta usada para firmar la sesión, los tokens CSRF y los
    # códigos de retiro (HMAC)
    SECRET_KEY = os.environ.get('SECRET_KEY', CLAVE_INSEGURA_POR_DEFECTO)

    # Entorno actual: development o production
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    ES_PRODUCCION = FLASK_ENV == 'production'

    # Origen(es) permitidos para CORS (el frontend), separados por coma si hay más de uno.
    # Si el frontend se sirve desde el mismo dominio que la API (recomendado), esto no se usa.
    FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:5500')

    # Dirección pública de la aplicación, para armar los enlaces de los correos
    # (verificación de correo, recuperación de contraseña, notificaciones).
    URL_PUBLICA = os.environ.get('URL_PUBLICA', 'http://127.0.0.1:5000').rstrip('/')

    # Cantidad de proxies confiables delante de la app (Render = 1). Con 0, se
    # usa la IP de la conexión directa. Solo debe ser > 0 si de verdad hay un
    # proxy: si no, cualquiera podría falsificar su IP con X-Forwarded-For y
    # saltarse el límite de peticiones.
    NUM_PROXIES = int(os.environ.get('NUM_PROXIES', '0') or 0)

    # --- Configuración de la cookie de sesión ---
    SESSION_COOKIE_HTTPONLY = True          # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE = 'Lax'         # protege contra CSRF básico entre sitios
    SESSION_COOKIE_SECURE = ES_PRODUCCION   # solo por HTTPS en producción (en dev por HTTP no aplica)

    # --- Registro: solo correos institucionales ---
    DOMINIO_CORREO_INSTITUCIONAL = os.environ.get('DOMINIO_CORREO_INSTITUCIONAL', 'sanmateo.edu.co').strip().lower()

    # --- Política de contraseñas ---
    LONGITUD_MINIMA_PASSWORD = 12

    # --- Tokens de un solo uso ---
    MINUTOS_EXPIRACION_TOKEN = 30           # recuperación de contraseña
    HORAS_EXPIRACION_VERIFICACION = 24      # verificación del correo

    # --- Envío de correos ---
    # consola: se imprimen en la terminal del servidor (solo desarrollo)
    # brevo:   se envían de verdad por la API HTTPS de Brevo (producción)
    # memoria: se guardan en una lista (solo pruebas automáticas)
    CORREO_PROVEEDOR = os.environ.get('CORREO_PROVEEDOR', 'consola').strip().lower()
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
    CORREO_REMITENTE = os.environ.get('CORREO_REMITENTE', '')
    CORREO_REMITENTE_NOMBRE = os.environ.get('CORREO_REMITENTE_NOMBRE', 'EncuentraU')

    # --- Base de datos (PostgreSQL) ---
    # DATABASE_URL: usuario de permisos mínimos con el que corre la aplicación.
    # DATABASE_URL_MIGRACIONES: usuario dueño, solo para migraciones y respaldos.
    # Si no se define, las migraciones usan DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = _normalizar_url_bd(os.environ.get('DATABASE_URL'))
    URL_BD_MIGRACIONES = _normalizar_url_bd(os.environ.get('DATABASE_URL_MIGRACIONES')) or SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping: comprueba la conexión antes de usarla. Los poolers en la
    # nube (como el de Supabase) cierran conexiones inactivas.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # --- Paginación ---
    RESULTADOS_POR_PAGINA_DEFECTO = 10
    RESULTADOS_POR_PAGINA_MAXIMO = 50

    # --- Límite de tamaño de petición ---
    # Sin esto, Flask acepta cuerpos de tamaño ilimitado (riesgo de agotar
    # memoria con un solo POST). 1 MB es de sobra para los formularios de
    # texto que maneja la API (no hay subida de archivos).
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    @staticmethod
    def validar_configuracion(config_app):
        """Se llama al crear la app. Si la configuración es insegura o está
        incompleta, la aplicación falla al arrancar con un mensaje claro
        (deny by default) en vez de arrancar a medias."""
        url_bd = config_app.get('SQLALCHEMY_DATABASE_URI') or ''
        if not url_bd.startswith('postgresql'):
            raise RuntimeError(
                'DATABASE_URL no está definida o no es PostgreSQL. EncuentraU v2.0 '
                'usa triggers y procedimientos almacenados de PostgreSQL. Revisa '
                'backend/.env (ver README.md, sección "Cómo ejecutar en desarrollo").'
            )
        if config_app.get('CORREO_PROVEEDOR') not in PROVEEDORES_CORREO:
            raise RuntimeError(f'CORREO_PROVEEDOR inválido. Valores permitidos: {", ".join(PROVEEDORES_CORREO)}')

        if not Config.ES_PRODUCCION:
            return
        if config_app.get('SECRET_KEY') == CLAVE_INSEGURA_POR_DEFECTO:
            raise RuntimeError(
                'SECRET_KEY insegura: define una variable de entorno SECRET_KEY '
                'real antes de arrancar en producción (FLASK_ENV=production).'
            )
        # En producción los correos deben enviarse de verdad: el modo
        # "consola" escribiría enlaces de verificación y recuperación en los
        # logs del servidor.
        if config_app.get('CORREO_PROVEEDOR') != 'brevo':
            raise RuntimeError('En producción CORREO_PROVEEDOR debe ser "brevo".')
        if not config_app.get('BREVO_API_KEY') or not config_app.get('CORREO_REMITENTE'):
            raise RuntimeError('Faltan BREVO_API_KEY o CORREO_REMITENTE para enviar correos en producción.')
        if not config_app.get('URL_PUBLICA', '').startswith('https://'):
            raise RuntimeError('En producción URL_PUBLICA debe ser la dirección https:// de la aplicación.')
