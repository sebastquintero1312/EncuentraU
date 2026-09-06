# Modelo de Usuario.
#
# IMPORTANTE: en esta fase (v0.25) todavía NO hay conexión a MySQL.
# Los usuarios y los tokens de recuperación se guardan en listas en memoria,
# solo para poder implementar y probar la seguridad del login/registro.
# Esto se reemplazará por tablas reales en la fase de base de datos.
# Si el servidor se reinicia, estos datos se pierden.

# Cada usuario: {id, primer_nombre, segundo_nombre, primer_apellido,
#                segundo_apellido, correo, password_hash, rol}
usuarios = []
_siguiente_id = 1


def crear_usuario(datos, password_hash):
    global _siguiente_id
    usuario = {
        'id': _siguiente_id,
        'primer_nombre': datos['primer_nombre'],
        'segundo_nombre': datos.get('segundo_nombre', ''),
        'primer_apellido': datos['primer_apellido'],
        'segundo_apellido': datos.get('segundo_apellido', ''),
        'correo': datos['correo'].lower(),
        'password_hash': password_hash,
        'rol': 'ciudadano',
    }
    usuarios.append(usuario)
    _siguiente_id += 1
    return usuario


def buscar_por_correo(correo):
    correo = correo.lower()
    for usuario in usuarios:
        if usuario['correo'] == correo:
            return usuario
    return None


def buscar_por_id(usuario_id):
    for usuario in usuarios:
        if usuario['id'] == usuario_id:
            return usuario
    return None


def usuario_publico(usuario):
    # Versión del usuario segura para devolver por la API (sin password_hash)
    return {
        'id': usuario['id'],
        'primer_nombre': usuario['primer_nombre'],
        'primer_apellido': usuario['primer_apellido'],
        'correo': usuario['correo'],
        'rol': usuario['rol'],
    }
