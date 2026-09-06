# Modelo de Token de recuperación de contraseña.
#
# IMPORTANTE: igual que usuario.py, esto vive en memoria por ahora.
# En producción esto normalmente se guarda en la base de datos (con índice
# por token y limpieza periódica de los expirados).

from datetime import datetime, timedelta

# Cada token: {token, usuario_id, expira_en, usado}
tokens_recuperacion = []


def crear_token(token, usuario_id, minutos_expiracion):
    registro = {
        'token': token,
        'usuario_id': usuario_id,
        'expira_en': datetime.utcnow() + timedelta(minutes=minutos_expiracion),
        'usado': False,
    }
    tokens_recuperacion.append(registro)
    return registro


def buscar_token(token):
    for registro in tokens_recuperacion:
        if registro['token'] == token:
            return registro
    return None


def token_es_valido(registro):
    if registro is None:
        return False
    if registro['usado']:
        return False
    if datetime.utcnow() > registro['expira_en']:
        return False
    return True


def invalidar_token(registro):
    registro['usado'] = True
