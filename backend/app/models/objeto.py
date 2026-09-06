# Modelo de Objeto (reporte de objeto perdido o encontrado).
#
# Un "objeto" es el registro de un reporte hecho por un usuario. Puede ser
# de tipo 'perdido' o 'encontrado'. Ver docs/API.md y la skill
# objetos-perdidos para las reglas de negocio y las transiciones de estado.

from datetime import datetime

from app.extensions import db

TIPOS_VALIDOS = ('perdido', 'encontrado')
CATEGORIAS_VALIDAS = ('Tecnología', 'Accesorios', 'Útiles', 'Documentos', 'Ropa', 'Otro')
ESTADOS_VALIDOS = ('activo', 'en_proceso', 'resuelto', 'cerrado', 'cancelado')

# Transiciones de estado permitidas (origen -> destinos posibles)
TRANSICIONES_VALIDAS = {
    'activo': {'en_proceso', 'cancelado', 'cerrado'},
    'en_proceso': {'resuelto', 'activo', 'cerrado'},
    'resuelto': set(),
    'cerrado': set(),
    'cancelado': set(),
}


class Objeto(db.Model):
    __tablename__ = 'objetos'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    ubicacion = db.Column(db.String(150), nullable=False)
    fecha_evento = db.Column(db.Date, nullable=False)
    imagen_url = db.Column(db.String(500), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='activo', index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('objetos', lazy='dynamic'))

    __table_args__ = (
        db.CheckConstraint("tipo IN ('perdido','encontrado')", name='ck_objeto_tipo'),
        db.CheckConstraint(
            "estado IN ('activo','en_proceso','resuelto','cerrado','cancelado')",
            name='ck_objeto_estado',
        ),
    )

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in TRANSICIONES_VALIDAS.get(self.estado, set())

    def publico(self, incluir_correo_reportante=False):
        """Versión segura del objeto para la API pública: nunca expone el
        correo del reportante salvo que se pida explícitamente (ej. al dueño
        del propio reporte)."""
        datos = {
            'id': self.id,
            'tipo': self.tipo,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'descripcion': self.descripcion,
            'ubicacion': self.ubicacion,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None,
            'imagen_url': self.imagen_url,
            'estado': self.estado,
            'usuario_id': self.usuario_id,
            'usuario_nombre': f'{self.usuario.primer_nombre} {self.usuario.primer_apellido}'.strip() if self.usuario else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if incluir_correo_reportante and self.usuario:
            datos['usuario_correo'] = self.usuario.correo
        return datos
