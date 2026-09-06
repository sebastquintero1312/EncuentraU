# Lógica del flujo de recuperación de contraseña.
#
# Flujo: correo -> token seguro con expiración -> el usuario lo usa una vez
# -> se cambia la contraseña -> el token queda invalidado.

import secrets

from app.config.config import Config
from app.models.token_recuperacion import crear_token, buscar_token, token_es_valido, invalidar_token


def generar_token_para_usuario(usuario_id):
    # secrets.token_urlsafe usa el generador criptográficamente seguro del
    # sistema operativo. NUNCA usar Math.random()/random ni IDs secuenciales.
    token = secrets.token_urlsafe(32)
    crear_token(token, usuario_id, Config.MINUTOS_EXPIRACION_TOKEN)
    return token


def obtener_usuario_id_si_token_valido(token):
    """Consulta el token SIN marcarlo como usado. Devuelve (usuario_id, registro)
    o (None, registro) si no es válido. Se consume aparte, con confirmar_uso_token,
    solo cuando el cambio de contraseña ya fue exitoso."""
    registro = buscar_token(token)
    if not token_es_valido(registro):
        return None, registro
    return registro['usuario_id'], registro


def confirmar_uso_token(registro):
    invalidar_token(registro)
