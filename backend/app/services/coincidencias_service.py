# Lógica de POSIBLES COINCIDENCIAS entre un objeto perdido y uno encontrado.
#
# IMPORTANTE (ver skill objetos-perdidos): una coincidencia es solo una pista
# para ayudar a la persona a encontrar su objeto. NUNCA significa propiedad
# confirmada. La propiedad solo se confirma con la reclamación, la revisión
# del encargado y la entrega presencial.
#
# Seguridad: cuando la coincidencia se le muestra a un ESTUDIANTE, el puntaje
# se calcula solo con datos públicos (nombre, categoría, ubicación, fecha).
# Si usara la descripción privada del objeto encontrado, alguien podría
# crear reportes de pérdida con detalles inventados y ver cuál sube en la
# lista, adivinando así los detalles privados.

from datetime import timedelta

from app.models.objeto import ESTADOS_DISPONIBLES, TIPO_ENCONTRADO, TIPO_PERDIDO, Objeto

DIAS_ANTES = 3        # un objeto se puede encontrar antes de que su dueño note la pérdida
DIAS_DESPUES = 30     # ...o varias semanas después
MAXIMO_COINCIDENCIAS = 5
PUNTAJE_MINIMO_AVISO = 3  # para avisar por notificación, no solo mostrar


def _palabras(texto):
    return set(w.lower().strip('.,;:()') for w in (texto or '').split() if len(w) >= 4)


def _puntaje(perdido, encontrado, usar_descripciones):
    puntaje = 0
    if perdido.ubicacion_id == encontrado.ubicacion_id:
        puntaje += 3

    diferencia_dias = abs((encontrado.fecha_evento - perdido.fecha_evento).days)
    if diferencia_dias == 0:
        puntaje += 3
    elif diferencia_dias <= 3:
        puntaje += 2
    elif diferencia_dias <= 10:
        puntaje += 1

    texto_perdido = perdido.nombre
    texto_encontrado = encontrado.nombre
    if usar_descripciones:
        texto_perdido += ' ' + perdido.descripcion
        texto_encontrado += ' ' + encontrado.descripcion
    puntaje += min(len(_palabras(texto_perdido) & _palabras(texto_encontrado)), 3)
    return puntaje


def _ordenar(pares):
    pares = [par for par in pares if par[1] > 0]
    pares.sort(key=lambda par: (par[1], par[0].id), reverse=True)
    return pares[:MAXIMO_COINCIDENCIAS]


def encontrados_para_perdido(perdido):
    """Para el ESTUDIANTE dueño de un reporte de pérdida: objetos que están en
    la oficina y podrían ser el suyo. Devuelve [(objeto, puntaje)]."""
    if perdido is None or perdido.tipo != TIPO_PERDIDO or perdido.estado != 'buscando':
        return []
    candidatos = Objeto.query.filter(
        Objeto.tipo == TIPO_ENCONTRADO,
        Objeto.estado.in_(ESTADOS_DISPONIBLES),
        Objeto.categoria_id == perdido.categoria_id,
        Objeto.fecha_evento >= perdido.fecha_evento - timedelta(days=DIAS_ANTES),
        Objeto.fecha_evento <= perdido.fecha_evento + timedelta(days=DIAS_DESPUES),
    ).all()
    return _ordenar([(c, _puntaje(perdido, c, usar_descripciones=False)) for c in candidatos])


def perdidos_para_encontrado(encontrado):
    """Para la OFICINA: reportes de pérdida que podrían corresponder a un
    objeto encontrado. Aquí sí se usan las descripciones privadas (el
    encargado puede verlas). Devuelve [(objeto, puntaje)]."""
    if encontrado is None or encontrado.tipo != TIPO_ENCONTRADO:
        return []
    candidatos = Objeto.query.filter(
        Objeto.tipo == TIPO_PERDIDO,
        Objeto.estado == 'buscando',
        Objeto.categoria_id == encontrado.categoria_id,
        Objeto.fecha_evento >= encontrado.fecha_evento - timedelta(days=DIAS_DESPUES),
        Objeto.fecha_evento <= encontrado.fecha_evento + timedelta(days=DIAS_ANTES),
        Objeto.usuario_id != encontrado.usuario_id,
    ).all()
    return _ordenar([(c, _puntaje(c, encontrado, usar_descripciones=True)) for c in candidatos])


def duenos_a_avisar(encontrado):
    """Al recibir un objeto en la oficina se avisa a los estudiantes cuyo
    reporte de pérdida se parece. El aviso solo menciona datos públicos."""
    return [perdido.usuario for perdido, puntaje in perdidos_para_encontrado(encontrado)
            if puntaje >= PUNTAJE_MINIMO_AVISO]
