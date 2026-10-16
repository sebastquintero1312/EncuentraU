"""Transacciones (ACID) y concurrencia con DOS conexiones reales a la vez.

Cada prueba abre dos conexiones independientes a PostgreSQL (como dos
encargados en dos computadores) y comprueba que el bloqueo de filas
(SELECT ... FOR UPDATE dentro de los procedimientos) y los índices únicos
mantienen los datos consistentes aunque actúen al mismo tiempo."""

import os
import threading
import time

import psycopg2
import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import StaleDataError

from tests.ayudantes import consultar, crear_reporte, generar_codigo, objeto_en_oficina, objeto_reservado, reclamar


def _conexion_app():
    """Conexión directa con el usuario de la aplicación (conftest.py dejó
    DATABASE_URL apuntando a la base de pruebas)."""
    conexion = psycopg2.connect(os.environ['DATABASE_URL'])
    conexion.autocommit = False
    return conexion


def _hash_codigo(app, codigo):
    from app.seguridad import hash_codigo_retiro
    with app.app_context():
        return hash_codigo_retiro(codigo)


def _en_otro_hilo(funcion):
    """Ejecuta `funcion` en un hilo y devuelve un diccionario donde quedará
    su resultado o el error que lanzó."""
    resultado = {}

    def correr():
        try:
            resultado['valor'] = funcion()
        except Exception as error:  # noqa: BLE001 - se inspecciona en la prueba
            resultado['error'] = error

    hilo = threading.Thread(target=correr)
    hilo.start()
    resultado['hilo'] = hilo
    return resultado


def test_dos_encargados_entregan_el_mismo_objeto_al_tiempo(app, estudiante_a, estudiante_b, encargado, encargado_2):
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    hash_codigo = _hash_codigo(app, generar_codigo(estudiante_b, solicitud['id']))
    sql = "CALL sp_registrar_entrega(%s, %s, %s, TRUE, 'Desbloqueó el celular', '', NULL)"

    primera = _conexion_app()
    segunda = _conexion_app()
    try:
        cursor_1 = primera.cursor()
        cursor_1.execute(sql, (objeto['id'], encargado.usuario['id'], hash_codigo))
        assert cursor_1.fetchone()[0] == 'entregado'   # todavía SIN commit: tiene la fila bloqueada

        def segunda_entrega():
            cursor_2 = segunda.cursor()
            cursor_2.execute(sql, (objeto['id'], encargado_2.usuario['id'], hash_codigo))
            return cursor_2.fetchone()[0]

        resultado = _en_otro_hilo(segunda_entrega)
        time.sleep(0.5)
        assert resultado['hilo'].is_alive(), 'la segunda transacción debería estar esperando el bloqueo'

        primera.commit()
        resultado['hilo'].join(timeout=10)
        assert 'error' in resultado
        assert 'no tiene una reclamación pre-aprobada' in str(resultado['error'])
        segunda.rollback()
    finally:
        primera.close()
        segunda.close()

    assert consultar(app, 'SELECT count(*) AS n FROM entregas')[0]['n'] == 1
    entrega = consultar(app, 'SELECT entregado_por_id FROM entregas')[0]
    assert entrega['entregado_por_id'] == encargado.usuario['id']


def test_dos_encargados_preaprueban_reclamaciones_distintas_al_tiempo(
        app, estudiante_a, estudiante_b, estudiante_c, encargado, encargado_2):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    s_b = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    s_c = reclamar(estudiante_c, objeto['id']).get_json()['solicitud']
    sql = "CALL sp_preaprobar_solicitud(%s, %s, '', NULL)"

    primera = _conexion_app()
    segunda = _conexion_app()
    try:
        primera.cursor().execute(sql, (s_b['id'], encargado.usuario['id']))
        resultado = _en_otro_hilo(lambda: segunda.cursor().execute(sql, (s_c['id'], encargado_2.usuario['id'])))
        time.sleep(0.5)
        assert resultado['hilo'].is_alive()
        primera.commit()
        resultado['hilo'].join(timeout=10)
        assert 'otra reclamación pre-aprobada' in str(resultado['error'])
        segunda.rollback()
    finally:
        primera.close()
        segunda.close()

    estados = {f['id']: f['estado'] for f in consultar(app, 'SELECT id, estado FROM solicitudes')}
    assert estados == {s_b['id']: 'preaprobada', s_c['id']: 'pendiente'}


def test_indice_unico_parcial_impide_dos_preaprobadas(app, estudiante_a, estudiante_b, estudiante_c, encargado, motor_dueno):
    """Aunque alguien se saltara el procedimiento y escribiera directo en la
    tabla, la base de datos no permite dos reclamaciones pre-aprobadas para
    el mismo objeto."""
    from sqlalchemy import text
    objeto, s_b = objeto_reservado(estudiante_a, estudiante_b, encargado)
    s_c = reclamar(estudiante_c, objeto['id']).get_json()['solicitud']
    with pytest.raises(DBAPIError) as error:
        with motor_dueno.begin() as conexion:
            conexion.execute(text("""UPDATE solicitudes SET estado = 'preaprobada', preaprobada_en = now(),
                                     vence_en = now() + interval '1 day' WHERE id = :id"""), {'id': s_c['id']})
    assert error.value.orig.pgcode == '23505'
    assert error.value.orig.diag.constraint_name == 'ux_solicitudes_una_preaprobada'


def test_atomicidad_un_error_deshace_todo_el_procedimiento(app, estudiante_a, estudiante_b, encargado):
    """Si la entrega falla a mitad de camino (carné no verificado), no queda
    NADA a medias: ni acta de entrega, ni objeto entregado."""
    objeto, solicitud = objeto_reservado(estudiante_a, estudiante_b, encargado)
    hash_codigo = _hash_codigo(app, generar_codigo(estudiante_b, solicitud['id']))
    conexion = _conexion_app()
    try:
        with pytest.raises(psycopg2.Error) as error:
            conexion.cursor().execute("CALL sp_registrar_entrega(%s, %s, %s, FALSE, 'Prueba', '', NULL)",
                                      (objeto['id'], encargado.usuario['id'], hash_codigo))
        assert 'carné' in str(error.value)
        conexion.rollback()
    finally:
        conexion.close()

    estado = consultar(app, '''SELECT (SELECT estado FROM objetos WHERE id = :o) AS objeto,
                                      (SELECT estado FROM solicitudes WHERE id = :s) AS solicitud,
                                      (SELECT count(*) FROM entregas) AS entregas''', o=objeto['id'], s=solicitud['id'])[0]
    assert estado == {'objeto': 'reservado', 'solicitud': 'preaprobada', 'entregas': 0}


def test_concurrencia_optimista_en_el_orm(app, estudiante_a):
    """Dos sesiones leen el mismo reporte; la primera guarda y la segunda,
    que tiene la versión vieja, recibe StaleDataError en vez de pisar el cambio."""
    objeto = crear_reporte(estudiante_a, 'perdido')
    from sqlalchemy.orm import Session
    from app.extensions import db
    from app.models.objeto import Objeto

    with app.app_context():
        sesion_1 = Session(bind=db.engine)
        sesion_2 = Session(bind=db.engine)
        try:
            copia_1 = sesion_1.get(Objeto, objeto['id'])
            copia_2 = sesion_2.get(Objeto, objeto['id'])
            copia_1.nombre = 'Primera edición'
            sesion_1.commit()
            copia_2.nombre = 'Segunda edición (con datos viejos)'
            with pytest.raises(StaleDataError):
                sesion_2.commit()
        finally:
            sesion_1.close()
            sesion_2.close()

    assert consultar(app, 'SELECT nombre FROM objetos WHERE id = :id', id=objeto['id'])[0]['nombre'] == 'Primera edición'
