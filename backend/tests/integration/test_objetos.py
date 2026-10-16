"""Reportes de objetos perdidos y encontrados: creación, visibilidad
(verificación a ciegas), edición con control de versión y cancelación."""

from datetime import timedelta

from app.utils import hoy_en_colombia
from tests.ayudantes import (
    consultar, crear_cliente, crear_reporte, ejecutar, objeto_en_oficina, recibir_en_oficina,
)


def test_crear_reporte_perdido_empieza_buscando(estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    assert objeto['estado'] == 'buscando'
    assert objeto['categoria'] == 'Tecnología'
    assert objeto['ubicacion'] == 'Biblioteca'
    assert objeto['descripcion']  # el dueño ve su propia descripción


def test_crear_reporte_encontrado_empieza_pendiente_de_entrega(estudiante_a):
    objeto = crear_reporte(estudiante_a, 'encontrado')
    assert objeto['estado'] == 'pendiente_entrega'


def test_crear_reporte_requiere_sesion(client):
    assert client.post('/api/objetos', json={'tipo': 'perdido'}).status_code == 401


def test_estudiante_sin_verificar_no_puede_reportar(app):
    # Caso límite: cuenta verificada que luego pierde la verificación
    cliente = crear_cliente(app, 'sinverificar@sanmateo.edu.co')
    ejecutar(app, "UPDATE usuarios SET correo_verificado_en = NULL WHERE correo = 'sinverificar@sanmateo.edu.co'")
    respuesta = cliente.post('/api/objetos', json={'tipo': 'perdido'})
    assert respuesta.status_code == 400
    assert 'correo' in respuesta.get_json()['errores']


def test_validaciones_de_reporte(estudiante_a):
    manana = (hoy_en_colombia() + timedelta(days=1)).isoformat()
    respuesta = estudiante_a.post('/api/objetos', json={
        'tipo': 'robado', 'nombre': 'x', 'categoria_id': 999, 'ubicacion_id': 'abc',
        'descripcion': 'corta', 'fecha_evento': manana,
    })
    assert respuesta.status_code == 400
    errores = respuesta.get_json()['errores']
    for campo in ('tipo', 'nombre', 'categoria_id', 'ubicacion_id', 'descripcion', 'fecha_evento'):
        assert campo in errores


def test_categoria_desactivada_no_se_puede_usar(app, estudiante_a):
    ejecutar(app, 'UPDATE categorias SET activa = FALSE WHERE id = 1')
    respuesta = estudiante_a.post('/api/objetos', json={
        'tipo': 'perdido', 'nombre': 'Celular', 'categoria_id': 1, 'ubicacion_id': 1,
        'descripcion': 'Descripción suficientemente larga', 'fecha_evento': hoy_en_colombia().isoformat(),
    })
    assert respuesta.status_code == 400
    assert 'categoria_id' in respuesta.get_json()['errores']


def test_objeto_encontrado_no_aparece_en_busqueda_hasta_llegar_a_la_oficina(estudiante_a, estudiante_b, encargado):
    objeto = crear_reporte(estudiante_a, 'encontrado')
    assert estudiante_b.get('/api/objetos').get_json()['total'] == 0
    recibir_en_oficina(encargado, objeto['id'])
    resultado = estudiante_b.get('/api/objetos').get_json()
    assert resultado['total'] == 1
    assert resultado['datos'][0]['estado'] == 'en_oficina'


def test_busqueda_no_muestra_la_descripcion_privada(estudiante_a, estudiante_b, encargado):
    objeto_en_oficina(estudiante_a, encargado)
    publico = estudiante_b.get('/api/objetos').get_json()['datos'][0]
    assert 'descripcion' not in publico
    assert 'detalle_ubicacion' not in publico
    assert 'reportado_por' not in publico
    assert 'Pokémon' not in str(publico)


def test_detalle_para_otro_estudiante_es_solo_publico(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    datos = estudiante_b.get(f"/api/objetos/{objeto['id']}").get_json()
    assert datos['es_propio'] is False
    assert 'descripcion' not in datos['objeto']


def test_detalle_para_el_dueno_incluye_su_descripcion(estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    datos = estudiante_a.get(f"/api/objetos/{objeto['id']}").get_json()
    assert datos['es_propio'] is True
    assert 'Pokémon' in datos['objeto']['descripcion']


def test_reporte_de_perdida_ajeno_no_es_visible(estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'perdido')
    assert estudiante_b.get(f"/api/objetos/{objeto['id']}").status_code == 403


def test_objeto_pendiente_de_entrega_ajeno_no_es_visible(estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'encontrado')
    assert estudiante_b.get(f"/api/objetos/{objeto['id']}").status_code == 403


def test_encargado_ve_todo_el_detalle(estudiante_a, encargado):
    objeto = crear_reporte(estudiante_a, 'perdido')
    datos = encargado.get(f"/api/objetos/{objeto['id']}").get_json()['objeto']
    assert 'Pokémon' in datos['descripcion']
    assert datos['reportado_por']['correo'] == 'ana.a@sanmateo.edu.co'


def test_busqueda_por_texto_y_filtros(estudiante_a, estudiante_b, encargado):
    objeto_en_oficina(estudiante_a, encargado, nombre='Chaqueta azul', categoria_id=5)
    objeto_en_oficina(estudiante_a, encargado, nombre='Celular')
    assert estudiante_b.get('/api/objetos?q=chaq').get_json()['total'] == 1
    assert estudiante_b.get('/api/objetos?categoria_id=5').get_json()['total'] == 1
    assert estudiante_b.get('/api/objetos?q=100%25').get_json()['total'] == 0  # "%" se busca literal


def test_busqueda_no_filtra_por_la_descripcion_privada(estudiante_a, estudiante_b, encargado):
    objeto_en_oficina(estudiante_a, encargado)
    # "Pokémon" solo aparece en la descripción privada: buscarlo no debe
    # revelar que existe un objeto con ese detalle.
    assert estudiante_b.get('/api/objetos?q=Pokémon').get_json()['total'] == 0


def test_editar_reporte_propio_con_version(estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    respuesta = estudiante_a.put(f"/api/objetos/{objeto['id']}", json={
        'version': objeto['version'], 'nombre': 'Celular Samsung', 'categoria_id': 1, 'ubicacion_id': 2,
        'descripcion': 'Samsung negro con funda de Pokémon', 'fecha_evento': objeto['fecha_evento'],
    })
    assert respuesta.status_code == 200
    editado = respuesta.get_json()['objeto']
    assert editado['nombre'] == 'Celular Samsung'
    assert editado['version'] == objeto['version'] + 1


def test_editar_con_version_vieja_devuelve_conflicto(estudiante_a):
    """Concurrencia optimista: dos pestañas editan el mismo reporte; la
    segunda en guardar recibe 409 en vez de pisar el cambio de la primera."""
    objeto = crear_reporte(estudiante_a, 'perdido')
    cambios = {'nombre': 'Celular viejo', 'categoria_id': 1, 'ubicacion_id': 1,
               'descripcion': 'Descripción actualizada del celular', 'fecha_evento': objeto['fecha_evento']}
    primera = estudiante_a.put(f"/api/objetos/{objeto['id']}", json=dict(cambios, version=objeto['version']))
    segunda = estudiante_a.put(f"/api/objetos/{objeto['id']}", json=dict(cambios, version=objeto['version']))
    assert primera.status_code == 200
    assert segunda.status_code == 409


def test_editar_reporte_ajeno_esta_prohibido(estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'perdido')
    respuesta = estudiante_b.put(f"/api/objetos/{objeto['id']}", json={'version': 1, 'nombre': 'Hackeado'})
    assert respuesta.status_code == 403


def test_no_se_edita_un_objeto_que_ya_esta_en_la_oficina(estudiante_a, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    respuesta = estudiante_a.put(f"/api/objetos/{objeto['id']}", json={'version': objeto['version'], 'nombre': 'Otro'})
    assert respuesta.status_code == 400


def test_editar_ignora_campos_no_permitidos(app, estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'perdido')
    estudiante_a.put(f"/api/objetos/{objeto['id']}", json={
        'version': objeto['version'], 'nombre': 'Celular', 'categoria_id': 1, 'ubicacion_id': 1,
        'descripcion': 'Descripción suficientemente larga', 'fecha_evento': objeto['fecha_evento'],
        'estado': 'recuperado', 'usuario_id': estudiante_b.usuario['id'], 'tipo': 'encontrado',
    })
    fila = consultar(app, 'SELECT estado, usuario_id, tipo FROM objetos WHERE id = :id', id=objeto['id'])[0]
    assert fila == {'estado': 'buscando', 'usuario_id': estudiante_a.usuario['id'], 'tipo': 'perdido'}


def test_cancelar_reporte(estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    respuesta = estudiante_a.post(f"/api/objetos/{objeto['id']}/cancelar")
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['estado'] == 'cancelado'
    # Un estado final no se puede volver a cancelar
    assert estudiante_a.post(f"/api/objetos/{objeto['id']}/cancelar").status_code == 400


def test_no_se_cancela_un_objeto_en_custodia(estudiante_a, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    assert estudiante_a.post(f"/api/objetos/{objeto['id']}/cancelar").status_code == 400


def test_mis_reportes_solo_muestra_los_propios(estudiante_a, estudiante_b):
    crear_reporte(estudiante_a, 'perdido')
    crear_reporte(estudiante_b, 'perdido')
    datos = estudiante_a.get('/api/mis-reportes').get_json()
    assert datos['total'] == 1
    assert estudiante_a.get('/api/mis-reportes?tipo=encontrado').get_json()['total'] == 0


def test_coincidencias_para_un_reporte_de_perdida(app, estudiante_a, estudiante_b, encargado):
    perdido = crear_reporte(estudiante_b, 'perdido', nombre='Celular Samsung')
    encontrado = objeto_en_oficina(estudiante_a, encargado, nombre='Celular')
    datos = estudiante_b.get(f"/api/objetos/{perdido['id']}/coincidencias").get_json()['datos']
    assert len(datos) == 1
    assert 'descripcion' not in datos[0]
    # Una coincidencia es solo una pista: no cambia el estado de ningún objeto
    estados = {f['id']: f['estado'] for f in consultar(app, 'SELECT id, estado FROM objetos')}
    assert estados == {perdido['id']: 'buscando', encontrado['id']: 'en_oficina'}


def test_al_recibir_un_objeto_se_avisa_a_quien_reporto_algo_parecido(app, estudiante_a, estudiante_b, encargado):
    crear_reporte(estudiante_b, 'perdido')
    objeto_en_oficina(estudiante_a, encargado)
    avisos = consultar(app, "SELECT usuario_id FROM notificaciones WHERE tipo = 'posible_coincidencia'")
    assert [a['usuario_id'] for a in avisos] == [estudiante_b.usuario['id']]
