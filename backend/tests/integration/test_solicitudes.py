"""Pruebas de integración del proceso de reclamación (solicitudes)."""

import datetime


def _payload_objeto(tipo='encontrado', **overrides):
    datos = {
        'tipo': tipo,
        'nombre': 'Celular Samsung',
        'categoria': 'Tecnología',
        'descripcion': 'Celular Samsung negro con la pantalla rayada',
        'ubicacion': 'Cafetería bloque 4',
        'fecha_evento': datetime.date.today().isoformat(),
    }
    datos.update(overrides)
    return datos


def _payload_solicitud(objeto_id, **overrides):
    datos = {
        'objeto_id': objeto_id,
        'contacto': 'contacto@sanmateo.edu.co',
        'mensaje': 'Ese celular es mío, tiene una funda transparente',
    }
    datos.update(overrides)
    return datos


def test_crear_solicitud_requiere_autenticacion(client, usuario_a):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    client.post('/api/auth/logout')
    respuesta = client.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    assert respuesta.status_code == 401


def test_no_puede_reclamar_su_propio_objeto(client, usuario_a):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = client.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    assert respuesta.status_code == 400
    assert 'objeto_id' in respuesta.get_json()['errores']


def test_puede_reclamar_objeto_ajeno(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    assert respuesta.status_code == 201
    assert respuesta.get_json()['solicitud']['estado'] == 'pendiente'


def test_reclamar_un_objeto_lo_pasa_a_en_proceso(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    detalle = client.get(f"/api/objetos/{objeto['id']}")
    assert detalle.get_json()['objeto']['estado'] == 'en_proceso'


def test_no_puede_haber_dos_solicitudes_abiertas_del_mismo_usuario(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    segunda = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))
    assert segunda.status_code == 400


def test_solicitudes_privadas_solo_visibles_para_dueno_y_admin(client, usuario_a, cliente_b, cliente_admin):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id']))

    # El dueño del objeto SÍ puede ver la información de verificación
    como_dueno = client.get(f"/api/objetos/{objeto['id']}/solicitudes")
    assert como_dueno.status_code == 200
    assert len(como_dueno.get_json()['datos']) == 1

    # Un admin también puede
    como_admin = cliente_admin.get(f"/api/objetos/{objeto['id']}/solicitudes")
    assert como_admin.status_code == 200

    # Un tercero (ni dueño ni admin) no puede
    otro_client = client.application.test_client()
    otro_client.post('/api/auth/registro', json={
        'primer_nombre': 'Terceiro', 'primer_apellido': 'C',
        'correo': 'tercero@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    otro_client.post('/api/auth/login', json={'correo': 'tercero@sanmateo.edu.co', 'contrasena': 'Prueba$Segura2026'})
    como_tercero = otro_client.get(f"/api/objetos/{objeto['id']}/solicitudes")
    assert como_tercero.status_code == 403


def test_admin_aprueba_solicitud_resuelve_el_objeto(client, usuario_a, cliente_b, cliente_admin):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    solicitud = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id'])).get_json()['solicitud']

    respuesta = cliente_admin.put(f"/api/admin/solicitudes/{solicitud['id']}", json={'estado': 'aprobada'})
    assert respuesta.status_code == 200

    detalle = client.get(f"/api/objetos/{objeto['id']}")
    assert detalle.get_json()['objeto']['estado'] == 'resuelto'


def test_admin_rechaza_solicitud_reactiva_el_objeto(client, usuario_a, cliente_b, cliente_admin):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    solicitud = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id'])).get_json()['solicitud']

    respuesta = cliente_admin.put(f"/api/admin/solicitudes/{solicitud['id']}", json={'estado': 'rechazada'})
    assert respuesta.status_code == 200

    detalle = client.get(f"/api/objetos/{objeto['id']}")
    assert detalle.get_json()['objeto']['estado'] == 'activo'


def test_solicitudes_admin_requiere_rol_admin(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    solicitud = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id'])).get_json()['solicitud']
    respuesta = cliente_b.put(f"/api/admin/solicitudes/{solicitud['id']}", json={'estado': 'aprobada'})
    assert respuesta.status_code == 403


def test_solicitante_puede_cancelar_su_propia_solicitud(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    solicitud = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id'])).get_json()['solicitud']
    respuesta = cliente_b.delete(f"/api/solicitudes/{solicitud['id']}")
    assert respuesta.status_code == 200

    detalle = client.get(f"/api/objetos/{objeto['id']}")
    assert detalle.get_json()['objeto']['estado'] == 'activo'


def test_otro_usuario_no_puede_cancelar_solicitud_ajena(client, usuario_a, cliente_b):
    objeto = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    solicitud = cliente_b.post('/api/solicitudes', json=_payload_solicitud(objeto['id'])).get_json()['solicitud']
    respuesta = client.delete(f"/api/solicitudes/{solicitud['id']}")
    assert respuesta.status_code == 403
