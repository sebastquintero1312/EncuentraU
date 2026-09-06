# Manejo centralizado de errores.
# Nunca se debe devolver al usuario un stack trace, una consulta SQL,
# ni ningún detalle interno del servidor.

from flask import jsonify
from werkzeug.exceptions import HTTPException


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

    @app.errorhandler(Exception)
    def error_interno(error):
        # Log interno para nosotros (no se muestra al usuario)
        app.logger.exception('Error no controlado')
        return jsonify({'mensaje': 'Ocurrió un error en el servidor'}), 500
