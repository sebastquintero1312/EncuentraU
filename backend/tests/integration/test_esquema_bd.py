"""Pruebas de la base de datos en sí: esquema, restricciones, triggers,
auditoría, permisos mínimos (least privilege), RLS e índices.

Se conectan DIRECTAMENTE a PostgreSQL (sin Flask) con los dos usuarios:
  motor_app    el usuario de permisos mínimos con el que corre la aplicación
  motor_dueno  el dueño de las tablas (migraciones)"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.ayudantes import consultar, crear_reporte, objeto_en_oficina, reclamar


def _codigo_error(error):
    return error.value.orig.pgcode


def _ejecutar_como(motor, sql, **parametros):
    with motor.begin() as conexion:
        return conexion.execute(text(sql), parametros)


# --- Esquema ----------------------------------------------------------------

def test_la_migracion_crea_tablas_vistas_y_procedimientos(app):
    tablas = {f['table_name'] for f in consultar(app, """
        SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'""")}
    assert {'roles', 'estados_objeto', 'transiciones_objeto', 'estados_solicitud', 'parametros', 'categorias',
            'ubicaciones', 'usuarios', 'tokens_usuario', 'objetos', 'solicitudes', 'entregas',
            'notificaciones', 'auditoria'} <= tablas

    vistas = {f['table_name'] for f in consultar(app, """
        SELECT table_name FROM information_schema.views WHERE table_schema = 'public'""")}
    assert {'v_objetos_disponibles', 'v_estadisticas_generales', 'v_estadisticas_mensuales',
            'v_desempeno_encargados', 'v_auditoria_detallada'} <= vistas

    rutinas = {(f['proname'], f['prokind']) for f in consultar(app, """
        SELECT p.proname, p.prokind FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'""")}
    for procedimiento in ('sp_registrar_recepcion', 'sp_preaprobar_solicitud', 'sp_rechazar_solicitud',
                          'sp_registrar_entrega', 'sp_cerrar_objeto'):
        assert (procedimiento, 'p') in rutinas  # 'p' = PROCEDURE
    assert ('fn_vencer_reservas', 'f') in rutinas


def test_datos_iniciales(app):
    assert {f['codigo'] for f in consultar(app, 'SELECT codigo FROM roles')} == {'estudiante', 'encargado', 'administrador'}
    assert consultar(app, 'SELECT count(*) AS n FROM transiciones_objeto')[0]['n'] == 10


# --- Restricciones e integridad ---------------------------------------------

def test_check_rechaza_correo_en_mayusculas(motor_dueno):
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_dueno, """INSERT INTO usuarios (primer_nombre, primer_apellido, correo, password_hash)
                                       VALUES ('A', 'B', 'MAYUS@sanmateo.edu.co', 'x')""")
    assert _codigo_error(error) == '23514'  # check_violation


def test_fk_compuesta_impide_un_estado_de_otro_tipo(app, estudiante_a, motor_dueno):
    objeto = crear_reporte(estudiante_a, 'perdido')
    # 'en_oficina' solo existe para objetos encontrados
    with pytest.raises(DBAPIError):
        _ejecutar_como(motor_dueno, "UPDATE objetos SET estado = 'en_oficina' WHERE id = :id", id=objeto['id'])


def test_trigger_rechaza_transiciones_no_permitidas(app, estudiante_a, motor_dueno):
    objeto = crear_reporte(estudiante_a, 'encontrado')
    # Saltarse la oficina: de "pendiente_entrega" directo a "entregado"
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_dueno, "UPDATE objetos SET estado = 'entregado' WHERE id = :id", id=objeto['id'])
    assert _codigo_error(error) == 'P0001'
    assert 'no permitido' in str(error.value.orig)


def test_trigger_exige_el_estado_inicial_al_crear(app, estudiante_a, motor_dueno):
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_dueno, """INSERT INTO objetos (tipo, nombre, categoria_id, ubicacion_id, fecha_evento,
                                       descripcion, estado, usuario_id)
                                       VALUES ('encontrado', 'Celular', 1, 1, CURRENT_DATE, 'Descripción larga',
                                               'en_oficina', :u)""", u=estudiante_a.usuario['id'])
    assert _codigo_error(error) == 'P0001'


def test_un_objeto_no_se_puede_entregar_dos_veces(app, estudiante_a, estudiante_b, encargado, motor_dueno):
    objeto = objeto_en_oficina(estudiante_a, encargado)
    solicitud = reclamar(estudiante_b, objeto['id']).get_json()['solicitud']
    sql = """INSERT INTO entregas (objeto_id, solicitud_id, entregado_por_id, carne_verificado, prueba_propiedad)
             VALUES (:o, :s, :e, TRUE, 'Prueba directa')"""
    _ejecutar_como(motor_dueno, sql, o=objeto['id'], s=solicitud['id'], e=encargado.usuario['id'])
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_dueno, sql, o=objeto['id'], s=solicitud['id'], e=encargado.usuario['id'])
    assert _codigo_error(error) == '23505'


def test_entrega_con_objeto_que_no_coincide_con_la_solicitud(app, estudiante_a, estudiante_b, encargado, motor_dueno):
    """Clave foránea compuesta (solicitud_id, objeto_id): la copia de
    objeto_id en entregas nunca puede quedar inconsistente."""
    objeto_1 = objeto_en_oficina(estudiante_a, encargado, nombre='Objeto uno')
    objeto_2 = objeto_en_oficina(estudiante_a, encargado, nombre='Objeto dos')
    solicitud = reclamar(estudiante_b, objeto_1['id']).get_json()['solicitud']
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_dueno, """INSERT INTO entregas (objeto_id, solicitud_id, entregado_por_id,
                                       carne_verificado, prueba_propiedad) VALUES (:o, :s, :e, TRUE, 'Prueba directa')""",
                       o=objeto_2['id'], s=solicitud['id'], e=encargado.usuario['id'])
    assert _codigo_error(error) == '23503'  # foreign_key_violation


# --- Auditoría ----------------------------------------------------------------

def test_auditoria_registra_insert_y_update_con_campos_modificados(app, estudiante_a):
    objeto = crear_reporte(estudiante_a, 'perdido')
    estudiante_a.put(f"/api/objetos/{objeto['id']}", json={
        'version': objeto['version'], 'nombre': 'Celular Samsung', 'categoria_id': 1, 'ubicacion_id': 1,
        'descripcion': objeto['descripcion'], 'fecha_evento': objeto['fecha_evento'],
        'detalle_ubicacion': objeto['detalle_ubicacion'],
    })
    filas = consultar(app, """SELECT operacion, usuario_id, campos_modificados, datos_anteriores ->> 'nombre' AS antes,
                                     datos_nuevos ->> 'nombre' AS despues
                              FROM auditoria WHERE tabla = 'objetos' AND registro_id = :id ORDER BY id""", id=objeto['id'])
    assert [f['operacion'] for f in filas] == ['INSERT', 'UPDATE']
    assert all(f['usuario_id'] == estudiante_a.usuario['id'] for f in filas)
    assert filas[1]['campos_modificados'] == ['nombre']
    assert (filas[1]['antes'], filas[1]['despues']) == ('Celular', 'Celular Samsung')


def test_auditoria_es_inmutable_incluso_para_el_dueno(app, estudiante_a, motor_dueno):
    crear_reporte(estudiante_a, 'perdido')
    for sql in ('UPDATE auditoria SET usuario_id = NULL', 'DELETE FROM auditoria', 'TRUNCATE auditoria'):
        with pytest.raises(DBAPIError) as error:
            _ejecutar_como(motor_dueno, sql)
        assert 'solo inserción' in str(error.value.orig)


# --- Permisos mínimos del usuario de la aplicación ---------------------------

@pytest.mark.parametrize('sql', [
    'UPDATE auditoria SET usuario_id = NULL',
    'DELETE FROM auditoria',
    "INSERT INTO auditoria (tabla, operacion) VALUES ('objetos', 'DELETE')",
    'DELETE FROM objetos',
    'DELETE FROM usuarios',
    "UPDATE usuarios SET correo = 'otro@sanmateo.edu.co'",
    "UPDATE solicitudes SET descripcion = 'Texto cambiado después de enviarla'",
    'UPDATE objetos SET usuario_id = 1',
    "UPDATE entregas SET prueba_propiedad = 'Modificada'",
    'CREATE TABLE tabla_intrusa (id INTEGER)',
    'ALTER TABLE auditoria DISABLE TRIGGER trg_auditoria_sin_vaciar',
    'DROP TABLE notificaciones',
])
def test_la_aplicacion_no_tiene_permiso(app, motor_app, sql):
    with pytest.raises(DBAPIError) as error:
        _ejecutar_como(motor_app, sql)
    # 42501 = insufficient_privilege ; 42P01 nunca debería aparecer (las tablas existen)
    assert _codigo_error(error) in ('42501',), str(error.value.orig)


def test_la_aplicacion_si_puede_leer_la_auditoria(app, motor_app, estudiante_a):
    crear_reporte(estudiante_a, 'perdido')
    with motor_app.connect() as conexion:
        assert conexion.execute(text('SELECT count(*) FROM auditoria')).scalar() >= 1


def test_rls_activo_en_todas_las_tablas(app):
    sin_rls = consultar(app, """
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> 'alembic_version' AND NOT c.relrowsecurity""")
    assert sin_rls == []


def test_procedimientos_no_ejecutables_por_public(app):
    filas = consultar(app, """SELECT has_function_privilege('public', 'sp_registrar_entrega(integer,integer,text,boolean,text,text,text)', 'EXECUTE') AS puede""")
    assert filas[0]['puede'] is False


# --- Índices ---------------------------------------------------------------------

def test_indices_especiales_existen(app):
    indices = {f['indexname']: f['indexdef'] for f in consultar(app, "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'")}
    assert 'USING gin' in indices['ix_objetos_nombre_trgm']
    assert 'USING brin' in indices['ix_auditoria_fecha']
    assert 'WHERE' in indices['ux_solicitudes_una_preaprobada'] and 'UNIQUE' in indices['ux_solicitudes_una_preaprobada']
    assert 'WHERE' in indices['ix_objetos_disponibles']
    # Las claves foráneas tienen índice (PostgreSQL no los crea solo)
    for nombre in ('ix_objetos_usuario', 'ix_objetos_categoria', 'ix_solicitudes_objeto', 'ix_solicitudes_solicitante'):
        assert nombre in indices


def test_la_busqueda_por_texto_puede_usar_el_indice_de_trigramas(app, motor_dueno):
    """Con pocas filas PostgreSQL prefiere recorrer la tabla; se desactiva el
    recorrido secuencial solo en esta transacción para comprobar que el
    índice SÍ sirve para ILIKE '%...%'."""
    with motor_dueno.begin() as conexion:
        conexion.execute(text('SET LOCAL enable_seqscan = off'))
        plan = '\n'.join(fila[0] for fila in conexion.execute(text(
            "EXPLAIN SELECT id FROM objetos WHERE nombre ILIKE '%celu%'")))
    assert 'ix_objetos_nombre_trgm' in plan
