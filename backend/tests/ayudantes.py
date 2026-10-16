# Atajos compartidos por las pruebas: crear usuarios por el camino real
# (registro + verificación del correo), recorrer el flujo de un objeto y
# consultar la base de datos directamente para comprobar su estado REAL.
#
# Se importa DESPUÉS de conftest.py (que fija las variables de entorno de
# prueba antes de cargar la aplicación).

import re
from app.utils import hoy_en_colombia

from sqlalchemy import text

from app.services.correo_service import CORREOS_ENVIADOS

CONTRASENA = 'ClaveDePrueba!2026'


def consultar(app, sql, **parametros):
    """Lee la base de datos directamente (como dueño), sin pasar por la API
    ni por el ORM: sirve para comprobar el estado REAL de las tablas."""
    with app.motor_dueno.connect() as conexion:
        return [dict(fila._mapping) for fila in conexion.execute(text(sql), parametros)]


def ejecutar(app, sql, **parametros):
    """Modifica la base de datos directamente como dueño (por ejemplo, para
    simular que pasó el tiempo y una reserva venció)."""
    with app.motor_dueno.begin() as conexion:
        conexion.execute(text(sql), parametros)



# ---------------------------------------------------------------------------
# Usuarios de prueba
# ---------------------------------------------------------------------------

def ultimo_token_en_correo(correo, pagina):
    """Busca en los correos "enviados" (proveedor memoria) el último enlace
    a `pagina` dirigido a `correo` y devuelve su token."""
    for enviado in reversed(CORREOS_ENVIADOS):
        if enviado['para'] == correo:
            coincidencia = re.search(rf'{re.escape(pagina)}\?token=([A-Za-z0-9_\-]+)', enviado['texto'])
            if coincidencia:
                return coincidencia.group(1)
    return None


def crear_cliente(app, correo, rol='estudiante', nombre='Ana', apellido='Prueba', verificar=True, iniciar_sesion=True):
    """Registra una cuenta por la API (el camino real), la verifica con el
    enlace del correo y, si se pide, le cambia el rol e inicia sesión.
    Devuelve un test client con el atributo .usuario."""
    cliente = app.test_client()
    respuesta = cliente.post('/api/auth/registro', json={
        'primer_nombre': nombre, 'primer_apellido': apellido, 'correo': correo,
        'contrasena': CONTRASENA, 'confirmar_contrasena': CONTRASENA,
    })
    assert respuesta.status_code == 201, respuesta.get_json()

    if verificar:
        token = ultimo_token_en_correo(correo, 'verificar-correo.html')
        assert cliente.post('/api/auth/verificar-correo', json={'token': token}).status_code == 200

    if rol != 'estudiante':
        ejecutar(app, 'UPDATE usuarios SET rol = :rol WHERE correo = :correo', rol=rol, correo=correo)

    cliente.usuario = None
    if iniciar_sesion and verificar:
        respuesta = cliente.post('/api/auth/login', json={'correo': correo, 'contrasena': CONTRASENA})
        assert respuesta.status_code == 200, respuesta.get_json()
        cliente.usuario = respuesta.get_json()['usuario']
    return cliente


# ---------------------------------------------------------------------------
# Pasos del flujo de negocio (atajos para no repetir en cada prueba)
# ---------------------------------------------------------------------------

def crear_reporte(cliente, tipo='encontrado', **campos):
    datos = {
        'tipo': tipo,
        'nombre': 'Celular',
        'categoria_id': 1,   # Tecnología (datos iniciales)
        'ubicacion_id': 1,   # Biblioteca
        'fecha_evento': hoy_en_colombia().isoformat(),
        'descripcion': 'Samsung A54 negro, funda con un sticker de Pokémon y fondo de pantalla de un perro',
        'detalle_ubicacion': 'Segundo piso, mesa 4',
    }
    datos.update(campos)
    respuesta = cliente.post('/api/objetos', json=datos)
    assert respuesta.status_code == 201, respuesta.get_json()
    return respuesta.get_json()['objeto']


def recibir_en_oficina(encargado_cliente, objeto_id, observaciones=''):
    respuesta = encargado_cliente.post(f'/api/encargado/objetos/{objeto_id}/recepcion',
                                       json={'observaciones': observaciones})
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()['objeto']


def reclamar(cliente, objeto_id, **campos):
    datos = {
        'objeto_id': objeto_id,
        'descripcion': 'Es un Samsung negro con funda de Pokémon; el fondo de pantalla es mi perro',
        'lugar_perdida': 'Biblioteca, segundo piso',
        'fecha_perdida': hoy_en_colombia().isoformat(),
        'evidencia': 'Puedo desbloquearlo con mi huella',
    }
    datos.update(campos)
    return cliente.post('/api/solicitudes', json=datos)


def objeto_en_oficina(estudiante_que_encuentra, encargado_cliente, **campos):
    objeto = crear_reporte(estudiante_que_encuentra, 'encontrado', **campos)
    return recibir_en_oficina(encargado_cliente, objeto['id'])


def preaprobar(encargado_cliente, solicitud_id, respuesta=''):
    return encargado_cliente.post(f'/api/encargado/solicitudes/{solicitud_id}/preaprobar', json={'respuesta': respuesta})


def generar_codigo(cliente, solicitud_id):
    respuesta = cliente.post(f'/api/solicitudes/{solicitud_id}/codigo')
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()['codigo']


def entregar(encargado_cliente, objeto_id, codigo, carne=True, prueba='Desbloqueó el celular con su huella'):
    return encargado_cliente.post(f'/api/encargado/objetos/{objeto_id}/entrega', json={
        'codigo': codigo, 'carne_verificado': carne, 'prueba_propiedad': prueba,
    })


def objeto_reservado(estudiante_que_encuentra, reclamante, encargado_cliente):
    """Deja un objeto en la oficina con una reclamación pre-aprobada.
    Devuelve (objeto, solicitud)."""
    objeto = objeto_en_oficina(estudiante_que_encuentra, encargado_cliente)
    solicitud = reclamar(reclamante, objeto['id']).get_json()['solicitud']
    assert preaprobar(encargado_cliente, solicitud['id']).status_code == 200
    return objeto, solicitud
