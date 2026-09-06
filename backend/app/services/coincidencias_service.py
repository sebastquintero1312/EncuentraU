# Lógica de POSIBLES COINCIDENCIAS entre un objeto perdido y uno encontrado.
#
# IMPORTANTE (ver skill objetos-perdidos): una coincidencia es solo una pista
# para ayudar a la persona a encontrar su objeto. NUNCA significa propiedad
# confirmada. La propiedad solo se confirma mediante el proceso de solicitud
# de reclamación y su revisión (ver solicitudes_service.py).

from datetime import timedelta

DIAS_VENTANA_FECHA = 14
MAXIMO_COINCIDENCIAS = 5


def _tipo_contrario(tipo):
    return 'encontrado' if tipo == 'perdido' else 'perdido'


def _palabras(texto):
    return set(w.lower() for w in (texto or '').split() if len(w) >= 4)


def _puntaje(objeto_origen, candidato):
    puntaje = 0

    if objeto_origen.ubicacion.strip().lower() == candidato.ubicacion.strip().lower():
        puntaje += 3
    elif objeto_origen.ubicacion.strip().lower() in candidato.ubicacion.strip().lower() or \
            candidato.ubicacion.strip().lower() in objeto_origen.ubicacion.strip().lower():
        puntaje += 1

    diferencia_dias = abs((objeto_origen.fecha_evento - candidato.fecha_evento).days)
    if diferencia_dias == 0:
        puntaje += 3
    elif diferencia_dias <= 3:
        puntaje += 2
    elif diferencia_dias <= DIAS_VENTANA_FECHA:
        puntaje += 1

    palabras_comunes = _palabras(objeto_origen.nombre + ' ' + objeto_origen.descripcion) & \
        _palabras(candidato.nombre + ' ' + candidato.descripcion)
    puntaje += min(len(palabras_comunes), 3)

    return puntaje


def encontrar_coincidencias(objeto_origen):
    """Devuelve hasta MAXIMO_COINCIDENCIAS objetos del tipo contrario, misma
    categoría, dentro de la ventana de fecha, ordenados por relevancia.
    Solo se consideran reportes todavía activos (no resueltos/cerrados)."""
    from app.models.objeto import Objeto

    if objeto_origen is None:
        return []

    fecha_min = objeto_origen.fecha_evento - timedelta(days=DIAS_VENTANA_FECHA)
    fecha_max = objeto_origen.fecha_evento + timedelta(days=DIAS_VENTANA_FECHA)

    candidatos = Objeto.query.filter(
        Objeto.tipo == _tipo_contrario(objeto_origen.tipo),
        Objeto.categoria == objeto_origen.categoria,
        Objeto.estado.in_(('activo', 'en_proceso')),
        Objeto.id != objeto_origen.id,
        Objeto.fecha_evento >= fecha_min,
        Objeto.fecha_evento <= fecha_max,
    ).all()

    calificados = [(c, _puntaje(objeto_origen, c)) for c in candidatos]
    calificados = [c for c in calificados if c[1] > 0]
    calificados.sort(key=lambda par: par[1], reverse=True)

    return [
        {**c.publico(), 'posible_coincidencia': True, 'puntaje_coincidencia': puntaje}
        for c, puntaje in calificados[:MAXIMO_COINCIDENCIAS]
    ]
