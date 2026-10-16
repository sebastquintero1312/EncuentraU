"""Guardrails de configuración (deny by default): la aplicación se niega a
arrancar con una configuración insegura o incompleta."""

import pytest

from app.config.config import CLAVE_INSEGURA_POR_DEFECTO, Config, modo_debug_permitido

CONFIG_PRODUCCION_VALIDA = {
    'SQLALCHEMY_DATABASE_URI': 'postgresql://usuario:clave@servidor:5432/encuentrau',
    'SECRET_KEY': 'una-clave-larga-y-aleatoria-0123456789abcdef',
    'CORREO_PROVEEDOR': 'brevo',
    'BREVO_API_KEY': 'clave-de-api',
    'CORREO_REMITENTE': 'encuentrau@ejemplo.com',
    'URL_PUBLICA': 'https://encuentrau.onrender.com',
}


@pytest.fixture()
def en_produccion(monkeypatch):
    monkeypatch.setattr(Config, 'ES_PRODUCCION', True)


def test_rechaza_arrancar_sin_postgresql():
    for url in ('', 'sqlite:///encuentrau.db', 'mysql://x@y/z'):
        with pytest.raises(RuntimeError, match='PostgreSQL'):
            Config.validar_configuracion({'SQLALCHEMY_DATABASE_URI': url, 'CORREO_PROVEEDOR': 'consola'})


def test_rechaza_proveedor_de_correo_desconocido():
    with pytest.raises(RuntimeError, match='CORREO_PROVEEDOR'):
        Config.validar_configuracion({'SQLALCHEMY_DATABASE_URI': 'postgresql://x@y/z', 'CORREO_PROVEEDOR': 'smtp'})


def test_produccion_valida_arranca(en_produccion):
    Config.validar_configuracion(dict(CONFIG_PRODUCCION_VALIDA))


def test_produccion_rechaza_secret_key_insegura(en_produccion):
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        Config.validar_configuracion(dict(CONFIG_PRODUCCION_VALIDA, SECRET_KEY=CLAVE_INSEGURA_POR_DEFECTO))


def test_produccion_exige_correos_reales(en_produccion):
    # El modo "consola" escribiría los enlaces de verificación en los logs
    with pytest.raises(RuntimeError, match='brevo'):
        Config.validar_configuracion(dict(CONFIG_PRODUCCION_VALIDA, CORREO_PROVEEDOR='consola'))
    with pytest.raises(RuntimeError, match='BREVO_API_KEY'):
        Config.validar_configuracion(dict(CONFIG_PRODUCCION_VALIDA, BREVO_API_KEY=''))


def test_produccion_exige_https(en_produccion):
    with pytest.raises(RuntimeError, match='https'):
        Config.validar_configuracion(dict(CONFIG_PRODUCCION_VALIDA, URL_PUBLICA='http://encuentrau.onrender.com'))


def test_produccion_cookie_segura_y_hsts():
    """SESSION_COOKIE_SECURE depende de ES_PRODUCCION; HSTS solo se envía en
    producción (en desarrollo por HTTP rompería el acceso local)."""
    assert Config.SESSION_COOKIE_SECURE == Config.ES_PRODUCCION
    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert Config.SESSION_COOKIE_SAMESITE == 'Lax'


def test_debug_solo_con_development_explicito():
    """Regresión (bug heredado de v1.0): si FLASK_ENV no estaba definida,
    app.py activaba el debugger interactivo."""
    assert modo_debug_permitido({}) is False
    assert modo_debug_permitido({'FLASK_ENV': ''}) is False
    assert modo_debug_permitido({'FLASK_ENV': 'production'}) is False
    assert modo_debug_permitido({'FLASK_ENV': 'Development'}) is False
    assert modo_debug_permitido({'FLASK_ENV': 'development'}) is True


def test_sin_hsts_fuera_de_produccion(client):
    assert 'Strict-Transport-Security' not in client.get('/health').headers
