# Notificaciones dentro de la aplicación. Cada notificación también se puede
# enviar por correo (ver services/notificaciones_service.py): si el correo
# cae en spam, el estudiante igual la ve en su cuenta.

from app.extensions import db


class Notificacion(db.Model):
    __tablename__ = 'notificaciones'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    mensaje = db.Column(db.String(500), nullable=False)
    enlace = db.Column(db.String(200), nullable=False, server_default='')
    leida_en = db.Column(db.DateTime(timezone=True), nullable=True)
    correo_enviado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    usuario = db.relationship('Usuario')

    __mapper_args__ = {'eager_defaults': True}

    def a_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'enlace': self.enlace,
            'leida': self.leida_en is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
