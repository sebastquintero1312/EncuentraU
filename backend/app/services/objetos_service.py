# Reglas de negocio de reportes de objetos perdidos/encontrados.
#
# Igual que auth_service: esta es la validación DEFINITIVA. El frontend
# valida solo para dar buena experiencia, nunca hay que confiar en lo que
# llega del navegador.

from datetime import date, datetime

from app.extensions import db
from app.models.objeto import Objeto, TIPOS_VALIDOS, CATEGORIAS_VALIDAS, ESTADOS_VALIDOS

LONGITUD_MIN_NOMBRE = 3
LONGITUD_MAX_NOMBRE = 120
LONGITUD_MIN_DESCRIPCION = 10
LONGITUD_MAX_DESCRIPCION = 300
LONGITUD_MIN_UBICACION = 3
LONGITUD_MAX_UBICACION = 150

# Campos que un usuario puede escribir al crear o editar un reporte.
# Todo lo que no está aquí (estado, usuario_id, id, created_at...) se ignora
# aunque venga en el body: es una whitelist explícita contra mass assignment.
CAMPOS_EDITABLES = ('nombre', 'categoria', 'descripcion', 'ubicacion', 'fecha_evento', 'imagen_url')


def _texto(valor):
    return (valor or '').strip() if isinstance(valor, str) else ''


def validar_datos_objeto(datos, requiere_tipo=True):
    """Devuelve (errores: dict, valores_limpios: dict)."""
    errores = {}
    limpio = {}

    if requiere_tipo:
        tipo = _texto(datos.get('tipo'))
        if tipo not in TIPOS_VALIDOS:
            errores['tipo'] = 'El tipo debe ser "perdido" o "encontrado"'
        else:
            limpio['tipo'] = tipo

    nombre = _texto(datos.get('nombre'))
    if not (LONGITUD_MIN_NOMBRE <= len(nombre) <= LONGITUD_MAX_NOMBRE):
        errores['nombre'] = f'El nombre debe tener entre {LONGITUD_MIN_NOMBRE} y {LONGITUD_MAX_NOMBRE} caracteres'
    else:
        limpio['nombre'] = nombre

    categoria = _texto(datos.get('categoria'))
    if categoria not in CATEGORIAS_VALIDAS:
        errores['categoria'] = 'Selecciona una categoría válida'
    else:
        limpio['categoria'] = categoria

    descripcion = _texto(datos.get('descripcion'))
    if not (LONGITUD_MIN_DESCRIPCION <= len(descripcion) <= LONGITUD_MAX_DESCRIPCION):
        errores['descripcion'] = f'La descripción debe tener entre {LONGITUD_MIN_DESCRIPCION} y {LONGITUD_MAX_DESCRIPCION} caracteres'
    else:
        limpio['descripcion'] = descripcion

    ubicacion = _texto(datos.get('ubicacion'))
    if not (LONGITUD_MIN_UBICACION <= len(ubicacion) <= LONGITUD_MAX_UBICACION):
        errores['ubicacion'] = f'La ubicación debe tener entre {LONGITUD_MIN_UBICACION} y {LONGITUD_MAX_UBICACION} caracteres'
    else:
        limpio['ubicacion'] = ubicacion

    fecha_texto = _texto(datos.get('fecha_evento'))
    if not fecha_texto:
        errores['fecha_evento'] = 'La fecha es obligatoria'
    else:
        try:
            fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
            if fecha > date.today():
                errores['fecha_evento'] = 'La fecha no puede ser futura'
            else:
                limpio['fecha_evento'] = fecha
        except ValueError:
            errores['fecha_evento'] = 'La fecha debe tener formato AAAA-MM-DD'

    imagen_url = datos.get('imagen_url')
    if imagen_url:
        imagen_url = _texto(imagen_url)
        if len(imagen_url) > 500 or not (imagen_url.startswith('http://') or imagen_url.startswith('https://')):
            errores['imagen_url'] = 'La imagen debe ser una URL http(s) válida'
        else:
            limpio['imagen_url'] = imagen_url

    return errores, limpio


def crear_objeto(usuario_id, datos):
    errores, limpio = validar_datos_objeto(datos, requiere_tipo=True)
    if errores:
        return errores, None

    objeto = Objeto(
        tipo=limpio['tipo'],
        nombre=limpio['nombre'],
        categoria=limpio['categoria'],
        descripcion=limpio['descripcion'],
        ubicacion=limpio['ubicacion'],
        fecha_evento=limpio['fecha_evento'],
        imagen_url=limpio.get('imagen_url'),
        estado='activo',
        usuario_id=usuario_id,
    )
    db.session.add(objeto)
    db.session.commit()
    return {}, objeto


def actualizar_objeto(objeto, datos):
    errores, limpio = validar_datos_objeto(datos, requiere_tipo=False)
    if errores:
        return errores

    for campo in CAMPOS_EDITABLES:
        if campo in limpio:
            setattr(objeto, campo, limpio[campo])
    db.session.commit()
    return {}


def cancelar_objeto(objeto):
    if not objeto.puede_transicionar_a('cancelado'):
        return False
    objeto.estado = 'cancelado'
    db.session.commit()
    return True


def cambiar_estado_admin(objeto, nuevo_estado):
    if nuevo_estado not in ESTADOS_VALIDOS:
        return False, 'Estado inválido'
    if not objeto.puede_transicionar_a(nuevo_estado):
        return False, f'No se puede pasar de "{objeto.estado}" a "{nuevo_estado}"'
    objeto.estado = nuevo_estado
    db.session.commit()
    return True, None


def buscar_objetos(filtros, pagina, por_pagina):
    query = Objeto.query

    tipo = filtros.get('tipo')
    if tipo in TIPOS_VALIDOS:
        query = query.filter(Objeto.tipo == tipo)

    categoria = filtros.get('categoria')
    if categoria in CATEGORIAS_VALIDAS:
        query = query.filter(Objeto.categoria == categoria)

    estado = filtros.get('estado')
    if estado in ESTADOS_VALIDOS:
        query = query.filter(Objeto.estado == estado)
    else:
        # Por defecto, la búsqueda pública solo muestra reportes activos.
        query = query.filter(Objeto.estado.in_(('activo', 'en_proceso')))

    ubicacion = _texto(filtros.get('ubicacion'))
    if ubicacion:
        query = query.filter(Objeto.ubicacion.ilike(f'%{ubicacion}%'))

    texto = _texto(filtros.get('q'))
    if texto:
        patron = f'%{texto}%'
        query = query.filter(db.or_(Objeto.nombre.ilike(patron), Objeto.descripcion.ilike(patron)))

    query = query.order_by(Objeto.created_at.desc())
    paginado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    return paginado
