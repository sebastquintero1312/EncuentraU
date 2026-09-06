# Importa todos los modelos para que Flask-Migrate/Alembic los detecte al
# generar migraciones (autogenerate necesita que las clases ya estén
# registradas contra db.metadata en el momento de ejecutarse).

from app.models.usuario import Usuario
from app.models.token_recuperacion import TokenRecuperacion
from app.models.objeto import Objeto
from app.models.solicitud import Solicitud

__all__ = ['Usuario', 'TokenRecuperacion', 'Objeto', 'Solicitud']
