"""Panel del administrador: usuarios y roles, catálogos, parámetros,
auditoría, estadísticas y exportación."""

from tests.ayudantes import consultar, crear_cliente, crear_reporte, entregar, generar_codigo, objeto_reservado


# --- Usuarios y roles ---------------------------------------------------------

def test_admin_lista_y_filtra_usuarios(admin, estudiante_a, encargado):
    assert admin.get('/api/admin/usuarios').get_json()['total'] == 3
    encargados = admin.get('/api/admin/usuarios?rol=encargado').get_json()['datos']
    assert [u['correo'] for u in encargados] == ['elena.encargada@sanmateo.edu.co']
    assert admin.get('/api/admin/usuarios?q=ana.a').get_json()['total'] == 1


def test_admin_nombra_encargado_y_se_le_avisa(app, admin, estudiante_a):
    respuesta = admin.put(f"/api/admin/usuarios/{estudiante_a.usuario['id']}", json={'rol': 'encargado'})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['rol'] == 'encargado'
    avisos = consultar(app, "SELECT tipo FROM notificaciones WHERE usuario_id = :id", id=estudiante_a.usuario['id'])
    assert {'tipo': 'rol_cambiado'} in avisos


def test_desde_la_web_no_se_crean_administradores(admin, estudiante_a):
    respuesta = admin.put(f"/api/admin/usuarios/{estudiante_a.usuario['id']}", json={'rol': 'administrador'})
    assert respuesta.status_code == 400


def test_admin_no_se_modifica_a_si_mismo(admin):
    respuesta = admin.put(f"/api/admin/usuarios/{admin.usuario['id']}", json={'activo': False})
    assert respuesta.status_code == 400


def test_admin_no_modifica_a_otro_admin(app, admin):
    otro = crear_cliente(app, 'otro.admin@sanmateo.edu.co', rol='administrador')
    respuesta = admin.put(f"/api/admin/usuarios/{otro.usuario['id']}", json={'activo': False})
    assert respuesta.status_code == 400


def test_solo_cuentas_verificadas_pueden_ser_encargado(app, admin):
    crear_cliente(app, 'sinverificar@sanmateo.edu.co', verificar=False, iniciar_sesion=False)
    usuario_id = consultar(app, "SELECT id FROM usuarios WHERE correo = 'sinverificar@sanmateo.edu.co'")[0]['id']
    respuesta = admin.put(f'/api/admin/usuarios/{usuario_id}', json={'rol': 'encargado'})
    assert respuesta.status_code == 400


def test_whitelist_al_actualizar_usuario(app, admin, estudiante_a):
    admin.put(f"/api/admin/usuarios/{estudiante_a.usuario['id']}",
              json={'activo': True, 'correo': 'robado@sanmateo.edu.co', 'password_hash': 'x'})
    fila = consultar(app, 'SELECT correo FROM usuarios WHERE id = :id', id=estudiante_a.usuario['id'])[0]
    assert fila['correo'] == 'ana.a@sanmateo.edu.co'


def test_desactivar_usuario(admin, estudiante_a):
    respuesta = admin.put(f"/api/admin/usuarios/{estudiante_a.usuario['id']}", json={'activo': False})
    assert respuesta.status_code == 200
    assert estudiante_a.get('/api/mis-reportes').status_code == 401


# --- Catálogos y parámetros -----------------------------------------------------

def test_crear_y_renombrar_categoria(admin, estudiante_a):
    respuesta = admin.post('/api/admin/categorias', json={'nombre': 'Instrumentos musicales'})
    assert respuesta.status_code == 201
    categoria = respuesta.get_json()['categoria']

    objeto = crear_reporte(estudiante_a, 'perdido', categoria_id=categoria['id'])
    admin.put(f"/api/admin/categorias/{categoria['id']}", json={'nombre': 'Instrumentos'})
    # Normalización: el reporte muestra el nombre nuevo sin haberlo tocado
    detalle = estudiante_a.get(f"/api/objetos/{objeto['id']}").get_json()['objeto']
    assert detalle['categoria'] == 'Instrumentos'


def test_categoria_con_nombre_repetido(admin):
    respuesta = admin.post('/api/admin/categorias', json={'nombre': 'tecnología'})  # ya existe "Tecnología"
    assert respuesta.status_code == 409
    assert 'Ya existe' in respuesta.get_json()['mensaje']


def test_categoria_desactivada_no_sale_en_los_formularios(admin, estudiante_a):
    admin.put('/api/admin/categorias/1', json={'activa': False})
    nombres = [c['nombre'] for c in estudiante_a.get('/api/catalogos').get_json()['categorias']]
    assert 'Tecnología' not in nombres


def test_crear_ubicacion(admin, estudiante_a):
    respuesta = admin.post('/api/admin/ubicaciones', json={'nombre': 'Gimnasio', 'descripcion': 'Bloque deportivo'})
    assert respuesta.status_code == 201
    nombres = [u['nombre'] for u in estudiante_a.get('/api/catalogos').get_json()['ubicaciones']]
    assert 'Gimnasio' in nombres


def test_parametros_respetan_su_rango(admin):
    assert admin.put('/api/admin/parametros/max_solicitudes_abiertas', json={'valor': 5}).status_code == 200
    assert admin.put('/api/admin/parametros/max_solicitudes_abiertas', json={'valor': 500}).status_code == 400
    assert admin.put('/api/admin/parametros/max_solicitudes_abiertas', json={'valor': '5'}).status_code == 400
    assert admin.put('/api/admin/parametros/no_existe', json={'valor': 1}).status_code == 404


# --- Auditoría, estadísticas y exportación --------------------------------------

def test_auditoria_filtrada_por_registro(admin, estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    datos = admin.get(f"/api/admin/auditoria?tabla=objetos&registro_id={objeto['id']}").get_json()['datos']
    assert len(datos) == 1
    fila = datos[0]
    assert fila['operacion'] == 'INSERT'
    assert fila['usuario_nombre'] == 'Ana Acosta'
    assert fila['ip'] == '127.0.0.1'


def test_auditoria_no_expone_hashes(admin, estudiante_a):
    datos = admin.get('/api/admin/auditoria?tabla=usuarios').get_json()['datos']
    assert datos
    assert all('password_hash' not in (fila['datos_nuevos'] or {}) for fila in datos)


def test_cambio_de_contrasena_queda_auditado_sin_el_hash(app, admin, estudiante_a, client):
    from tests.ayudantes import ultimo_token_en_correo
    client.post('/api/auth/recuperar', json={'correo': 'ana.a@sanmateo.edu.co'})
    token = ultimo_token_en_correo('ana.a@sanmateo.edu.co', 'restablecer-contrasena.html')
    nueva = 'NuevaClave$Segura2027'
    client.post('/api/auth/restablecer', json={'token': token, 'contrasena': nueva, 'confirmar_contrasena': nueva})
    filas = consultar(app, """SELECT campos_modificados, datos_nuevos FROM auditoria
                              WHERE tabla = 'usuarios' AND operacion = 'UPDATE' AND 'password_hash' = ANY (campos_modificados)""")
    assert len(filas) == 1
    assert 'password_hash' not in filas[0]['datos_nuevos']


def test_estadisticas_del_admin(admin, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    entregar(encargado, objeto['id'], generar_codigo(estudiante_b, solicitud['id']))
    datos = admin.get('/api/admin/estadisticas').get_json()
    assert datos['generales']['entregados'] == 1
    assert datos['mensuales'][-1]['entregados'] == 1
    elena = [e for e in datos['encargados'] if e['correo'] == 'elena.encargada@sanmateo.edu.co'][0]
    assert elena['objetos_recibidos'] == 1 and elena['entregas'] == 1 and elena['preaprobaciones'] == 1


def test_exportar_csv_sin_datos_personales_y_seguro_para_excel(admin, estudiante_a):
    crear_reporte(estudiante_a, 'perdido', nombre='=HYPERLINK("http://malo")')
    respuesta = admin.get('/api/admin/exportar/objetos.csv')
    assert respuesta.status_code == 200
    assert respuesta.mimetype == 'text/csv'
    contenido = respuesta.get_data(as_text=True)
    assert contenido.startswith('﻿')            # BOM para que Excel lea las tildes
    assert '\'=HYPERLINK' in contenido               # fórmula neutralizada
    assert 'ana.a@sanmateo.edu.co' not in contenido   # sin correos
    assert 'Pokémon' not in contenido                 # sin descripciones privadas


def test_estadisticas_publicas_solo_numeros(client, estudiante_a, encargado):
    from tests.ayudantes import objeto_en_oficina
    objeto_en_oficina(estudiante_a, encargado)
    datos = client.get('/api/estadisticas/publicas').get_json()
    assert datos == {'en_custodia': 1, 'entregados': 0}
