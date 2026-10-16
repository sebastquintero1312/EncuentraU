"""La documentación de la API (docs/API.md) debe coincidir con el código.

Compara cada fila "| MÉTODO | `/api/...` |" de docs/API.md con las rutas
reales registradas en Flask. Si alguien agrega, quita o renombra un endpoint
sin actualizar la documentación (o al revés), esta prueba falla."""

import os
import re

RUTA_API_MD = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'API.md')
PATRON_FILA = re.compile(r'^\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*`(/api/[^`]*)`', re.MULTILINE)


def _rutas_documentadas():
    with open(RUTA_API_MD, encoding='utf-8') as archivo:
        return {(metodo, ruta) for metodo, ruta in PATRON_FILA.findall(archivo.read())}


def _rutas_reales(app):
    reales = set()
    for regla in app.url_map.iter_rules():
        if not regla.rule.startswith('/api/'):
            continue
        ruta = re.sub(r'<(?:\w+:)?(\w+)>', lambda m: '<id>' if m.group(1).endswith('_id') else f'<{m.group(1)}>', regla.rule)
        for metodo in regla.methods - {'HEAD', 'OPTIONS'}:
            reales.add((metodo, ruta))
    return reales


def test_cada_endpoint_real_esta_documentado(app):
    faltan = _rutas_reales(app) - _rutas_documentadas()
    assert not faltan, f'Endpoints sin documentar en docs/API.md: {sorted(faltan)}'


def test_no_se_documentan_endpoints_que_no_existen(app):
    sobran = _rutas_documentadas() - _rutas_reales(app)
    assert not sobran, f'docs/API.md documenta endpoints que no existen: {sorted(sobran)}'
