"""Pruebas ofensivas siguiendo el checklist de la skill
seguridad-ofensiva-defensiva. Todas corren SOLO contra el test client de
Flask y la base de datos de pruebas (nunca contra un sistema de terceros)."""

from tests.ayudantes import consultar, crear_reporte, objeto_en_oficina, objeto_reservado, reclamar


# --- Inyección SQL ------------------------------------------------------------

def test_sql_injection_en_busqueda_no_rompe_nada(estudiante_a):
    respuesta = estudiante_a.get("/api/objetos?q=' OR '1'='1")
    assert respuesta.status_code == 200
    assert respuesta.get_json()['total'] == 0


def test_sql_injection_intento_drop_table(app, estudiante_a):
    respuesta = estudiante_a.get("/api/objetos?q='; DROP TABLE usuarios; --")
    assert respuesta.status_code == 200
    assert consultar(app, 'SELECT count(*) AS n FROM usuarios')[0]['n'] == 1


def test_sql_injection_en_filtros_numericos(estudiante_a):
    respuesta = estudiante_a.get('/api/objetos?categoria_id=1 OR 1=1&ubicacion_id=1;DROP TABLE objetos')
    assert respuesta.status_code == 200


def test_sql_injection_en_filtros_de_auditoria(admin):
    respuesta = admin.get("/api/admin/auditoria?tabla=usuarios' OR '1'='1&registro_id=1 OR 1=1")
    assert respuesta.status_code == 200


def test_parametros_de_paginacion_maliciosos(estudiante_a):
    for consulta in ('pagina=-5&por_pagina=99999', 'pagina=abc&por_pagina=xyz', 'pagina=1e9', 'por_pagina=0'):
        respuesta = estudiante_a.get(f'/api/objetos?{consulta}')
        assert respuesta.status_code == 200
        assert 1 <= respuesta.get_json()['por_pagina'] <= 50
        assert respuesta.get_json()['pagina'] >= 1


# --- XSS ----------------------------------------------------------------------

def test_xss_almacenado_se_guarda_como_texto_plano(estudiante_a):
    payload = "<script>alert('XSS')</script>"
    objeto = crear_reporte(estudiante_a, 'perdido', nombre=payload)
    # Se guarda literal (sin ejecutar ni modificar); escapar al mostrar es
    # responsabilidad del frontend (main.js usa textContent, nunca innerHTML).
    assert objeto['nombre'] == payload


# --- Tamaño y formato de las peticiones ----------------------------------------

def test_payload_json_extremadamente_grande_es_rechazado(estudiante_a):
    respuesta = estudiante_a.post('/api/objetos', json={'tipo': 'perdido', 'descripcion': 'A' * (2 * 1024 * 1024)})
    assert respuesta.status_code == 413


def test_json_malformado_no_causa_error_500(client):
    respuesta = client.post('/api/auth/login', data='esto no es json valido {{{',
                            headers={'Content-Type': 'application/json'})
    assert respuesta.status_code in (400, 401)


def test_json_que_no_es_un_objeto_no_causa_error_500(estudiante_a):
    for cuerpo in ('[1, 2, 3]', '"texto"', '123', 'null'):
        respuesta = estudiante_a.post('/api/objetos', data=cuerpo, headers={'Content-Type': 'application/json'})
        assert respuesta.status_code == 400


def test_tipos_inesperados_en_los_campos(estudiante_a):
    respuesta = estudiante_a.post('/api/objetos', json={
        'tipo': ['perdido'], 'nombre': {'$gt': ''}, 'categoria_id': True, 'ubicacion_id': [1],
        'descripcion': 12345, 'fecha_evento': {'a': 1},
    })
    assert respuesta.status_code == 400


def test_texto_demasiado_largo_no_causa_error_500(estudiante_a, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    respuesta = encargado.post(f"/api/encargado/objetos/{objeto['id']}/cerrar", json={'motivo': 'x' * 5000})
    assert respuesta.status_code == 400


# --- Mass assignment ------------------------------------------------------------

def test_mass_assignment_al_crear_reporte(app, estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'encontrado', estado='en_oficina', usuario_id=estudiante_b.usuario['id'],
                           recibido_por_id=estudiante_a.usuario['id'], version=99)
    fila = consultar(app, 'SELECT estado, usuario_id, recibido_por_id, version FROM objetos WHERE id = :id', id=objeto['id'])[0]
    assert fila == {'estado': 'pendiente_entrega', 'usuario_id': estudiante_a.usuario['id'],
                    'recibido_por_id': None, 'version': 1}


def test_mass_assignment_al_reclamar(app, estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id'], estado='preaprobada', solicitante_id=estudiante_a.usuario['id'],
                         intentos_codigo=0, codigo_hash='0' * 64).get_json()['solicitud']
    fila = consultar(app, 'SELECT estado, solicitante_id, codigo_hash FROM solicitudes WHERE id = :id', id=solicitud['id'])[0]
    assert fila == {'estado': 'pendiente', 'solicitante_id': estudiante_b.usuario['id'], 'codigo_hash': None}


# --- IDOR (acceso a recursos ajenos cambiando el id) ------------------------------

def test_idor_reporte_de_perdida_ajeno(estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'perdido')
    assert estudiante_b.get(f"/api/objetos/{objeto['id']}").status_code == 403
    assert estudiante_b.get(f"/api/objetos/{objeto['id']}/coincidencias").status_code == 403
    assert estudiante_b.post(f"/api/objetos/{objeto['id']}/cancelar").status_code == 403


def test_idor_codigo_de_retiro_ajeno(estudiante_a, estudiante_b, estudiante_c, encargado):
    _, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    assert estudiante_c.post(f"/api/solicitudes/{solicitud['id']}/codigo").status_code == 403
    assert estudiante_c.post(f"/api/solicitudes/{solicitud['id']}/cancelar").status_code == 403


def test_idor_ids_inexistentes_responden_404(estudiante_a):
    assert estudiante_a.get('/api/objetos/999999').status_code == 404
    assert estudiante_a.post('/api/solicitudes/999999/cancelar').status_code == 404


# --- Fuga de información -----------------------------------------------------------

def test_la_api_nunca_devuelve_hashes(admin, estudiante_a):
    for ruta in ('/api/auth/sesion', '/api/admin/usuarios', '/api/admin/auditoria?tabla=usuarios'):
        cliente = admin if 'admin' in ruta else estudiante_a
        cuerpo = cliente.get(ruta).get_data(as_text=True)
        assert 'password_hash' not in cuerpo
        assert '$argon2' not in cuerpo


def test_errores_no_exponen_detalles_internos(estudiante_a):
    respuesta = estudiante_a.get('/api/objetos/abc')
    assert respuesta.status_code == 404
    cuerpo = respuesta.get_data(as_text=True)
    assert 'Traceback' not in cuerpo and 'sqlalchemy' not in cuerpo.lower()


# --- Cabeceras de seguridad -----------------------------------------------------

def test_cabeceras_de_seguridad(client):
    respuesta = client.get('/api/auth/sesion')
    assert respuesta.headers['X-Content-Type-Options'] == 'nosniff'
    assert respuesta.headers['X-Frame-Options'] == 'DENY'
    assert "script-src 'self'" in respuesta.headers['Content-Security-Policy']
    assert "'unsafe-inline'" not in respuesta.headers['Content-Security-Policy']
    assert respuesta.headers['Cache-Control'] == 'no-store'


def test_health_no_revela_informacion(client):
    assert client.get('/health').get_json() == {'estado': 'ok'}
