# Acta de entrega: el registro definitivo de que un objeto salió de la
# oficina y a manos de quién. La crea SOLO el procedimiento almacenado
# sp_registrar_entrega (ver migrations/sql/03_procedimientos.sql); la
# aplicación no tiene permiso para modificarla ni borrarla después.

from app.extensions import db


class Entrega(db.Model):
    __tablename__ = 'entregas'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    objeto_id = db.Column(db.Integer, db.ForeignKey('objetos.id'), nullable=False, unique=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes.id'), nullable=False, unique=True)
    entregado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    carne_verificado = db.Column(db.Boolean, nullable=False)
    prueba_propiedad = db.Column(db.String(300), nullable=False)
    observaciones = db.Column(db.String(300), nullable=False, server_default='')
    entregado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    objeto = db.relationship('Objeto')
    solicitud = db.relationship('Solicitud')
    entregado_por = db.relationship('Usuario')

    def a_dict(self):
        return {
            'id': self.id,
            'objeto_id': self.objeto_id,
            'solicitud_id': self.solicitud_id,
            'entregado_por': self.entregado_por.nombre_completo if self.entregado_por else None,
            'recibido_por': self.solicitud.solicitante.nombre_completo if self.solicitud else None,
            'carne_verificado': self.carne_verificado,
            'prueba_propiedad': self.prueba_propiedad,
            'observaciones': self.observaciones,
            'entregado_en': self.entregado_en.isoformat() if self.entregado_en else None,
        }
