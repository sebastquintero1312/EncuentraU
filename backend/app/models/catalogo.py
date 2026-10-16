# Catálogos editables por el administrador (categorías y ubicaciones) y
# parámetros del negocio.
#
# Normalización: un reporte guarda solo categoria_id / ubicacion_id; el
# nombre vive una sola vez aquí. Renombrar una categoría la cambia en todos
# los reportes a la vez, sin actualizar ninguno.

from app.extensions import db


class Categoria(db.Model):
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, server_default=db.true())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    __mapper_args__ = {'eager_defaults': True}

    def a_dict(self):
        return {'id': self.id, 'nombre': self.nombre, 'activa': self.activa}


class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False, server_default='')
    activa = db.Column(db.Boolean, nullable=False, server_default=db.true())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    __mapper_args__ = {'eager_defaults': True}

    def a_dict(self):
        return {'id': self.id, 'nombre': self.nombre, 'descripcion': self.descripcion, 'activa': self.activa}


class Parametro(db.Model):
    __tablename__ = 'parametros'

    clave = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Integer, nullable=False)
    minimo = db.Column(db.Integer, nullable=False)
    maximo = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(),
                           server_onupdate=db.FetchedValue())

    __mapper_args__ = {'eager_defaults': True}

    def a_dict(self):
        return {
            'clave': self.clave,
            'valor': self.valor,
            'minimo': self.minimo,
            'maximo': self.maximo,
            'descripcion': self.descripcion,
        }


def categorias_activas():
    return Categoria.query.filter(Categoria.activa.is_(True)).order_by(Categoria.nombre).all()


def ubicaciones_activas():
    return Ubicacion.query.filter(Ubicacion.activa.is_(True)).order_by(Ubicacion.nombre).all()


def valor_parametro(clave):
    parametro = db.session.get(Parametro, clave)
    if parametro is None:
        raise RuntimeError(f'Parámetro de configuración inexistente: {clave}')
    return parametro.valor
