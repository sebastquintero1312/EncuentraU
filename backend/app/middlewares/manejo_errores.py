# Manejo centralizado de errores.
# Nunca se debe devolver al usuario un stack trace, una consulta SQL,
# ni ningún detalle interno del servidor.

from flask import jsonify
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import HTTPException

from app.extensions import db

# Índices únicos y restricciones cuyo choque tiene un significado claro
# para el usuario (ver migrations/sql/01_tablas.sql).
MENSAJES_RESTRICCION_UNICA = {
    'ux_solicitudes_abierta_por_usuario': 'Ya tienes una reclamación abierta para este objeto',
    'ux_solicitudes_una_preaprobada': 'Ya hay otra reclamación pre-aprobada para este objeto',
    'ux_categorias_nombre': 'Ya existe una categoría con ese nombre',
    'ux_ubicaciones_nombre': 'Ya existe una ubicación con ese nombre',
    'uq_entregas_objeto': 'Este objeto ya fue entregado',
    'uq_entregas_solicitud': 'Esta reclamación ya tiene una entrega registrada',
    'ux_usuarios_correo': 'No fue posible completar la operación',
}


def registrar_manejadores_error(app):

    @app.errorhandler(404)
    def no_encontrado(error):
        return jsonify({'mensaje': 'Recurso no encontrado'}), 404

    @app.errorhandler(405)
    def metodo_no_permitido(error):
        return jsonify({'mensaje': 'Método no permitido'}), 405

    @app.errorhandler(429)
    def demasiadas_peticiones(error):
        return jsonify({'mensaje': 'Demasiados intentos, intenta de nuevo en un momento'}), 429

    @app.errorhandler(HTTPException)
    def error_http(error):
        # Cubre cualquier error HTTP que no tenga un manejador específico
        # arriba: CSRF inválido/ausente (400), abort(401)/abort(403), body
        # JSON malformado (400), etc. Sin este manejador, el handler genérico
        # de Exception de más abajo los convertía todos en 500, ocultando el
        # código HTTP real (bug detectado y corregido durante la migración a v1.0).
        mensaje = error.description if error.description else 'Solicitud inválida'
        return jsonify({'mensaje': mensaje}), error.code

    @app.errorhandler(StaleDataError)
    def conflicto_de_version(error):
        # Concurrencia optimista: otra persona modificó la misma fila entre
        # que se leyó y se intentó guardar (ver version_id_col en los modelos).
        db.session.rollback()
        return jsonify({
            'mensaje': 'Otra persona modificó este registro al mismo tiempo. Recarga la página e inténtalo de nuevo.',
        }), 409

    @app.errorhandler(DBAPIError)
    def error_base_de_datos(error):
        """Traduce los errores de PostgreSQL a respuestas útiles. Las reglas
        del negocio que se aplican dentro de la base de datos (triggers y
        procedimientos) usan el código P0001 con un mensaje ya pensado para
        el usuario; el resto se responde de forma genérica."""
        db.session.rollback()
        original = getattr(error, 'orig', None)
        codigo = getattr(original, 'pgcode', None)
        diagnostico = getattr(original, 'diag', None)

        if codigo == 'P0001' and diagnostico is not None and diagnostico.message_primary:
            return jsonify({'mensaje': diagnostico.message_primary}), 409

        if codigo == '23505':  # unique_violation
            restriccion = getattr(diagnostico, 'constraint_name', None)
            mensaje = MENSAJES_RESTRICCION_UNICA.get(restriccion, 'El registro ya existe')
            return jsonify({'mensaje': mensaje}), 409

        if codigo in ('40P01', '40001', '55P03'):  # deadlock, serialización, lock no disponible
            return jsonify({'mensaje': 'Hubo un conflicto con otra operación simultánea. Intenta de nuevo.'}), 409

        if codigo in ('23514', '23503', '23502', '22001', '22P02', '22007', '22008'):
            # check, FK, not null, texto demasiado largo, formato inválido
            return jsonify({'mensaje': 'Los datos enviados no son válidos'}), 400

        if codigo == '42501':  # insufficient_privilege
            app.logger.error('Permiso de base de datos denegado: %s', diagnostico.message_primary if diagnostico else '')
            return jsonify({'mensaje': 'Operación no permitida'}), 403

        app.logger.exception('Error de base de datos no controlado')
        return jsonify({'mensaje': 'Ocurrió un error en el servidor'}), 500

    @app.errorhandler(Exception)
    def error_interno(error):
        # Log interno para nosotros (no se muestra al usuario)
        app.logger.exception('Error no controlado')
        return jsonify({'mensaje': 'Ocurrió un error en el servidor'}), 500
