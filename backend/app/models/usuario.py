# Modelos de Rol y Usuario.
#
# v2.0: tres roles con permisos separados (ver docs/AUTHORIZATION.md):
#   estudiante     reporta objetos y reclama los suyos
#   encargado      recibe objetos en la oficina, verifica y entrega
#   administrador  gestiona usuarios, roles, catálogos y revisa la auditoría
#
# El esquema real (restricciones, triggers, permisos) está en
# migrations/sql/; estas clases solo lo reflejan para usarlo desde Python.

from app.extensions import db

ROL_ESTUDIANTE = 'estudiante'
ROL_ENCARGADO = 'encargado'
ROL_ADMINISTRADOR = 'administrador'
ROLES_VALIDOS = (ROL_ESTUDIANTE, ROL_ENCARGADO, ROL_ADMINISTRADOR)


class Rol(db.Model):
    __tablename__ = 'roles'

    codigo = db.Column(db.String(20), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    primer_nombre = db.Column(db.String(80), nullable=False)
    segundo_nombre = db.Column(db.String(80), nullable=False, server_default='')
    primer_apellido = db.Column(db.String(80), nullable=False)
    segundo_apellido = db.Column(db.String(80), nullable=False, server_default='')
    correo = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), db.ForeignKey('roles.codigo'), nullable=False, server_default=ROL_ESTUDIANTE)
    activo = db.Column(db.Boolean, nullable=False, server_default=db.true())
    correo_verificado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    marcado_revision = db.Column(db.Boolean, nullable=False, server_default=db.false())
    motivo_revision = db.Column(db.String(255), nullable=False, server_default='')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    # eager_defaults: tras un INSERT/UPDATE, PostgreSQL devuelve (RETURNING)
    # los valores que calculó él mismo (id, created_at, updated_at...).
    __mapper_args__ = {'eager_defaults': True}

    @property
    def correo_verificado(self):
        return self.correo_verificado_en is not None

    @property
    def nombre_completo(self):
        return f'{self.primer_nombre} {self.primer_apellido}'.strip()


def crear_usuario(datos, password_hash):
    """Todo usuario nuevo es estudiante y empieza con el correo SIN verificar.
    El rol nunca se toma de lo que envía el cliente."""
    usuario = Usuario(
        primer_nombre=datos['primer_nombre'],
        segundo_nombre=datos.get('segundo_nombre', '') or '',
        primer_apellido=datos['primer_apellido'],
        segundo_apellido=datos.get('segundo_apellido', '') or '',
        correo=datos['correo'].lower(),
        password_hash=password_hash,
        rol=ROL_ESTUDIANTE,
        activo=True,
    )
    db.session.add(usuario)
    db.session.flush()
    return usuario


def buscar_por_correo(correo):
    return Usuario.query.filter_by(correo=(correo or '').strip().lower()).first()


def buscar_por_id(usuario_id):
    return db.session.get(Usuario, usuario_id)


def usuarios_activos_con_rol(rol):
    return Usuario.query.filter(Usuario.rol == rol, Usuario.activo.is_(True)).all()


def usuario_publico(usuario):
    """Datos seguros para devolver por la API (nunca el hash de la contraseña)."""
    return {
        'id': usuario.id,
        'primer_nombre': usuario.primer_nombre,
        'primer_apellido': usuario.primer_apellido,
        'nombre_completo': usuario.nombre_completo,
        'correo': usuario.correo,
        'rol': usuario.rol,
        'activo': usuario.activo,
        'correo_verificado': usuario.correo_verificado,
    }


def usuario_para_admin(usuario):
    datos = usuario_publico(usuario)
    datos.update({
        'segundo_nombre': usuario.segundo_nombre,
        'segundo_apellido': usuario.segundo_apellido,
        'marcado_revision': usuario.marcado_revision,
        'motivo_revision': usuario.motivo_revision,
        'created_at': usuario.created_at.isoformat() if usuario.created_at else None,
    })
    return datos
