# Importa todos los modelos para que SQLAlchemy conozca todas las clases
# (y sus relaciones) antes de la primera consulta.
#
# El esquema NO se genera desde estas clases: lo crea la migración
# migrations/versions/0001_esquema_v2_postgresql.py a partir de los
# archivos SQL de migrations/sql/. Estas clases solo lo reflejan.

from app.models.usuario import Rol, Usuario
from app.models.catalogo import Categoria, Ubicacion, Parametro
from app.models.token_usuario import TokenUsuario
from app.models.objeto import EstadoObjeto, TransicionObjeto, Objeto
from app.models.solicitud import EstadoSolicitud, Solicitud
from app.models.entrega import Entrega
from app.models.notificacion import Notificacion
from app.models.auditoria import AuditoriaDetallada

__all__ = [
    'Rol', 'Usuario', 'Categoria', 'Ubicacion', 'Parametro', 'TokenUsuario',
    'EstadoObjeto', 'TransicionObjeto', 'Objeto', 'EstadoSolicitud', 'Solicitud',
    'Entrega', 'Notificacion', 'AuditoriaDetallada',
]
