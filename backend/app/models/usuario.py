# Modelo de Usuario.
#
# v1.0: los usuarios viven en una base de datos real (SQLAlchemy), ya no en
# una lista en memoria. Se mantienen las mismas funciones de ayuda que ya
# usaban los controladores (crear_usuario, buscar_por_correo, buscar_por_id,
# usuario_publico) para que la migración no cambie el resto del backend.

from datetime import datetime

from app.extensions import db

ROLES_VALIDOS = ('ciudadano', 'administrador')


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    primer_nombre = db.Column(db.String(80), nullable=False)
    segundo_nombre = db.Column(db.String(80), nullable=False, default='')
    primer_apellido = db.Column(db.String(80), nullable=False)
    segundo_apellido = db.Column(db.String(80), nullable=False, default='')
    correo = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='ciudadano')
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("rol IN ('ciudadano', 'administrador')", name='ck_usuario_rol'),
    )


def crear_usuario(datos, password_hash):
    usuario = Usuario(
        primer_nombre=datos['primer_nombre'],
        segundo_nombre=datos.get('segundo_nombre', '') or '',
        primer_apellido=datos['primer_apellido'],
        segundo_apellido=datos.get('segundo_apellido', '') or '',
        correo=datos['correo'].lower(),
        password_hash=password_hash,
        rol='ciudadano',
        activo=True,
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def buscar_por_correo(correo):
    return Usuario.query.filter_by(correo=correo.lower()).first()


def buscar_por_id(usuario_id):
    return db.session.get(Usuario, usuario_id)


def usuario_publico(usuario):
    # Versión del usuario segura para devolver por la API (sin password_hash)
    return {
        'id': usuario.id,
        'primer_nombre': usuario.primer_nombre,
        'primer_apellido': usuario.primer_apellido,
        'correo': usuario.correo,
        'rol': usuario.rol,
        'activo': usuario.activo,
    }
