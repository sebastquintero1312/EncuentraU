# Lectura de la auditoría.
#
# Las filas las escribe SOLO el trigger fn_auditoria() de PostgreSQL; la
# aplicación únicamente puede leerlas (ver migrations/sql/06_permisos.sql).
# Esta clase se mapea sobre la VISTA v_auditoria_detallada, que agrega el
# nombre de quien hizo cada cambio. Es de solo lectura.

from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB

TABLAS_AUDITADAS = (
    'usuarios', 'tokens_usuario', 'objetos', 'solicitudes', 'entregas',
    'categorias', 'ubicaciones', 'parametros',
)
OPERACIONES = ('INSERT', 'UPDATE', 'DELETE')


class AuditoriaDetallada(db.Model):
    __tablename__ = 'v_auditoria_detallada'

    id = db.Column(db.BigInteger, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True))
    tabla = db.Column(db.String(63))
    registro_id = db.Column(db.BigInteger)
    operacion = db.Column(db.String(10))
    usuario_id = db.Column(db.Integer)
    usuario_nombre = db.Column(db.String(200))
    usuario_correo = db.Column(db.String(255))
    usuario_rol = db.Column(db.String(20))
    ip = db.Column(INET)
    campos_modificados = db.Column(ARRAY(db.Text))
    datos_anteriores = db.Column(JSONB)
    datos_nuevos = db.Column(JSONB)
    transaccion_id = db.Column(db.BigInteger)

    # Es una vista: SQLAlchemy nunca debe intentar crearla como tabla.
    __table_args__ = {'info': {'es_vista': True}}

    def a_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'tabla': self.tabla,
            'registro_id': self.registro_id,
            'operacion': self.operacion,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario_nombre,
            'usuario_correo': self.usuario_correo,
            'usuario_rol': self.usuario_rol,
            'ip': str(self.ip) if self.ip else None,
            'campos_modificados': self.campos_modificados or [],
            'datos_anteriores': self.datos_anteriores,
            'datos_nuevos': self.datos_nuevos,
            'transaccion_id': self.transaccion_id,
        }
