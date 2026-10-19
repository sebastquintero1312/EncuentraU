# Envío de correos electrónicos.
#
# Proveedor según CORREO_PROVEEDOR (ver config.py):
#   consola  imprime el correo en la terminal del servidor (desarrollo).
#   brevo    lo envía de verdad por la API HTTPS de Brevo (producción).
#            Se usa HTTPS y no SMTP porque el plan gratuito de Render
#            bloquea los puertos SMTP (25, 465 y 587).
#   memoria  lo guarda en la lista CORREOS_ENVIADOS (pruebas automáticas).
#
# Un correo que no se pudo enviar NUNCA rompe la operación del usuario: se
# registra en el log y la notificación sigue visible dentro de la aplicación.
# Los correos son solo texto plano: así un nombre de objeto escrito por un
# usuario no puede inyectar HTML en el correo de otra persona.

import json
import urllib.error
import urllib.request

from flask import current_app

URL_API_BREVO = 'https://api.brevo.com/v3/smtp/email'
TIEMPO_ESPERA_SEGUNDOS = 10

CORREOS_ENVIADOS = []  # solo se llena con el proveedor "memoria"


def enviar_correo(destinatario, nombre_destinatario, asunto, texto):
    """Devuelve True si el correo se entregó al proveedor."""
    proveedor = current_app.config.get('CORREO_PROVEEDOR', 'consola')

    if proveedor == 'memoria':
        CORREOS_ENVIADOS.append({'para': destinatario, 'asunto': asunto, 'texto': texto})
        return True

    if proveedor == 'consola':
        # Solo en desarrollo (en producción, config.py exige "brevo"). Esto
        # incluye los enlaces de verificación y recuperación: por eso nunca
        # debe usarse en un servidor real.
        print(f'\n===== [EncuentraU] Correo para {destinatario} =====\nAsunto: {asunto}\n\n{texto}\n'
              f'===== fin del correo =====\n', flush=True)
        return True

    if proveedor == 'brevo':
        return _enviar_con_brevo(destinatario, nombre_destinatario, asunto, texto)

    return False


def _enviar_con_brevo(destinatario, nombre_destinatario, asunto, texto):
    cuerpo = json.dumps({
        'sender': {
            'name': current_app.config['CORREO_REMITENTE_NOMBRE'],
            'email': current_app.config['CORREO_REMITENTE'],
        },
        'to': [{'email': destinatario, 'name': nombre_destinatario or destinatario}],
        'subject': asunto,
        'textContent': texto,
    }).encode('utf-8')

    peticion = urllib.request.Request(
        URL_API_BREVO,
        data=cuerpo,
        method='POST',
        headers={
            'api-key': current_app.config['BREVO_API_KEY'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            # Cloudflare (delante de la API de Brevo) a veces bloquea el
            # User-Agent por defecto de Python ("Python-urllib", error 1010).
            'User-Agent': 'EncuentraU/2.0',
        },
    )
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_ESPERA_SEGUNDOS) as respuesta:
            return 200 <= respuesta.status < 300
    except urllib.error.HTTPError as error:
        # No se registra el cuerpo del correo ni la API key: solo el código.
        current_app.logger.warning('Brevo rechazó el correo (HTTP %s)', error.code)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        current_app.logger.warning('No se pudo contactar a Brevo (%s)', type(error).__name__)
    return False


def pie_de_correo():
    return (
        '\n\n— EncuentraU · Oficina de objetos perdidos\n'
        'Este es un mensaje automático, por favor no lo respondas.'
    )
