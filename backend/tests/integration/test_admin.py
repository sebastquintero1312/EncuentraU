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
