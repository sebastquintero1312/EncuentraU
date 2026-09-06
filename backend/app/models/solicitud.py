# Modelo de Solicitud (reclamación de un objeto encontrado/perdido).
#
# Una solicitud es el proceso mediante el cual un usuario intenta demostrar
# que un objeto reportado es suyo. El campo "mensaje" contiene información
# privada de verificación (características únicas del objeto) y NUNCA debe
# exponerse públicamente: solo la ve el propio solicitante, el dueño del
# reporte (para poder verificar) y el administrador.

from datetime import datetime

from app.extensions import db

ESTADOS_VALIDOS = ('pendiente', 'en_revision', 'aprobada', 'rechazada', 'cancelada')
ESTADOS_ABIERTOS = ('pendiente', 'en_revision')


class Solicitud(db.Model):
    __tablename__ = 'solicitudes'

    id = db.Column(db.Integer, primary_key=True)
    objeto_id = db.Column(db.Integer, db.ForeignKey('objetos.id'), nullable=False, index=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    contacto = db.Column(db.String(150), nullable=False)
    mensaje = db.Column(db.String(400), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    respuesta_admin = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    objeto = db.relationship('Objeto', backref=db.backref('solicitudes', lazy='dynamic'))
    solicitante = db.relationship('Usuario', backref=db.backref('solicitudes', lazy='dynamic'))

    __table_args__ = (
        db.CheckConstraint(
            "estado IN ('pendiente','en_revision','aprobada','rechazada','cancelada')",
            name='ck_solicitud_estado',
        ),
    )

    def publica(self):
        """Vista completa: solo para el propio solicitante, el dueño del
        objeto reclamado, o un administrador (la información de verificación
        es privada, ver docstring del módulo)."""
        return {
            'id': self.id,
            'objeto_id': self.objeto_id,
            'objeto_nombre': self.objeto.nombre if self.objeto else None,
            'solicitante_id': self.solicitante_id,
            'solicitante_nombre': f'{self.solicitante.primer_nombre} {self.solicitante.primer_apellido}'.strip() if self.solicitante else None,
            'contacto': self.contacto,
            'mensaje': self.mensaje,
            'estado': self.estado,
            'respuesta_admin': self.respuesta_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
