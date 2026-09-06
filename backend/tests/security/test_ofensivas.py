"""Pruebas ofensivas siguiendo el checklist de la skill
seguridad-ofensiva-defensiva. Todas corren SOLO contra el test client de
Flask (nunca contra un sistema de terceros)."""

import datetime

from app.extensions import db


def test_sql_injection_en_busqueda_no_rompe_nada(client):
    respuesta = client.get("/api/objetos?q=' OR '1'='1")
    assert respuesta.status_code == 200
    assert respuesta.get_json()['total'] == 0


def test_sql_injection_intento_drop_table(client, usuario_a):
    respuesta = client.get("/api/objetos?q='; DROP TABLE usuarios; --")
    assert respuesta.status_code == 200
    # Si la tabla hubiera sido borrada, esta petición fallaría con 500
    sesion = client.get('/api/auth/sesion')
    assert sesion.status_code == 200


def test_xss_almacenado_se_guarda_como_texto_plano(client, usuario_a):
    import datetime as dt
    payload = "<script>alert('XSS')</script>"
    respuesta = client.post('/api/objetos', json={
        'tipo': 'perdido', 'nombre': payload, 'categoria': 'Otro',
        'descripcion': 'Prueba de XSS almacenado con suficiente longitud de texto',
        'ubicacion': 'Test', 'fecha_evento': dt.date.today().isoformat(),
    })
    assert respuesta.status_code == 201
    # Se guarda literal (sin ejecutar ni modificar); escapar al mostrar es
    # responsabilidad del frontend (ver main.js: crearElemento usa textContent).
    assert respuesta.get_json()['objeto']['nombre'] == payload


def test_payload_json_extremadamente_grande_es_rechazado(client, usuario_a):
    descripcion_enorme = 'A' * (2 * 1024 * 1024)  # 2 MB > MAX_CONTENT_LENGTH (1 MB)
    respuesta = client.post('/api/objetos', json={
        'tipo': 'perdido', 'nombre': 'x', 'categoria': 'Otro',
        'descripcion': descripcion_enorme, 'ubicacion': 'x', 'fecha_evento': '2026-01-01',
    })
    assert respuesta.status_code == 413


def test_json_malformado_no_causa_error_500(client):
    respuesta = client.post(
        '/api/auth/login',
        data='esto no es json valido {{{',
        headers={'Content-Type': 'application/json'},
    )
    assert respuesta.status_code in (400, 401)
    assert respuesta.status_code != 500


def test_body_vacio_en_post_no_causa_error_500(client):
    respuesta = client.post('/api/auth/login', headers={'Content-Type': 'application/json'})
    assert respuesta.status_code != 500


def test_token_recuperacion_expirado_es_rechazado(client, app):
    client.post('/api/auth/registro', json={
        'primer_nombre': 'Test', 'primer_apellido': 'Usuario',
        'correo': 'expirado@sanmateo.edu.co',
        'contrasena': 'Prueba$Segura2026', 'confirmar_contrasena': 'Prueba$Segura2026',
    })
    client.post('/api/auth/recuperar', json={'correo': 'expirado@sanmateo.edu.co'})

    with app.app_context():
        from app.models.token_recuperacion import TokenRecuperacion
        registro = TokenRecuperacion.query.first()
        token = registro.token
        # Forzamos que ya haya expirado, sin esperar los 30 minutos reales.
        registro.expira_en = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        db.session.commit()

    respuesta = client.post('/api/auth/restablecer', json={
        'token': token, 'contrasena': 'NuevaClave$2026', 'confirmar_contrasena': 'NuevaClave$2026',
    })
    assert respuesta.status_code == 400


def test_token_recuperacion_de_otro_formato_es_rechazado(client):
    respuesta = client.post('/api/auth/restablecer', json={
        'token': "' OR '1'='1", 'contrasena': 'NuevaClave$2026', 'confirmar_contrasena': 'NuevaClave$2026',
    })
    assert respuesta.status_code == 400


def test_no_se_puede_acceder_a_recurso_de_otro_usuario_cambiando_el_id(client, usuario_a, cliente_b):
    import datetime as dt
    creado = client.post('/api/objetos', json={
        'tipo': 'perdido', 'nombre': 'Objeto de A', 'categoria': 'Otro',
        'descripcion': 'Descripción con longitud suficiente para pasar validación',
        'ubicacion': 'Test', 'fecha_evento': dt.date.today().isoformat(),
    }).get_json()['objeto']

    # IDOR clásico: B intenta editar el recurso de A solo cambiando el id en la URL
    respuesta = cliente_b.put(f"/api/objetos/{creado['id']}", json={'nombre': 'Robado'})
    assert respuesta.status_code == 403


def test_parametros_de_paginacion_maliciosos_no_rompen_nada(client):
    respuesta = client.get('/api/objetos?pagina=-1&por_pagina=99999999')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['por_pagina'] <= 50  # el máximo configurado, no lo que pidió el cliente


def test_parametros_de_paginacion_no_numericos_no_rompen_nada(client):
    respuesta = client.get('/api/objetos?pagina=abc&por_pagina=xyz')
    assert respuesta.status_code == 200
