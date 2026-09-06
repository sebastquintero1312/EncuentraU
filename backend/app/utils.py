# Utilidades pequeñas y compartidas entre controladores.

from app.config.config import Config


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
