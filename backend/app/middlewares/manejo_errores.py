# Manejo centralizado de errores.
# Nunca se debe devolver al usuario un stack trace, una consulta SQL,
# ni ningún detalle interno del servidor.

from flask import jsonify


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

    @app.errorhandler(Exception)
    def error_interno(error):
        # Log interno para nosotros (no se muestra al usuario)
        app.logger.exception('Error no controlado')
        return jsonify({'mensaje': 'Ocurrió un error en el servidor'}), 500
