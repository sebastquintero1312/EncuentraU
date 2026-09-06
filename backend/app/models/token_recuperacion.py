# Modelo de Token de recuperación de contraseña.
#
# v1.0: se guarda en la base de datos real, con índice único por token y
# referencia (FK) al usuario dueño del token.

from datetime import datetime, timedelta

from app.extensions import db


class TokenRecuperacion(db.Model):
    __tablename__ = 'tokens_recuperacion'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    expira_en = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def crear_token(token, usuario_id, minutos_expiracion):
    registro = TokenRecuperacion(
        token=token,
        usuario_id=usuario_id,
        expira_en=datetime.utcnow() + timedelta(minutes=minutos_expiracion),
        usado=False,
    )
    db.session.add(registro)
    db.session.commit()
    return registro


def buscar_token(token):
    return TokenRecuperacion.query.filter_by(token=token).first()


def token_es_valido(registro):
    if registro is None:
        return False
    if registro.usado:
        return False
    if datetime.utcnow() > registro.expira_en:
        return False
    return True


def invalidar_token(registro):
    registro.usado = True
    db.session.commit()
