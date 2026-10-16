"""Notificaciones dentro de la aplicación (y su copia por correo)."""

from tests.ayudantes import consultar, objeto_en_oficina, reclamar
from app.services.correo_service import CORREOS_ENVIADOS


def test_reclamar_genera_notificaciones(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    reclamar(estudiante_b, objeto['id'])
    del_estudiante = estudiante_b.get('/api/notificaciones').get_json()
    assert del_estudiante['no_leidas'] >= 1
    assert any(n['tipo'] == 'reclamacion_recibida' for n in del_estudiante['datos'])
    del_encargado = encargado.get('/api/notificaciones').get_json()
    assert any(n['tipo'] == 'reclamacion_nueva' for n in del_encargado['datos'])


def test_las_notificaciones_tambien_llegan_por_correo(app, estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    CORREOS_ENVIADOS.clear()
    reclamar(estudiante_b, objeto['id'])
    assert any(c['para'] == 'beto.b@sanmateo.edu.co' and 'Recibimos tu reclamación' in c['asunto']
               for c in CORREOS_ENVIADOS)
    fila = consultar(app, "SELECT correo_enviado_en FROM notificaciones WHERE tipo = 'reclamacion_recibida'")[0]
    assert fila['correo_enviado_en'] is not None


def test_marcar_leida_y_todas(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    reclamar(estudiante_b, objeto['id'])
    notificacion = estudiante_b.get('/api/notificaciones').get_json()['datos'][0]
    assert estudiante_b.post(f"/api/notificaciones/{notificacion['id']}/leida").status_code == 200
    assert estudiante_b.post('/api/notificaciones/leer-todas').status_code == 200
    assert estudiante_b.get('/api/notificaciones').get_json()['no_leidas'] == 0


def test_no_se_puede_marcar_la_notificacion_de_otro(estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    reclamar(estudiante_b, objeto['id'])
    ajena = estudiante_b.get('/api/notificaciones').get_json()['datos'][0]
    assert estudiante_a.post(f"/api/notificaciones/{ajena['id']}/leida").status_code == 404


def test_los_enlaces_de_las_notificaciones_son_internos(app, estudiante_a, estudiante_b, encargado):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    reclamar(estudiante_b, objeto['id'])
    for fila in consultar(app, 'SELECT enlace FROM notificaciones'):
        assert not fila['enlace'].startswith(('http', '//', 'javascript'))
