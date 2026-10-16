"""Registro, verificación del correo institucional, inicio de sesión y
recuperación de contraseña."""

from tests.ayudantes import CONTRASENA, consultar, crear_cliente, ejecutar, ultimo_token_en_correo
from app.services.correo_service import CORREOS_ENVIADOS


def _registro(client, correo, **extra):
    datos = {
        'primer_nombre': 'Laura', 'primer_apellido': 'Lopez', 'correo': correo,
        'contrasena': CONTRASENA, 'confirmar_contrasena': CONTRASENA,
    }
    datos.update(extra)
    return client.post('/api/auth/registro', json=datos)


def test_registro_exitoso_crea_estudiante_sin_verificar(client, app):
    respuesta = _registro(client, 'laura@sanmateo.edu.co')
    assert respuesta.status_code == 201
    fila = consultar(app, 'SELECT rol, correo_verificado_en FROM usuarios WHERE correo = :c', c='laura@sanmateo.edu.co')[0]
    assert fila['rol'] == 'estudiante'
    assert fila['correo_verificado_en'] is None


def test_registro_solo_con_correo_institucional(client):
    respuesta = _registro(client, 'laura@gmail.com')
    assert respuesta.status_code == 400
    assert 'institucional' in respuesta.get_json()['errores']['correo']


def test_registro_ignora_el_rol_que_manda_el_cliente(client, app):
    _registro(client, 'hacker@sanmateo.edu.co', rol='administrador')
    fila = consultar(app, 'SELECT rol FROM usuarios WHERE correo = :c', c='hacker@sanmateo.edu.co')[0]
    assert fila['rol'] == 'estudiante'


def test_registro_con_correo_existente_no_revela_que_existe(client, app):
    primera = _registro(client, 'laura@sanmateo.edu.co')
    CORREOS_ENVIADOS.clear()
    segunda = _registro(client, 'laura@sanmateo.edu.co')
    # Misma respuesta para un correo nuevo y uno existente
    assert segunda.status_code == primera.status_code == 201
    assert segunda.get_json() == primera.get_json()
    # ...y al dueño real se le avisa por correo
    assert any('intento de registro' in c['asunto'] for c in CORREOS_ENVIADOS)
    assert consultar(app, 'SELECT count(*) AS n FROM usuarios')[0]['n'] == 1


def test_no_puede_iniciar_sesion_sin_verificar_el_correo(client):
    _registro(client, 'laura@sanmateo.edu.co')
    respuesta = client.post('/api/auth/login', json={'correo': 'laura@sanmateo.edu.co', 'contrasena': CONTRASENA})
    assert respuesta.status_code == 403
    assert respuesta.get_json()['codigo'] == 'correo_no_verificado'


def test_mensaje_de_verificacion_solo_con_contrasena_correcta(client):
    _registro(client, 'laura@sanmateo.edu.co')
    respuesta = client.post('/api/auth/login', json={'correo': 'laura@sanmateo.edu.co', 'contrasena': 'Incorrecta!2026x'})
    assert respuesta.status_code == 401
    assert 'codigo' not in respuesta.get_json()


def test_verificar_correo_con_el_enlace_permite_entrar(client):
    _registro(client, 'laura@sanmateo.edu.co')
    token = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    assert token
    assert client.post('/api/auth/verificar-correo', json={'token': token}).status_code == 200
    respuesta = client.post('/api/auth/login', json={'correo': 'laura@sanmateo.edu.co', 'contrasena': CONTRASENA})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['correo_verificado'] is True


def test_token_de_verificacion_es_de_un_solo_uso(client):
    _registro(client, 'laura@sanmateo.edu.co')
    token = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    assert client.post('/api/auth/verificar-correo', json={'token': token}).status_code == 200
    assert client.post('/api/auth/verificar-correo', json={'token': token}).status_code == 400


def test_token_de_verificacion_vencido_no_sirve(client, app):
    _registro(client, 'laura@sanmateo.edu.co')
    token = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    ejecutar(app, "UPDATE tokens_usuario SET created_at = now() - interval '3 days', expira_en = now() - interval '1 day'")
    assert client.post('/api/auth/verificar-correo', json={'token': token}).status_code == 400


def test_token_inventado_no_sirve(client):
    assert client.post('/api/auth/verificar-correo', json={'token': 'token-inventado'}).status_code == 400
    assert client.post('/api/auth/verificar-correo', json={'token': ['lista']}).status_code == 400


def test_en_la_base_solo_se_guarda_el_hash_del_token(client, app):
    _registro(client, 'laura@sanmateo.edu.co')
    token = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    filas = consultar(app, 'SELECT token_hash FROM tokens_usuario')
    assert len(filas) == 1
    assert filas[0]['token_hash'] != token
    assert token not in filas[0]['token_hash']


def test_reenviar_verificacion_invalida_el_enlace_anterior(client):
    _registro(client, 'laura@sanmateo.edu.co')
    viejo = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    assert client.post('/api/auth/reenviar-verificacion', json={'correo': 'laura@sanmateo.edu.co'}).status_code == 200
    nuevo = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    assert nuevo != viejo
    assert client.post('/api/auth/verificar-correo', json={'token': viejo}).status_code == 400
    assert client.post('/api/auth/verificar-correo', json={'token': nuevo}).status_code == 200


def test_reenviar_verificacion_no_revela_si_el_correo_existe(client):
    a = client.post('/api/auth/reenviar-verificacion', json={'correo': 'noexiste@sanmateo.edu.co'})
    _registro(client, 'laura@sanmateo.edu.co')
    b = client.post('/api/auth/reenviar-verificacion', json={'correo': 'laura@sanmateo.edu.co'})
    assert a.status_code == b.status_code == 200
    assert a.get_json() == b.get_json()


def test_login_con_credenciales_incorrectas_es_generico(client, estudiante_a):
    otro = client.post('/api/auth/login', json={'correo': 'noexiste@sanmateo.edu.co', 'contrasena': CONTRASENA})
    mala = client.post('/api/auth/login', json={'correo': 'ana.a@sanmateo.edu.co', 'contrasena': 'Mala$Clave2026x'})
    assert otro.status_code == mala.status_code == 401
    assert otro.get_json() == mala.get_json()


def test_cuenta_desactivada_no_puede_entrar(client, app, estudiante_a):
    ejecutar(app, "UPDATE usuarios SET activo = FALSE WHERE correo = 'ana.a@sanmateo.edu.co'")
    respuesta = client.post('/api/auth/login', json={'correo': 'ana.a@sanmateo.edu.co', 'contrasena': CONTRASENA})
    assert respuesta.status_code == 401
    # y la sesión que ya tenía abierta deja de servir
    assert estudiante_a.get('/api/mis-reportes').status_code == 401


def test_cookie_de_sesion_httponly_y_samesite(app, client):
    crear_cliente(app, 'laura@sanmateo.edu.co', iniciar_sesion=False)
    respuesta = client.post('/api/auth/login', json={'correo': 'laura@sanmateo.edu.co', 'contrasena': CONTRASENA})
    cookie = respuesta.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie
    assert 'SameSite=Lax' in cookie
    assert 'Expires' not in cookie  # cookie de sesión del navegador: se borra al cerrarlo


def test_la_sesion_solo_guarda_el_id_del_usuario(estudiante_a):
    with estudiante_a.session_transaction() as sesion:
        assert set(sesion.keys()) <= {'usuario_id', 'csrf_token', '_permanent'}
        assert isinstance(sesion['usuario_id'], int)


def test_pedir_recuperacion_dos_veces_invalida_el_primer_enlace(client, estudiante_a):
    client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'})
    primero = ultimo_token_en_correo('ana.a@sanmateo.edu.co', 'restablecer-contrasena.html')
    client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'})
    nueva = 'NuevaClave$Segura2027'
    respuesta = client.post('/api/auth/restablecer', json={'token': primero, 'contrasena': nueva, 'confirmar_contrasena': nueva})
    assert respuesta.status_code == 400


def test_sesion_y_logout(estudiante_a):
    assert estudiante_a.get('/api/auth/sesion').get_json()['usuario']['correo'] == 'ana.a@sanmateo.edu.co'
    assert estudiante_a.post('/api/auth/logout').status_code == 200
    assert estudiante_a.get('/api/auth/sesion').get_json()['usuario'] is None


def test_recuperacion_completa_y_token_de_un_solo_uso(client, estudiante_a):
    assert client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'}).status_code == 200
    token = ultimo_token_en_correo('ana.a@sanmateo.edu.co', 'restablecer-contrasena.html')
    assert token
    nueva = 'NuevaClave$Segura2027'
    respuesta = client.post('/api/auth/restablecer', json={'token': token, 'contrasena': nueva, 'confirmar_contrasena': nueva})
    assert respuesta.status_code == 200
    assert client.post('/api/auth/login', json={'correo': 'ana.a@sanmateo.edu.co', 'contrasena': nueva}).status_code == 200
    otra = 'OtraClave$Segura2028'
    reuso = client.post('/api/auth/restablecer', json={'token': token, 'contrasena': otra, 'confirmar_contrasena': otra})
    assert reuso.status_code == 400


def test_recuperacion_con_contrasena_debil_no_gasta_el_token(client, estudiante_a):
    client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'})
    token = ultimo_token_en_correo('ana.a@sanmateo.edu.co', 'restablecer-contrasena.html')
    debil = client.post('/api/auth/restablecer', json={'token': token, 'contrasena': 'corta', 'confirmar_contrasena': 'corta'})
    assert debil.status_code == 400
    nueva = 'NuevaClave$Segura2027'
    assert client.post('/api/auth/restablecer', json={
        'token': token, 'contrasena': nueva, 'confirmar_contrasena': nueva,
    }).status_code == 200


def test_recuperar_no_revela_si_el_correo_existe(client, estudiante_a):
    a = client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'})
    b = client.post('/api/auth/recuperar', json={'correo': 'noexiste@sanmateo.edu.co'})
    assert a.status_code == b.status_code == 200
    assert a.get_json() == b.get_json()


def test_token_de_verificacion_no_sirve_para_restablecer(client, app):
    crear_cliente(app, 'laura@sanmateo.edu.co', verificar=False, iniciar_sesion=False)
    token = ultimo_token_en_correo('laura@sanmateo.edu.co', 'verificar-correo.html')
    nueva = 'NuevaClave$Segura2027'
    respuesta = client.post('/api/auth/restablecer', json={'token': token, 'contrasena': nueva, 'confirmar_contrasena': nueva})
    assert respuesta.status_code == 400
