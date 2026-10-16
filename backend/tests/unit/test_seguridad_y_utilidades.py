"""Pruebas unitarias de app/seguridad.py y app/utils.py."""

from datetime import timedelta

from app import seguridad
from app.services.coincidencias_service import _palabras
from app.services.objetos_service import patron_busqueda
from app.services.auditoria_service import _celda_segura
from app.utils import entero_o_none, fecha_o_none, hoy_en_colombia, validar_fecha_pasada


def test_token_es_largo_y_distinto_cada_vez():
    tokens = {seguridad.generar_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(t) >= 40 for t in tokens)


def test_hash_de_token_es_sha256_y_no_contiene_el_token():
    token = seguridad.generar_token()
    hash_token = seguridad.hash_token(token)
    assert len(hash_token) == 64
    assert token not in hash_token
    assert seguridad.hash_token(token) == hash_token  # determinista


def test_codigo_de_retiro_tiene_6_digitos():
    for _ in range(200):
        codigo = seguridad.generar_codigo_retiro()
        assert seguridad.codigo_retiro_con_formato_valido(codigo)


def test_formato_de_codigo_invalido():
    for valor in ('12345', '1234567', 'abcdef', '12 456', None, 123456):
        assert not seguridad.codigo_retiro_con_formato_valido(valor)


def test_hash_de_codigo_depende_de_la_secret_key(app):
    with app.app_context():
        hash_1 = seguridad.hash_codigo_retiro('123456')
        app.config['SECRET_KEY'] = 'otra-clave-distinta-para-esta-prueba-0123456789'
        hash_2 = seguridad.hash_codigo_retiro('123456')
    # Sin la SECRET_KEY, el hash de un código de 6 dígitos no se puede
    # recalcular aunque alguien robe la base de datos.
    assert hash_1 != hash_2


def test_entero_o_none_rechaza_booleanos_y_negativos():
    assert entero_o_none(5) == 5
    assert entero_o_none('7') == 7
    assert entero_o_none(True) is None   # en Python, True es un int
    assert entero_o_none(-3) is None
    assert entero_o_none(0) is None
    assert entero_o_none('1 OR 1=1') is None
    assert entero_o_none([1]) is None


def test_fecha_o_none():
    assert fecha_o_none('2026-10-01').isoformat() == '2026-10-01'
    assert fecha_o_none('01/10/2026') is None
    assert fecha_o_none(20261001) is None


def test_validar_fecha_pasada_rechaza_futuro():
    errores = {}
    manana = (hoy_en_colombia() + timedelta(days=1)).isoformat()
    assert validar_fecha_pasada(manana, errores, 'fecha') is None
    assert 'futura' in errores['fecha']


def test_patron_busqueda_escapa_comodines():
    assert patron_busqueda('50%') == '%50\\%%'
    assert patron_busqueda('a_b') == '%a\\_b%'
    assert len(patron_busqueda('x' * 500)) <= 82


def test_celda_csv_evita_inyeccion_de_formulas():
    assert _celda_segura('=HYPERLINK("http://malo")') == '\'=HYPERLINK("http://malo")'
    assert _celda_segura('+1') == "'+1"
    assert _celda_segura('@SUM(A1)') == "'@SUM(A1)"
    assert _celda_segura('Celular') == 'Celular'
    assert _celda_segura(None) == ''


def test_palabras_ignora_cortas_y_puntuacion():
    assert _palabras('Celular negro, con funda.') == {'celular', 'negro', 'funda'}
