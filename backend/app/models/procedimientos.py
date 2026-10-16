# Llamadas a los procedimientos almacenados de PostgreSQL.
#
# Es el único lugar del backend (además de models/reportes.py) donde se
# escribe SQL a mano. Siempre con parámetros (:nombre), nunca concatenando
# texto: SQLAlchemy los envía separados de la consulta, así que no hay
# posibilidad de inyección SQL.
#
# Ninguna función hace commit: el procedimiento corre dentro de la
# transacción de la petición y el servicio decide cuándo confirmarla.

from sqlalchemy import text

from app.extensions import db


def _llamar(sql, parametros):
    """Ejecuta un CALL y devuelve el valor del parámetro INOUT p_resultado."""
    return db.session.execute(text(sql), parametros).scalar()


def registrar_recepcion(objeto_id, encargado_id, observaciones):
    return _llamar(
        'CALL sp_registrar_recepcion(:objeto_id, :encargado_id, :observaciones, NULL)',
        {'objeto_id': objeto_id, 'encargado_id': encargado_id, 'observaciones': observaciones},
    )


def preaprobar_solicitud(solicitud_id, encargado_id, respuesta):
    return _llamar(
        'CALL sp_preaprobar_solicitud(:solicitud_id, :encargado_id, :respuesta, NULL)',
        {'solicitud_id': solicitud_id, 'encargado_id': encargado_id, 'respuesta': respuesta},
    )


def rechazar_solicitud(solicitud_id, encargado_id, motivo):
    return _llamar(
        'CALL sp_rechazar_solicitud(:solicitud_id, :encargado_id, :motivo, NULL)',
        {'solicitud_id': solicitud_id, 'encargado_id': encargado_id, 'motivo': motivo},
    )


def registrar_entrega(objeto_id, encargado_id, codigo_hash, carne_verificado, prueba, observaciones):
    return _llamar(
        'CALL sp_registrar_entrega(:objeto_id, :encargado_id, :codigo_hash, :carne, :prueba, :observaciones, NULL)',
        {
            'objeto_id': objeto_id,
            'encargado_id': encargado_id,
            'codigo_hash': codigo_hash,
            'carne': carne_verificado,
            'prueba': prueba,
            'observaciones': observaciones,
        },
    )


def cerrar_objeto(objeto_id, encargado_id, motivo):
    return _llamar(
        'CALL sp_cerrar_objeto(:objeto_id, :encargado_id, :motivo, NULL)',
        {'objeto_id': objeto_id, 'encargado_id': encargado_id, 'motivo': motivo},
    )


def vencer_reservas():
    """Devuelve una lista de filas (solicitud_id, solicitante_id, objeto_id)
    de las reservas que acaban de vencer."""
    filas = db.session.execute(text('SELECT solicitud_id, solicitante_id, objeto_id FROM fn_vencer_reservas()'))
    return [dict(fila._mapping) for fila in filas]
