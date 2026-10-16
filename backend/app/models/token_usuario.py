# Tokens de un solo uso: verificación de correo y recuperación de contraseña.
#
# Seguridad: en la base de datos se guarda solo el HASH (SHA-256) del token.
# El token en claro solo existe en el enlace que recibe la persona por correo.
# Si alguien robara una copia de la base de datos, no podría usar los enlaces.

from datetime import datetime, timezone

from app.extensions import db

PROPOSITO_VERIFICACION = 'verificacion'
PROPOSITO_RECUPERACION = 'recuperacion'


class TokenUsuario(db.Model):
    __tablename__ = 'tokens_usuario'

    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proposito = db.Column(db.String(20), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    expira_en = db.Column(db.DateTime(timezone=True), nullable=False)
    usado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    usuario = db.relationship('Usuario')

    __mapper_args__ = {'eager_defaults': True}

    def es_valido(self):
        return self.usado_en is None and datetime.now(timezone.utc) < self.expira_en


def crear_token(usuario_id, proposito, token_hash, expira_en):
    registro = TokenUsuario(usuario_id=usuario_id, proposito=proposito, token_hash=token_hash, expira_en=expira_en)
    db.session.add(registro)
    db.session.flush()
    return registro


def buscar_token(token_hash, proposito):
    return TokenUsuario.query.filter_by(token_hash=token_hash, proposito=proposito).first()


def invalidar_tokens_pendientes(usuario_id, proposito):
    """Marca como usados los tokens anteriores sin usar (solo vale el último)."""
    ahora = datetime.now(timezone.utc)
    pendientes = TokenUsuario.query.filter(
        TokenUsuario.usuario_id == usuario_id,
        TokenUsuario.proposito == proposito,
        TokenUsuario.usado_en.is_(None),
    ).all()
    for token in pendientes:
        token.usado_en = ahora
