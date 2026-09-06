"""Pruebas de integración del panel de administración de usuarios."""


def test_listar_usuarios_requiere_admin(client, usuario_a):
    assert client.get('/api/admin/usuarios').status_code == 403


def test_listar_usuarios_sin_sesion(client):
    assert client.get('/api/admin/usuarios').status_code == 401


def test_admin_puede_listar_usuarios(client, usuario_a, cliente_admin):
    respuesta = cliente_admin.get('/api/admin/usuarios')
    assert respuesta.status_code == 200
    assert respuesta.get_json()['total'] >= 2  # usuario_a + admin


def test_admin_puede_promover_a_otro_usuario(client, usuario_a, cliente_admin):
    respuesta = cliente_admin.put(f"/api/admin/usuarios/{usuario_a['id']}", json={'rol': 'administrador'})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['rol'] == 'administrador'


def test_admin_no_puede_modificar_su_propia_cuenta(client, usuario_a, cliente_admin):
    # cliente_admin no conoce su propio id desde este test; lo pedimos a /sesion
    yo = cliente_admin.get('/api/auth/sesion').get_json()['usuario']
    respuesta = cliente_admin.put(f"/api/admin/usuarios/{yo['id']}", json={'activo': False})
    assert respuesta.status_code == 400


def test_ciudadano_no_puede_promoverse_a_si_mismo(client, usuario_a):
    respuesta = client.put(f"/api/admin/usuarios/{usuario_a['id']}", json={'rol': 'administrador'})
    assert respuesta.status_code == 403


def test_admin_desactiva_usuario_y_no_puede_loguear(client, usuario_a, cliente_admin):
    cliente_admin.put(f"/api/admin/usuarios/{usuario_a['id']}", json={'activo': False})
    client.post('/api/auth/logout')
    respuesta = client.post('/api/auth/login', json={
        'correo': 'usuario.a@sanmateo.edu.co', 'contrasena': 'ClaveDePrueba!2026',
    })
    assert respuesta.status_code == 401


def test_actualizar_usuario_rechaza_rol_invalido(client, usuario_a, cliente_admin):
    respuesta = cliente_admin.put(f"/api/admin/usuarios/{usuario_a['id']}", json={'rol': 'superadmin'})
    assert respuesta.status_code == 400


def _crear_objeto(client, **overrides):
    import datetime
    datos = {
        'tipo': 'perdido', 'nombre': 'Objeto de prueba', 'categoria': 'Otro',
        'descripcion': 'Descripción de prueba con suficiente longitud',
        'ubicacion': 'Test', 'fecha_evento': datetime.date.today().isoformat(),
    }
    datos.update(overrides)
    return client.post('/api/objetos', json=datos).get_json()['objeto']


def test_listar_objetos_admin_requiere_admin(client, usuario_a):
    assert client.get('/api/admin/objetos').status_code == 403


def test_listar_objetos_admin_incluye_todos_los_estados(client, usuario_a, cliente_admin):
    objeto = _crear_objeto(client)
    client.delete(f"/api/objetos/{objeto['id']}")  # lo cancela

    # La búsqueda pública, sin filtro, NO muestra cancelados
    publica = client.get('/api/objetos')
    assert publica.get_json()['total'] == 0

    # La vista de admin sí los incluye
    admin_vista = cliente_admin.get('/api/admin/objetos')
    assert admin_vista.get_json()['total'] == 1


def test_admin_cambia_estado_de_un_objeto(client, usuario_a, cliente_admin):
    objeto = _crear_objeto(client)
    respuesta = cliente_admin.put(f"/api/admin/objetos/{objeto['id']}/estado", json={'estado': 'cerrado'})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['estado'] == 'cerrado'


def test_cambiar_estado_objeto_requiere_admin(client, usuario_a):
    objeto = _crear_objeto(client)
    respuesta = client.put(f"/api/admin/objetos/{objeto['id']}/estado", json={'estado': 'cerrado'})
    assert respuesta.status_code == 403


def test_cambiar_estado_objeto_rechaza_transicion_invalida(client, usuario_a, cliente_admin):
    objeto = _crear_objeto(client)
    # activo -> resuelto no es una transición válida directa (falta pasar por en_proceso)
    respuesta = cliente_admin.put(f"/api/admin/objetos/{objeto['id']}/estado", json={'estado': 'resuelto'})
    assert respuesta.status_code == 400
