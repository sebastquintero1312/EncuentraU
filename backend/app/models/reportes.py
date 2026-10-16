# Consultas sobre las VISTAS de estadísticas (migrations/sql/04_vistas.sql).
#
# Las vistas son de solo lectura y no exponen datos personales sensibles
# (salvo v_desempeno_encargados, que solo usa el administrador).

from sqlalchemy import text

from app.extensions import db


def _filas(sql, parametros=None):
    resultado = db.session.execute(text(sql), parametros or {})
    return [dict(fila._mapping) for fila in resultado]


def estadisticas_generales():
    filas = _filas('SELECT * FROM v_estadisticas_generales')
    return filas[0] if filas else {}


def estadisticas_mensuales(meses):
    filas = _filas(
        'SELECT mes, perdidos, encontrados, entregados FROM v_estadisticas_mensuales '
        'ORDER BY mes DESC LIMIT :meses',
        {'meses': meses},
    )
    for fila in filas:
        fila['mes'] = fila['mes'].isoformat()
    return list(reversed(filas))


def desempeno_encargados():
    filas = _filas('SELECT * FROM v_desempeno_encargados ORDER BY encargado')
    for fila in filas:
        if fila.get('horas_promedio_custodia') is not None:
            fila['horas_promedio_custodia'] = float(fila['horas_promedio_custodia'])
    return filas


def objetos_para_exportar():
    """Datos SIN información personal, pensados para abrir en Excel o en una
    herramienta de análisis (integración con otras aplicaciones)."""
    return _filas(
        """
        SELECT o.id, o.tipo, o.nombre, c.nombre AS categoria, u.nombre AS ubicacion,
               o.fecha_evento, e.nombre AS estado, o.created_at, o.recibido_en
        FROM objetos o
        JOIN categorias c ON c.id = o.categoria_id
        JOIN ubicaciones u ON u.id = o.ubicacion_id
        JOIN estados_objeto e ON e.tipo = o.tipo AND e.codigo = o.estado
        ORDER BY o.id
        """
    )
