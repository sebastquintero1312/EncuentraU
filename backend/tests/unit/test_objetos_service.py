"""Pruebas unitarias de validación de app/services/objetos_service.py."""

import datetime

from app.services import objetos_service


def _datos_validos(**overrides):
    datos = {
        'tipo': 'perdido',
        'nombre': 'Mochila azul',
        'categoria': 'Accesorios',
        'descripcion': 'Mochila azul con laptop adentro',
        'ubicacion': 'Biblioteca central',
        'fecha_evento': datetime.date.today().isoformat(),
    }
    datos.update(overrides)
    return datos


def test_datos_validos_no_generan_errores():
    errores, limpio = objetos_service.validar_datos_objeto(_datos_validos())
    assert errores == {}
    assert limpio['nombre'] == 'Mochila azul'


def test_nombre_vacio_genera_error():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(nombre=''))
    assert 'nombre' in errores


def test_categoria_invalida_genera_error():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(categoria='Inventada'))
    assert 'categoria' in errores


def test_descripcion_muy_corta_genera_error():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(descripcion='corta'))
    assert 'descripcion' in errores


def test_tipo_invalido_genera_error():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(tipo='robado'))
    assert 'tipo' in errores


def test_fecha_futura_genera_error():
    fecha_futura = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(fecha_evento=fecha_futura))
    assert 'fecha_evento' in errores


def test_fecha_con_formato_invalido_genera_error():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(fecha_evento='no-es-una-fecha'))
    assert 'fecha_evento' in errores


def test_imagen_url_no_http_rechazada():
    errores, _ = objetos_service.validar_datos_objeto(_datos_validos(imagen_url='javascript:alert(1)'))
    assert 'imagen_url' in errores
