# Modelo de Solicitud (reclamación de un objeto encontrado).
#
# Flujo (ver docs/AUTHORIZATION.md, "Cómo se evita que alguien reclame algo
# ajeno"):
#   pendiente  -> el estudiante describe el objeto SIN ver los detalles privados
#   preaprobada -> el encargado comparó y la descripción coincide; el estudiante
#                  genera un código de retiro y tiene un plazo para ir a la oficina
#   entregada  -> entrega presencial con carné + código + prueba de propiedad
#   rechazada / cancelada / vencida / descartada -> cerrada sin entrega
#
# Lo que escribió el estudiante (descripción, lugar, fecha, evidencia) no se
# puede modificar después de enviarlo: el usuario de la aplicación en
# PostgreSQL ni siquiera tiene permiso UPDATE sobre esas columnas.

from datetime import datetime, timezone

from app.extensions import db

ESTADOS_ABIERTOS = ('pendiente', 'preaprobada')


class EstadoSolicitud(db.Model):
    __tablename__ = 'estados_solicitud'

    codigo = db.Column(db.String(20), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    es_abierta = db.Column(db.Boolean, nullable=False)
    cuenta_como_rechazo = db.Column(db.Boolean, nullable=False)


class Solicitud(db.Model):
    __tablename__ = 'solicitudes'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    objeto_id = db.Column(db.Integer, db.ForeignKey('objetos.id'), nullable=False)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    reporte_perdida_id = db.Column(db.Integer, db.ForeignKey('objetos.id'), nullable=True)
    descripcion = db.Column(db.String(500), nullable=False)
    lugar_perdida = db.Column(db.String(150), nullable=False)
    fecha_perdida = db.Column(db.Date, nullable=False)
    evidencia = db.Column(db.String(300), nullable=False, server_default='')
    estado = db.Column(db.String(20), nullable=False, server_default='pendiente')
    revisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    revisado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    respuesta = db.Column(db.String(300), nullable=False, server_default='')
    preaprobada_en = db.Column(db.DateTime(timezone=True), nullable=True)
    vence_en = db.Column(db.DateTime(timezone=True), nullable=True)
    codigo_hash = db.Column(db.String(64), nullable=True)
    codigo_generado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    intentos_codigo = db.Column(db.SmallInteger, nullable=False, server_default='0')
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    objeto = db.relationship('Objeto', foreign_keys=[objeto_id])
    reporte_perdida = db.relationship('Objeto', foreign_keys=[reporte_perdida_id])
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id])
    revisado_por = db.relationship('Usuario', foreign_keys=[revisado_por_id])

    __mapper_args__ = {'version_id_col': version, 'eager_defaults': True}

    @property
    def esta_abierta(self):
        return self.estado in ESTADOS_ABIERTOS

    @property
    def tiene_codigo(self):
        return self.codigo_hash is not None

    def nombre_estado(self):
        estado = db.session.get(EstadoSolicitud, self.estado)
        return estado.nombre if estado else self.estado

    def dias_reporte_previo(self):
        """Evidencia fuerte de propiedad: cuántos días ANTES de que alguien
        reportara el objeto como encontrado, el estudiante había reportado
        la pérdida. La fecha la pone el sistema (created_at), no el usuario,
        así que no se puede falsificar. Negativo = reportó después."""
        if not self.reporte_perdida or not self.objeto:
            return None
        diferencia = self.objeto.created_at - self.reporte_perdida.created_at
        return diferencia.days

    def _base(self):
        return {
            'id': self.id,
            'objeto_id': self.objeto_id,
            'descripcion': self.descripcion,
            'lugar_perdida': self.lugar_perdida,
            'fecha_perdida': self.fecha_perdida.isoformat() if self.fecha_perdida else None,
            'evidencia': self.evidencia,
            'estado': self.estado,
            'estado_nombre': self.nombre_estado(),
            'respuesta': self.respuesta,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'preaprobada_en': self.preaprobada_en.isoformat() if self.preaprobada_en else None,
            'vence_en': self.vence_en.isoformat() if self.vence_en else None,
            'tiene_codigo': self.tiene_codigo,
            'reporte_perdida_id': self.reporte_perdida_id,
        }

    def vista_estudiante(self):
        """Para el propio estudiante. El objeto se muestra solo con su parte
        PÚBLICA (el estudiante nunca ve la descripción privada de lo que
        reclama: así no puede copiarla en otra reclamación)."""
        datos = self._base()
        datos['objeto'] = self.objeto.vista_publica() if self.objeto else None
        return datos

    def vista_oficina(self):
        """Para el encargado y el administrador: la reclamación al lado de los
        detalles privados del objeto, para comparar."""
        datos = self._base()
        datos.update({
            'objeto': self.objeto.vista_oficina() if self.objeto else None,
            'solicitante': {
                'id': self.solicitante.id,
                'nombre': self.solicitante.nombre_completo,
                'correo': self.solicitante.correo,
                'marcado_revision': self.solicitante.marcado_revision,
            } if self.solicitante else None,
            'reporte_perdida': {
                'id': self.reporte_perdida.id,
                'nombre': self.reporte_perdida.nombre,
                'descripcion': self.reporte_perdida.descripcion,
                'fecha_evento': self.reporte_perdida.fecha_evento.isoformat(),
                'created_at': self.reporte_perdida.created_at.isoformat(),
            } if self.reporte_perdida else None,
            'dias_reporte_previo': self.dias_reporte_previo(),
            'intentos_codigo': self.intentos_codigo,
            'revisado_por': self.revisado_por.nombre_completo if self.revisado_por else None,
            'revisado_en': self.revisado_en.isoformat() if self.revisado_en else None,
            'vencida': bool(self.vence_en and self.vence_en < datetime.now(timezone.utc)),
        })
        return datos
