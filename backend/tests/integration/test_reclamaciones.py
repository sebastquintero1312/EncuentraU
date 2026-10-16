"""Proceso completo de reclamación y las medidas contra reclamaciones falsas:
verificación a ciegas, límites, pre-aprobación, código de retiro de un solo
uso, entrega presencial y vencimiento."""

from tests.ayudantes import (
    consultar, crear_reporte, ejecutar, entregar, generar_codigo, objeto_en_oficina,
    objeto_reservado, preaprobar, reclamar,
)
from app.services.correo_service import CORREOS_ENVIADOS


# --- Flujo completo ---------------------------------------------------------

def test_flujo_completo_hasta_la_entrega(app, estudiante_a, estudiante_b, encargado):
    perdido = crear_reporte(estudiante_b, 'perdido')
    objeto = objeto_en_oficina(estudiante_a, encargado)

    respuesta = reclamar(estudiante_b, objeto['id'], reporte_perdida_id=perdido['id'])
    assert respuesta.status_code == 201
    solicitud = respuesta.get_json()['solicitud']
    assert solicitud['estado'] == 'pendiente'

    assert preaprobar(encargado, solicitud['id']).status_code == 200
    assert consultar(app, 'SELECT estado FROM objetos WHERE id = :id', id=objeto['id'])[0]['estado'] == 'reservado'

    codigo = generar_codigo(estudiante_b, solicitud['id'])
    respuesta = entregar(encargado, objeto['id'], codigo)
    assert respuesta.status_code == 200, respuesta.get_json()

    estados = consultar(app, '''
        SELECT (SELECT estado FROM objetos WHERE id = :o) AS objeto,
               (SELECT estado FROM solicitudes WHERE id = :s) AS solicitud,
               (SELECT estado FROM objetos WHERE id = :p) AS perdido,
               (SELECT count(*) FROM entregas WHERE objeto_id = :o) AS entregas
    ''', o=objeto['id'], s=solicitud['id'], p=perdido['id'])[0]
    assert estados == {'objeto': 'entregado', 'solicitud': 'entregada', 'perdido': 'recuperado', 'entregas': 1}

    # Avisos por correo: al dueño ("si no fuiste tú...") y a quien lo encontró
    asuntos = [(c['para'], c['asunto']) for c in CORREOS_ENVIADOS]
    assert ('beto.b@sanmateo.edu.co', 'EncuentraU: Retiraste tu objeto') in asuntos
    assert ('ana.a@sanmateo.edu.co', 'EncuentraU: El objeto que encontraste volvió a su dueño') in asuntos


def test_entrega_descarta_las_demas_reclamaciones(app, estudiante_a, estudiante_b, estudiante_c, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    s_b = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    s_c = reclamar(estudiante_c, objeto['id']).get_json()['solicitud']
    preaprobar(encargado, s_b['id'])
    entregar(encargado, objeto['id'], generar_codigo(estudiante_b, s_b['id']))
    estado_c = consultar(app, 'SELECT estado FROM solicitudes WHERE id = :id', id=s_c['id'])[0]['estado']
    assert estado_c == 'descartada'
    # "descartada" no cuenta como rechazo contra el estudiante
    assert consultar(app, 'SELECT marcado_revision FROM usuarios WHERE id = :id',
                     id=estudiante_c.usuario['id'])[0]['marcado_revision'] is False


# --- Verificación a ciegas --------------------------------------------------

def test_el_reclamante_nunca_ve_la_descripcion_privada(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    reclamar(estudiante_b, objeto['id'])
    mias = estudiante_b.get('/api/mis-solicitudes').get_json()['datos']
    assert 'descripcion' not in mias[0]['objeto']
    assert 'Pokémon' not in str(mias[0]['objeto'])


def test_el_encargado_compara_reclamacion_con_detalles_privados(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    detalle = encargado.get(f"/api/encargado/solicitudes/{solicitud['id']}").get_json()['solicitud']
    assert 'Pokémon' in detalle['objeto']['descripcion']      # lo que se sabe del objeto
    assert 'funda de Pokémon' in detalle['descripcion']        # lo que dijo el estudiante
    assert detalle['solicitante']['correo'] == 'beto.b@sanmateo.edu.co'


def test_reporte_de_perdida_previo_es_evidencia(app, estudiante_a, estudiante_b, encargado):
    from datetime import timedelta
    from app.utils import hoy_en_colombia
    perdido = crear_reporte(estudiante_b, 'perdido', fecha_evento=(hoy_en_colombia() - timedelta(days=3)).isoformat())
    # Simula que la pérdida se reportó 2 días antes de que apareciera el objeto
    ejecutar(app, "UPDATE objetos SET created_at = created_at - interval '2 days' WHERE id = :id", id=perdido['id'])
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id'], reporte_perdida_id=perdido['id']).get_json()['solicitud']
    detalle = encargado.get(f"/api/encargado/solicitudes/{solicitud['id']}").get_json()['solicitud']
    assert detalle['dias_reporte_previo'] == 2


def test_no_se_puede_vincular_un_reporte_de_perdida_ajeno(estudiante_a, estudiante_b, estudiante_c, encargado):
    perdido_de_c = crear_reporte(estudiante_c, 'perdido')
    objeto = objeto_en_oficina(estudiante_a, encargado)
    respuesta = reclamar(estudiante_b, objeto['id'], reporte_perdida_id=perdido_de_c['id'])
    assert respuesta.status_code == 400
    assert 'reporte_perdida_id' in respuesta.get_json()['errores']


# --- Qué se puede reclamar --------------------------------------------------

def test_no_se_puede_reclamar_lo_que_uno_mismo_encontro(estudiante_a, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    assert reclamar(estudiante_a, objeto['id']).status_code == 400


def test_no_se_puede_reclamar_un_objeto_que_no_esta_en_la_oficina(estudiante_a, estudiante_b):
    objeto = crear_reporte(estudiante_a, 'encontrado')  # pendiente de entrega
    assert reclamar(estudiante_b, objeto['id']).status_code == 400


def test_no_se_puede_reclamar_un_reporte_de_perdida(estudiante_a, estudiante_b):
    perdido = crear_reporte(estudiante_a, 'perdido')
    assert reclamar(estudiante_b, perdido['id']).status_code == 400


def test_validaciones_de_la_reclamacion(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    respuesta = reclamar(estudiante_b, objeto['id'], descripcion='mío', lugar_perdida='', fecha_perdida='ayer')
    assert respuesta.status_code == 400
    errores = respuesta.get_json()['errores']
    assert {'descripcion', 'lugar_perdida', 'fecha_perdida'} <= set(errores)


def test_una_sola_reclamacion_abierta_por_objeto(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    assert reclamar(estudiante_b, objeto['id']).status_code == 201
    assert reclamar(estudiante_b, objeto['id']).status_code == 400


def test_maximo_de_reclamaciones_abiertas(estudiante_a, estudiante_b, encargado):
    objetos = [objeto_en_oficina(estudiante_a, encargado, nombre=f'Objeto {i}') for i in range(4)]
    for objeto in objetos[:3]:
        assert reclamar(estudiante_b, objeto['id']).status_code == 201
    respuesta = reclamar(estudiante_b, objetos[3]['id'])
    assert respuesta.status_code == 400
    assert 'máximo' in respuesta.get_json()['errores']['cuenta']


def test_el_limite_tambien_lo_exige_la_base_de_datos(app, estudiante_a, estudiante_b, encargado):
    """Defensa en profundidad: aunque Python no revisara el límite, el trigger
    trg_solicitudes_validar_nueva lo rechazaría."""
    objetos = [objeto_en_oficina(estudiante_a, encargado, nombre=f'Objeto {i}') for i in range(4)]
    for objeto in objetos[:3]:
        reclamar(estudiante_b, objeto['id'])
    import pytest
    from sqlalchemy.exc import DBAPIError
    with pytest.raises(DBAPIError) as error:
        ejecutar(app, '''
            INSERT INTO solicitudes (objeto_id, solicitante_id, descripcion, lugar_perdida, fecha_perdida)
            VALUES (:o, :u, 'Descripción directa insertada por SQL', 'Biblioteca', CURRENT_DATE)
        ''', o=objetos[3]['id'], u=estudiante_b.usuario['id'])
    assert 'máximo' in str(error.value.orig)


# --- Rechazos y cuentas en revisión -----------------------------------------

def test_rechazo_requiere_motivo(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    respuesta = encargado.post(f"/api/encargado/solicitudes/{solicitud['id']}/rechazar", json={'motivo': ''})
    assert respuesta.status_code == 400


def test_tres_rechazos_ponen_la_cuenta_en_revision(app, estudiante_a, estudiante_b, encargado, admin):
    for i in range(3):
        objeto = objeto_en_oficina(estudiante_a, encargado, nombre=f'Objeto {i}')
        solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
        respuesta = encargado.post(f"/api/encargado/solicitudes/{solicitud['id']}/rechazar",
                                   json={'motivo': 'La descripción no coincide'})
        assert respuesta.status_code == 200

    fila = consultar(app, 'SELECT marcado_revision, motivo_revision FROM usuarios WHERE id = :id',
                     id=estudiante_b.usuario['id'])[0]
    assert fila['marcado_revision'] is True
    assert '3 reclamaciones rechazadas' in fila['motivo_revision']

    # El administrador recibe el aviso...
    avisos = consultar(app, "SELECT usuario_id FROM notificaciones WHERE tipo = 'cuenta_en_revision'")
    assert [a['usuario_id'] for a in avisos] == [admin.usuario['id']]

    # ...y el estudiante no puede reclamar más hasta que lo revisen
    objeto = objeto_en_oficina(estudiante_a, encargado, nombre='Otro objeto')
    assert reclamar(estudiante_b, objeto['id']).status_code == 400

    assert admin.post(f"/api/admin/usuarios/{estudiante_b.usuario['id']}/quitar-revision").status_code == 200
    assert reclamar(estudiante_b, objeto['id']).status_code == 201


def test_rechazar_una_preaprobada_libera_el_objeto(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    encargado.post(f"/api/encargado/solicitudes/{solicitud['id']}/rechazar", json={'motivo': 'No trajo prueba'})
    assert consultar(app, 'SELECT estado FROM objetos WHERE id = :id', id=objeto['id'])[0]['estado'] == 'en_oficina'


def test_solo_una_preaprobada_por_objeto(estudiante_a, estudiante_b, estudiante_c, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    s_b = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    s_c = reclamar(estudiante_c, objeto['id']).get_json()['solicitud']
    assert preaprobar(encargado, s_b['id']).status_code == 200
    segunda = preaprobar(encargado, s_c['id'])
    assert segunda.status_code == 409
    assert 'pre-aprobada' in segunda.get_json()['mensaje']


# --- Código de retiro y entrega ---------------------------------------------

def test_el_codigo_no_se_guarda_en_claro(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    codigo = generar_codigo(estudiante_b, solicitud['id'])
    fila = consultar(app, 'SELECT codigo_hash FROM solicitudes WHERE id = :id', id=solicitud['id'])[0]
    assert len(fila['codigo_hash']) == 64
    assert codigo not in fila['codigo_hash']
    # Y la auditoría tampoco guarda el hash
    auditoria = consultar(app, "SELECT datos_nuevos FROM auditoria WHERE tabla = 'solicitudes'")
    assert all('codigo_hash' not in (fila['datos_nuevos'] or {}) for fila in auditoria)


def test_no_se_genera_codigo_sin_preaprobacion(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    assert estudiante_b.post(f"/api/solicitudes/{solicitud['id']}/codigo").status_code == 400


def test_nadie_mas_puede_generar_el_codigo(estudiante_a, estudiante_b, estudiante_c, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    assert estudiante_c.post(f"/api/solicitudes/{solicitud['id']}/codigo").status_code == 403
    assert encargado.post(f"/api/solicitudes/{solicitud['id']}/codigo").status_code == 403


def test_codigo_incorrecto_suma_intentos_y_se_bloquea(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    codigo = generar_codigo(estudiante_b, solicitud['id'])
    incorrecto = '000000' if codigo != '000000' else '111111'

    for intento in range(1, 5):
        respuesta = entregar(encargado, objeto['id'], incorrecto)
        assert respuesta.status_code == 400
        assert f'Quedan {5 - intento}' in respuesta.get_json()['mensaje']

    quinto = entregar(encargado, objeto['id'], incorrecto)
    assert 'invalidado' in quinto.get_json()['mensaje']
    # El código correcto ya no sirve: hay que generar uno nuevo
    assert 'todavía no ha generado' in entregar(encargado, objeto['id'], codigo).get_json()['mensaje']
    nuevo = generar_codigo(estudiante_b, solicitud['id'])
    assert entregar(encargado, objeto['id'], nuevo).status_code == 200


def test_codigo_con_formato_invalido_no_gasta_intentos(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    generar_codigo(estudiante_b, solicitud['id'])
    assert entregar(encargado, objeto['id'], 'abc').status_code == 400
    fila = consultar(app, 'SELECT intentos_codigo FROM solicitudes WHERE id = :id', id=solicitud['id'])[0]
    assert fila['intentos_codigo'] == 0


def test_generar_un_codigo_nuevo_invalida_el_anterior(estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    viejo = generar_codigo(estudiante_b, solicitud['id'])
    nuevo = generar_codigo(estudiante_b, solicitud['id'])
    if viejo != nuevo:  # (1 en un millón de que coincidan)
        assert entregar(encargado, objeto['id'], viejo).status_code == 400
    assert entregar(encargado, objeto['id'], nuevo).status_code == 200


def test_entrega_exige_carne_y_prueba(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    codigo = generar_codigo(estudiante_b, solicitud['id'])
    assert entregar(encargado, objeto['id'], codigo, carne=False).status_code == 400
    assert entregar(encargado, objeto['id'], codigo, prueba='no').status_code == 400
    assert consultar(app, 'SELECT count(*) AS n FROM entregas')[0]['n'] == 0


def test_reserva_vencida_libera_el_objeto(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    codigo = generar_codigo(estudiante_b, solicitud['id'])
    ejecutar(app, "UPDATE solicitudes SET vence_en = now() - interval '1 minute' WHERE id = :id", id=solicitud['id'])

    respuesta = entregar(encargado, objeto['id'], codigo)
    assert respuesta.status_code == 400
    assert 'venció' in respuesta.get_json()['mensaje']
    estados = consultar(app, '''SELECT (SELECT estado FROM objetos WHERE id = :o) AS objeto,
                                       (SELECT estado FROM solicitudes WHERE id = :s) AS solicitud''',
                        o=objeto['id'], s=solicitud['id'])[0]
    assert estados == {'objeto': 'en_oficina', 'solicitud': 'vencida'}


def test_las_reservas_vencidas_se_liberan_al_abrir_la_oficina(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    ejecutar(app, "UPDATE solicitudes SET vence_en = now() - interval '1 minute' WHERE id = :id", id=solicitud['id'])
    encargado.get('/api/encargado/objetos')
    assert consultar(app, 'SELECT estado FROM solicitudes WHERE id = :id', id=solicitud['id'])[0]['estado'] == 'vencida'
    avisos = consultar(app, "SELECT usuario_id FROM notificaciones WHERE tipo = 'reserva_vencida'")
    assert [a['usuario_id'] for a in avisos] == [estudiante_b.usuario['id']]


# --- Cancelaciones y cierres ------------------------------------------------

def test_estudiante_cancela_su_reclamacion_preaprobada(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    assert estudiante_b.post(f"/api/solicitudes/{solicitud['id']}/cancelar").status_code == 200
    assert consultar(app, 'SELECT estado FROM objetos WHERE id = :id', id=objeto['id'])[0]['estado'] == 'en_oficina'


def test_no_se_cancela_la_reclamacion_de_otro(estudiante_a, estudiante_b, estudiante_c, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    assert estudiante_c.post(f"/api/solicitudes/{solicitud['id']}/cancelar").status_code == 403


def test_encargado_cierra_un_objeto_y_descarta_reclamaciones(app, estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    respuesta = encargado.post(f"/api/encargado/objetos/{objeto['id']}/cerrar",
                               json={'motivo': 'Donado después de 6 meses en custodia'})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['objeto']['motivo_cierre'] == 'Donado después de 6 meses en custodia'
    assert consultar(app, 'SELECT estado FROM solicitudes WHERE id = :id', id=solicitud['id'])[0]['estado'] == 'descartada'


def test_no_se_cierra_un_objeto_reservado(estudiante_a, estudiante_b, encargado):
    objeto, _ = objeto_reservado(estudiante_a, estudiante_b, encargado)
    respuesta = encargado.post(f"/api/encargado/objetos/{objeto['id']}/cerrar", json={'motivo': 'Intento de cierre'})
    assert respuesta.status_code == 409


def test_recibir_dos_veces_el_mismo_objeto_falla(estudiante_a, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    respuesta = encargado.post(f"/api/encargado/objetos/{objeto['id']}/recepcion", json={})
    assert respuesta.status_code == 409


def test_la_auditoria_registra_quien_hizo_cada_paso(app, estudiante_a, estudiante_b, encargado):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    entregar(encargado, objeto['id'], generar_codigo(estudiante_b, solicitud['id']))
    filas = consultar(app, '''
        SELECT tabla, operacion, usuario_id, campos_modificados, datos_nuevos ->> 'estado' AS estado
        FROM auditoria WHERE (tabla = 'objetos' AND registro_id = :o) OR tabla = 'entregas' ORDER BY id
    ''', o=objeto['id'])
    autores = {(f['tabla'], f['estado']): f['usuario_id'] for f in filas}
    assert autores[('objetos', 'pendiente_entrega')] == estudiante_a.usuario['id']
    assert autores[('objetos', 'en_oficina')] == encargado.usuario['id']
    assert autores[('objetos', 'entregado')] == encargado.usuario['id']
    assert any(f['tabla'] == 'entregas' and f['operacion'] == 'INSERT' for f in filas)
