"""Matriz de permisos: cada rol hace SOLO lo suyo (deny by default).

Estudiante: reporta, busca y reclama.
Encargado: recibe, verifica y entrega; NO reporta ni reclama.
Administrador: usuarios, catálogos, auditoría; NO opera objetos."""

import pytest

from tests.ayudantes import crear_reporte, objeto_en_oficina, reclamar

RUTAS_ESTUDIANTE = [
    ('GET', '/api/objetos'),
    ('POST', '/api/objetos'),
    ('GET', '/api/mis-reportes'),
    ('POST', '/api/solicitudes'),
    ('GET', '/api/mis-solicitudes'),
]
RUTAS_ENCARGADO = [
    ('GET', '/api/encargado/objetos'),
    ('GET', '/api/encargado/solicitudes'),
    ('GET', '/api/encargado/estadisticas'),
    ('POST', '/api/encargado/objetos/1/recepcion'),
    ('POST', '/api/encargado/objetos/1/entrega'),
    ('POST', '/api/encargado/solicitudes/1/preaprobar'),
]
RUTAS_ADMIN = [
    ('GET', '/api/admin/usuarios'),
    ('GET', '/api/admin/auditoria'),
    ('GET', '/api/admin/estadisticas'),
    ('GET', '/api/admin/categorias'),
    ('POST', '/api/admin/categorias'),
    ('GET', '/api/admin/parametros'),
    ('GET', '/api/admin/objetos'),
    ('GET', '/api/admin/exportar/objetos.csv'),
]


def _pedir(cliente, metodo, ruta):
    return cliente.open(ruta, method=metodo, json={})


@pytest.mark.parametrize('metodo,ruta', RUTAS_ESTUDIANTE + RUTAS_ENCARGADO + RUTAS_ADMIN)
def test_sin_sesion_todo_responde_401(client, metodo, ruta):
    assert _pedir(client, metodo, ruta).status_code == 401


@pytest.mark.parametrize('metodo,ruta', RUTAS_ESTUDIANTE)
def test_rutas_de_estudiante_prohibidas_para_encargado_y_admin(encargado, admin, metodo, ruta):
    assert _pedir(encargado, metodo, ruta).status_code == 403
    assert _pedir(admin, metodo, ruta).status_code == 403


@pytest.mark.parametrize('metodo,ruta', RUTAS_ENCARGADO)
def test_rutas_de_encargado_prohibidas_para_estudiante_y_admin(estudiante_a, admin, metodo, ruta):
    assert _pedir(estudiante_a, metodo, ruta).status_code == 403
    assert _pedir(admin, metodo, ruta).status_code == 403


@pytest.mark.parametrize('metodo,ruta', RUTAS_ADMIN)
def test_rutas_de_admin_prohibidas_para_estudiante_y_encargado(estudiante_a, encargado, metodo, ruta):
    assert _pedir(estudiante_a, metodo, ruta).status_code == 403
    assert _pedir(encargado, metodo, ruta).status_code == 403


def test_cada_rol_accede_a_sus_propias_rutas(estudiante_a, encargado, admin):
    assert estudiante_a.get('/api/objetos').status_code == 200
    assert encargado.get('/api/encargado/objetos').status_code == 200
    assert admin.get('/api/admin/usuarios').status_code == 200


def test_encargado_no_puede_crear_reportes_ni_reclamar(estudiante_a, encargado):
    assert encargado.post('/api/objetos', json={'tipo': 'perdido'}).status_code == 403
    objeto = objeto_en_oficina(estudiante_a, encargado)
    assert reclamar(encargado, objeto['id']).status_code == 403


def test_admin_no_puede_operar_objetos(estudiante_a, admin):
    objeto = crear_reporte(estudiante_a, 'encontrado')
    assert admin.post(f"/api/encargado/objetos/{objeto['id']}/recepcion", json={}).status_code == 403
    assert admin.post(f"/api/encargado/objetos/{objeto['id']}/cerrar", json={'motivo': 'xxxxxx'}).status_code == 403


def test_admin_si_puede_consultar_objetos(estudiante_a, admin):
    objeto = crear_reporte(estudiante_a, 'perdido')
    assert admin.get(f"/api/admin/objetos/{objeto['id']}").status_code == 200


def test_el_rol_se_relee_de_la_base_en_cada_peticion(app, estudiante_a):
    """Si un administrador le quita el rol a alguien, el cambio aplica en la
    siguiente petición (no se confía en lo que se guardó al iniciar sesión)."""
    from tests.ayudantes import ejecutar
    ejecutar(app, "UPDATE usuarios SET rol = 'encargado' WHERE correo = 'ana.a@sanmateo.edu.co'")
    assert estudiante_a.get('/api/objetos').status_code == 403
    assert estudiante_a.get('/api/encargado/objetos').status_code == 200


def test_la_base_de_datos_tambien_exige_el_rol_encargado(app, estudiante_a):
    """Defensa en profundidad: aunque se saltara Flask, el procedimiento
    almacenado rechaza a quien no es encargado."""
    from sqlalchemy.exc import DBAPIError
    from tests.ayudantes import ejecutar
    objeto = crear_reporte(estudiante_a, 'encontrado')
    with pytest.raises(DBAPIError) as error:
        ejecutar(app, 'CALL sp_registrar_recepcion(:o, :u, NULL, NULL)', o=objeto['id'], u=estudiante_a.usuario['id'])
    assert 'Solo un encargado' in str(error.value.orig)
