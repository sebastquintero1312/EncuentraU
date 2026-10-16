# Le dice a PostgreSQL QUIÉN está haciendo cada cambio, para que el trigger
# de auditoría (fn_auditoria, en migrations/sql/02_funciones_triggers.sql)
# pueda guardarlo.
#
# Cómo funciona: al inicio de cada transacción se ejecuta
#     SELECT set_config('app.usuario_id', '<id>', true)
# El último parámetro (true) hace que el valor dure SOLO esa transacción:
# nunca se mezcla con la petición de otra persona aunque se reutilice la
# conexión del pool.

from flask import g, has_request_context, request
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.extensions import db

_SQL_CONTEXTO = text(
    "SELECT set_config('app.usuario_id', :usuario_id, true), set_config('app.ip', :ip, true)"
)

_listener_registrado = False


def _valores_contexto():
    usuario_id = ''
    ip = ''
    if has_request_context():
        usuario_id = str(g.get('usuario_id_auditoria') or '')
        ip = request.remote_addr or ''
    return {'usuario_id': usuario_id, 'ip': ip}


def registrar_contexto_auditoria():
    """Se llama una vez desde create_app(): cada transacción nueva empieza
    con el usuario y la IP de la petición actual (vacíos si no hay sesión o
    si la acción viene de un comando de terminal)."""
    global _listener_registrado
    if _listener_registrado:
        return

    @event.listens_for(Session, 'after_begin')
    def _al_iniciar_transaccion(session, transaction, connection):
        if connection.dialect.name == 'postgresql':
            connection.execute(_SQL_CONTEXTO, _valores_contexto())

    _listener_registrado = True


def fijar_usuario_auditoria(usuario_id):
    """La transacción de la petición ya empezó cuando se leyó el usuario de la
    sesión (para verificar su rol), así que el valor se fija también en la
    transacción actual, no solo en las siguientes."""
    g.usuario_id_auditoria = usuario_id
    db.session.execute(_SQL_CONTEXTO, _valores_contexto())
