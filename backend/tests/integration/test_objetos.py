"""Pruebas de integración de reportes de objetos perdidos/encontrados."""

import datetime


def _payload_objeto(tipo='perdido', **overrides):
    datos = {
        'tipo': tipo,
        'nombre': 'Mochila azul Totto',
        'categoria': 'Accesorios',
        'descripcion': 'Mochila azul con laptop adentro, marca Totto',
        'ubicacion': 'Biblioteca central',
        'fecha_evento': datetime.date.today().isoformat(),
    }
    datos.update(overrides)
    return datos


def test_crear_objeto_requiere_autenticacion(client):
    respuesta = client.post('/api/objetos', json=_payload_objeto())
    assert respuesta.status_code == 401


def test_crear_objeto_autenticado(client, usuario_a):
    respuesta = client.post('/api/objetos', json=_payload_objeto())
    assert respuesta.status_code == 201
    objeto = respuesta.get_json()['objeto']
    assert objeto['estado'] == 'activo'
    assert objeto['usuario_id'] == usuario_a['id']


def test_crear_objeto_valida_categoria(client, usuario_a):
    respuesta = client.post('/api/objetos', json=_payload_objeto(categoria='NoExiste'))
    assert respuesta.status_code == 400
    assert 'categoria' in respuesta.get_json()['errores']


def test_crear_objeto_rechaza_fecha_futura(client, usuario_a):
    fecha_futura = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
    respuesta = client.post('/api/objetos', json=_payload_objeto(fecha_evento=fecha_futura))
    assert respuesta.status_code == 400


def test_listar_objetos_es_publico(client, usuario_a):
    client.post('/api/objetos', json=_payload_objeto())
    client.post('/api/auth/logout')
    respuesta = client.get('/api/objetos')
    assert respuesta.status_code == 200
    assert respuesta.get_json()['total'] == 1


def test_listar_objetos_no_expone_correo_del_reportante(client, usuario_a):
    client.post('/api/objetos', json=_payload_objeto())
    respuesta = client.get('/api/objetos')
    objeto = respuesta.get_json()['datos'][0]
    assert 'usuario_correo' not in objeto


def test_buscar_objetos_por_texto(client, usuario_a):
    client.post('/api/objetos', json=_payload_objeto(nombre='Mochila azul'))
    client.post('/api/objetos', json=_payload_objeto(
        nombre='Cuaderno rojo', categoria='Útiles', descripcion='Cuaderno de apuntes de Cálculo II',
    ))
    respuesta = client.get('/api/objetos?q=mochila')
    assert respuesta.get_json()['total'] == 1


def test_actualizar_objeto_propio(client, usuario_a):
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = client.put(f"/api/objetos/{creado['id']}", json=_payload_objeto(nombre='Mochila azul actualizada'))
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['nombre'] == 'Mochila azul actualizada'


def test_no_puede_editar_reporte_ajeno(client, usuario_a, cliente_b):
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = cliente_b.put(f"/api/objetos/{creado['id']}", json=_payload_objeto(nombre='Hackeado'))
    assert respuesta.status_code == 403


def test_no_puede_cancelar_reporte_ajeno(client, usuario_a, cliente_b):
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = cliente_b.delete(f"/api/objetos/{creado['id']}")
    assert respuesta.status_code == 403


def test_mass_assignment_no_permite_cambiar_estado_directamente(client, usuario_a):
    """El campo 'estado' no está en la whitelist de actualizar_objeto: enviarlo se ignora."""
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = client.put(f"/api/objetos/{creado['id']}", json=_payload_objeto(estado='resuelto'))
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['estado'] == 'activo'


def test_cancelar_reporte_propio(client, usuario_a):
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    respuesta = client.delete(f"/api/objetos/{creado['id']}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['estado'] == 'cancelado'


def test_no_se_puede_cancelar_dos_veces(client, usuario_a):
    creado = client.post('/api/objetos', json=_payload_objeto()).get_json()['objeto']
    client.delete(f"/api/objetos/{creado['id']}")
    segunda = client.delete(f"/api/objetos/{creado['id']}")
    assert segunda.status_code == 400


def test_mis_reportes_requiere_autenticacion(client):
    assert client.get('/api/mis-reportes').status_code == 401


def test_mis_reportes_solo_devuelve_los_propios(client, usuario_a, cliente_b):
    client.post('/api/objetos', json=_payload_objeto())
    cliente_b.post('/api/objetos', json=_payload_objeto(nombre='Objeto de B'))
    respuesta = client.get('/api/mis-reportes')
    datos = respuesta.get_json()['datos']
    assert len(datos) == 1
    assert datos[0]['usuario_id'] == usuario_a['id']


def test_coincidencias_encuentra_objeto_del_tipo_contrario(client, usuario_a, cliente_b):
    perdido = client.post('/api/objetos', json=_payload_objeto(tipo='perdido')).get_json()['objeto']
    cliente_b.post('/api/objetos', json=_payload_objeto(
        tipo='encontrado', nombre='Mochila azul encontrada', descripcion='Encontre mochila azul Totto',
    ))
    respuesta = client.get(f"/api/objetos/{perdido['id']}")
    coincidencias = respuesta.get_json()['coincidencias']
    assert len(coincidencias) == 1
    assert coincidencias[0]['tipo'] == 'encontrado'
    assert coincidencias[0]['posible_coincidencia'] is True


def test_coincidencia_no_cambia_estado_del_objeto(client, usuario_a, cliente_b):
    """Una posible coincidencia es solo una pista: NO transfiere propiedad ni cambia el estado."""
    perdido = client.post('/api/objetos', json=_payload_objeto(tipo='perdido')).get_json()['objeto']
    cliente_b.post('/api/objetos', json=_payload_objeto(tipo='encontrado', nombre='Mochila azul encontrada'))
    respuesta = client.get(f"/api/objetos/{perdido['id']}")
    assert respuesta.get_json()['objeto']['estado'] == 'activo'
