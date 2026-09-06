"""Pruebas de integración del flujo de autenticación (RU-001 a RU-015)."""


def test_registro_exitoso(client):
    respuesta = client.post('/api/auth/registro', json={
        'primer_nombre': 'Test',
        'primer_apellido': 'Usuario',
        'correo': 'nuevo@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026',
        'confirmar_contrasena': 'Prueba$Segura2026',
    })
    assert respuesta.status_code == 201
    datos = respuesta.get_json()
    assert datos['usuario']['correo'] == 'nuevo@sanmateo.edu.co'
    assert datos['usuario']['rol'] == 'ciudadano'
    assert 'password_hash' not in datos['usuario']
    assert 'contrasena' not in datos['usuario']


def test_registro_falla_con_contrasena_debil(client):
    respuesta = client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'debil@sanmateo.edu.co',
        'contrasena': '12345678', 'confirmar_contrasena': '12345678',
    })
    assert respuesta.status_code == 400
    assert 'contrasena' in respuesta.get_json()['errores']


def test_registro_falla_si_correo_ya_existe(client):
    payload = {
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'duplicado@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    }
    client.post('/api/auth/registro', json=payload)
    respuesta = client.post('/api/auth/registro', json=payload)
    assert respuesta.status_code == 400
    assert 'correo' in respuesta.get_json()['errores']


def test_registro_ignora_rol_enviado_por_el_cliente(client):
    """Mass assignment: el cliente no puede autoasignarse rol administrador."""
    respuesta = client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'intento.admin@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
        'rol': 'administrador',
    })
    assert respuesta.status_code == 201
    assert respuesta.get_json()['usuario']['rol'] == 'ciudadano'


def test_login_exitoso(client):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'login@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    respuesta = client.post('/api/auth/login', json={
        'correo': 'login@sanmateo.edu.co', 'contrasena': 'Prueba$Segura2026',
    })
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['correo'] == 'login@sanmateo.edu.co'


def test_login_falla_con_contrasena_incorrecta(client):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'login2@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    respuesta = client.post('/api/auth/login', json={
        'correo': 'login2@sanmateo.edu.co', 'contrasena': 'ClaveIncorrecta!99',
    })
    assert respuesta.status_code == 401


def test_login_falla_con_correo_inexistente(client):
    respuesta = client.post('/api/auth/login', json={
        'correo': 'no.existe@sanmateo.edu.co', 'contrasena': 'Cualquiera$123',
    })
    assert respuesta.status_code == 401


def test_login_mensaje_no_revela_si_el_correo_existe(client):
    """Anti user-enumeration: mismo mensaje para correo inexistente y contraseña incorrecta."""
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'existente@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    r1 = client.post('/api/auth/login', json={'correo': 'existente@sanmateo.edu.co', 'contrasena': 'Mala$Clave123'})
    r2 = client.post('/api/auth/login', json={'correo': 'no.existe@sanmateo.edu.co', 'contrasena': 'Mala$Clave123'})
    assert r1.get_json()['mensaje'] == r2.get_json()['mensaje']


def test_logout_limpia_la_sesion(client):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'logout@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    client.post('/api/auth/login', json={'correo': 'logout@sanmateo.edu.co', 'contrasena': 'Prueba$Segura2026'})
    client.post('/api/auth/logout')
    respuesta = client.get('/api/auth/sesion')
    assert respuesta.get_json()['usuario'] is None


def test_sesion_actual_sin_login(client):
    respuesta = client.get('/api/auth/sesion')
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario'] is None


def test_recuperacion_no_revela_si_el_correo_existe(client, capsys):
    r1 = client.post('/api/auth/recuperar', json={'correo': 'no.existe@sanmateo.edu.co'})
    assert r1.status_code == 200
    mensaje_generico = r1.get_json()['mensaje']

    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'recuperar@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    r2 = client.post('/api/auth/recuperar', json={'correo': 'recuperar@sanmateo.edu.co'})
    assert r2.get_json()['mensaje'] == mensaje_generico


def test_restablecer_contrasena_con_token_valido(client, capsys):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'reset@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    client.post('/api/auth/recuperar', json={'correo': 'reset@sanmateo.edu.co'})
    salida = capsys.readouterr().out
    token = salida.strip().split(': ')[-1]

    respuesta = client.post('/api/auth/restablecer', json={
        'token': token, 'contrasena': 'NuevaClave$2026', 'confirmar_contrasena': 'NuevaClave$2026',
    })
    assert respuesta.status_code == 200

    login = client.post('/api/auth/login', json={'correo': 'reset@sanmateo.edu.co', 'contrasena': 'NuevaClave$2026'})
    assert login.status_code == 200


def test_restablecer_contrasena_con_token_invalido(client):
    respuesta = client.post('/api/auth/restablecer', json={
        'token': 'token-que-no-existe', 'contrasena': 'NuevaClave$2026', 'confirmar_contrasena': 'NuevaClave$2026',
    })
    assert respuesta.status_code == 400


def test_restablecer_contrasena_token_de_un_solo_uso(client, capsys):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'reset2@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    client.post('/api/auth/recuperar', json={'correo': 'reset2@sanmateo.edu.co'})
    token = capsys.readouterr().out.strip().split(': ')[-1]

    primero = client.post('/api/auth/restablecer', json={
        'token': token, 'contrasena': 'NuevaClave$2026', 'confirmar_contrasena': 'NuevaClave$2026',
    })
    assert primero.status_code == 200

    segundo = client.post('/api/auth/restablecer', json={
        'token': token, 'contrasena': 'OtraClave$2027', 'confirmar_contrasena': 'OtraClave$2027',
    })
    assert segundo.status_code == 400
