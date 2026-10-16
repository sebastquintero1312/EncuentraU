# Utilidades pequeñas y compartidas entre controladores y servicios.

from datetime import date, datetime

from app.config.config import Config, ZONA_HORARIA_COLOMBIA


def parametros_paginacion(request):
    try:
        pagina = int(request.args.get('pagina', 1))
    except (TypeError, ValueError):
        pagina = 1
    try:
        por_pagina = int(request.args.get('por_pagina', Config.RESULTADOS_POR_PAGINA_DEFECTO))
    except (TypeError, ValueError):
        por_pagina = Config.RESULTADOS_POR_PAGINA_DEFECTO

    pagina = max(pagina, 1)
    por_pagina = min(max(por_pagina, 1), Config.RESULTADOS_POR_PAGINA_MAXIMO)
    return pagina, por_pagina


def respuesta_paginada(paginado, pagina, por_pagina, serializar):
    return {
        'datos': [serializar(item) for item in paginado.items],
        'total': paginado.total,
        'pagina': pagina,
        'por_pagina': por_pagina,
    }


def texto(valor):
    """Texto limpio. Cualquier cosa que no sea un string se trata como vacío
    (un atacante puede mandar listas, números u objetos en el JSON)."""
    return valor.strip() if isinstance(valor, str) else ''


def entero_o_none(valor):
    """Convierte a entero positivo, o devuelve None si no es válido. Rechaza
    booleanos (en Python, True es un int)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor if valor > 0 else None
    if isinstance(valor, str) and valor.strip().isdigit():
        numero = int(valor.strip())
        return numero if numero > 0 else None
    return None


def hoy_en_colombia():
    return datetime.now(ZONA_HORARIA_COLOMBIA).date()


def fecha_o_none(valor):
    """Fecha en formato AAAA-MM-DD, o None si no es válida."""
    valor = texto(valor)
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


def validar_fecha_pasada(valor, errores, campo, obligatoria=True):
    """Valida una fecha que no puede ser futura (hora de Colombia)."""
    if not texto(valor):
        if obligatoria:
            errores[campo] = 'La fecha es obligatoria'
        return None
    fecha = fecha_o_none(valor)
    if fecha is None:
        errores[campo] = 'La fecha debe tener formato AAAA-MM-DD'
        return None
    if fecha > hoy_en_colombia():
        errores[campo] = 'La fecha no puede ser futura'
        return None
    if fecha < date(2000, 1, 1):
        errores[campo] = 'La fecha no es válida'
        return None
    return fecha
