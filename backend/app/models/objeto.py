# Modelo de Objeto (reporte de objeto perdido o encontrado).
#
# Verificación a ciegas (ver docs/AUTHORIZATION.md): cada reporte tiene una
# parte PÚBLICA (nombre genérico, categoría, ubicación, fecha) y una parte
# PRIVADA (descripción con marca, color, señas). La parte privada solo la ven
# quien hizo el reporte, el encargado y el administrador. Por eso existen
# tres formas distintas de convertir un objeto a JSON (vista_publica,
# vista_propietario, vista_oficina): cada una se usa según quién pregunta.
#
# Estados y transiciones: viven como DATOS en las tablas estados_objeto y
# transiciones_objeto, y un trigger de PostgreSQL rechaza cualquier cambio de
# estado que no esté permitido (ver migrations/sql/02_funciones_triggers.sql).

from app.extensions import db

TIPO_PERDIDO = 'perdido'
TIPO_ENCONTRADO = 'encontrado'
TIPOS_VALIDOS = (TIPO_PERDIDO, TIPO_ENCONTRADO)

ESTADO_INICIAL = {TIPO_PERDIDO: 'buscando', TIPO_ENCONTRADO: 'pendiente_entrega'}
# Objetos encontrados que están físicamente en la oficina: los únicos que un
# estudiante puede ver en la búsqueda y reclamar.
ESTADOS_DISPONIBLES = ('en_oficina', 'reservado')


class EstadoObjeto(db.Model):
    __tablename__ = 'estados_objeto'

    tipo = db.Column(db.String(20), primary_key=True)
    codigo = db.Column(db.String(20), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    es_inicial = db.Column(db.Boolean, nullable=False)
    es_final = db.Column(db.Boolean, nullable=False)


class TransicionObjeto(db.Model):
    __tablename__ = 'transiciones_objeto'

    tipo = db.Column(db.String(20), primary_key=True)
    estado_origen = db.Column(db.String(20), primary_key=True)
    estado_destino = db.Column(db.String(20), primary_key=True)
    actor = db.Column(db.String(20), nullable=False)


def transicion_permitida(tipo, origen, destino, actor):
    return db.session.query(TransicionObjeto.tipo).filter_by(
        tipo=tipo, estado_origen=origen, estado_destino=destino, actor=actor,
    ).first() is not None


class Objeto(db.Model):
    __tablename__ = 'objetos'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'), nullable=False)
    fecha_evento = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    detalle_ubicacion = db.Column(db.String(150), nullable=False, server_default='')
    estado = db.Column(db.String(20), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    recibido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    recibido_en = db.Column(db.DateTime(timezone=True), nullable=True)
    observaciones_custodia = db.Column(db.String(500), nullable=False, server_default='')
    motivo_cierre = db.Column(db.String(300), nullable=False, server_default='')
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    categoria = db.relationship('Categoria')
    ubicacion = db.relationship('Ubicacion')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    recibido_por = db.relationship('Usuario', foreign_keys=[recibido_por_id])

    # version_id_col: control de concurrencia OPTIMISTA. SQLAlchemy agrega
    # "AND version = <la que leí>" a cada UPDATE; si otra transacción cambió
    # la fila en el medio, el UPDATE no afecta ninguna fila y se lanza
    # StaleDataError (la API responde 409 Conflict).
    __mapper_args__ = {'version_id_col': version, 'eager_defaults': True}

    @property
    def disponible_para_reclamar(self):
        return self.tipo == TIPO_ENCONTRADO and self.estado in ESTADOS_DISPONIBLES

    def nombre_estado(self):
        estado = db.session.get(EstadoObjeto, (self.tipo, self.estado))
        return estado.nombre if estado else self.estado

    def vista_publica(self):
        """Lo que puede ver cualquier estudiante. SIN descripción privada y
        sin datos de quién lo reportó."""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'nombre': self.nombre,
            'categoria': self.categoria.nombre if self.categoria else None,
            'categoria_id': self.categoria_id,
            'ubicacion': self.ubicacion.nombre if self.ubicacion else None,
            'ubicacion_id': self.ubicacion_id,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None,
            'estado': self.estado,
            'estado_nombre': self.nombre_estado(),
            'recibido_en': self.recibido_en.isoformat() if self.recibido_en else None,
        }

    def vista_propietario(self):
        """Para quien hizo el reporte: incluye su propia descripción privada."""
        datos = self.vista_publica()
        datos.update({
            'descripcion': self.descripcion,
            'detalle_ubicacion': self.detalle_ubicacion,
            'motivo_cierre': self.motivo_cierre,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        })
        return datos

    def vista_oficina(self):
        """Para el encargado y el administrador: todo, incluido quién lo
        reportó y quién lo recibió en la oficina."""
        datos = self.vista_propietario()
        datos.update({
            'observaciones_custodia': self.observaciones_custodia,
            'reportado_por': {
                'id': self.usuario.id,
                'nombre': self.usuario.nombre_completo,
                'correo': self.usuario.correo,
            } if self.usuario else None,
            'recibido_por': self.recibido_por.nombre_completo if self.recibido_por else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        })
        return datos
