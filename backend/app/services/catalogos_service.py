# Administración de catálogos (categorías y ubicaciones) y de los
# parámetros del negocio.
#
# Nada se borra: una categoría o ubicación que ya no se usa se DESACTIVA
# (deja de aparecer en los formularios), porque puede haber reportes que la
# referencian (la clave foránea lo impediría de todos modos).

from app.extensions import db
from app.models.catalogo import Categoria, Parametro, Ubicacion
from app.utils import texto

LIMITES = {
    'categoria': {'nombre': (3, 50)},
    'ubicacion': {'nombre': (3, 80), 'descripcion': (0, 200)},
}


def _validar_texto(datos, campo, minimo, maximo, errores, obligatorio):
    if campo not in datos:
        if obligatorio:
            errores[campo] = 'Este campo es obligatorio'
        return None
    valor = texto(datos.get(campo))
    if not (minimo <= len(valor) <= maximo):
        errores[campo] = f'Debe tener entre {minimo} y {maximo} caracteres'
        return None
    return valor


def _validar_activa(datos, errores):
    if 'activa' not in datos:
        return None
    if not isinstance(datos.get('activa'), bool):
        errores['activa'] = 'El campo "activa" debe ser verdadero o falso'
        return None
    return datos.get('activa')


def listar(modelo):
    return modelo.query.order_by(modelo.activa.desc(), modelo.nombre).all()


def crear_categoria(datos):
    errores = {}
    nombre = _validar_texto(datos, 'nombre', *LIMITES['categoria']['nombre'], errores, obligatorio=True)
    if errores:
        return errores, None
    categoria = Categoria(nombre=nombre)
    db.session.add(categoria)
    db.session.commit()  # un nombre repetido lo rechaza el índice único (409)
    return {}, categoria


def actualizar_categoria(categoria, datos):
    errores = {}
    nombre = _validar_texto(datos, 'nombre', *LIMITES['categoria']['nombre'], errores, obligatorio=False)
    activa = _validar_activa(datos, errores)
    if errores:
        return errores
    if nombre is not None:
        categoria.nombre = nombre
    if activa is not None:
        categoria.activa = activa
    db.session.commit()
    return {}


def crear_ubicacion(datos):
    errores = {}
    nombre = _validar_texto(datos, 'nombre', *LIMITES['ubicacion']['nombre'], errores, obligatorio=True)
    descripcion = _validar_texto(datos, 'descripcion', *LIMITES['ubicacion']['descripcion'], errores, obligatorio=False)
    if errores:
        return errores, None
    ubicacion = Ubicacion(nombre=nombre, descripcion=descripcion or '')
    db.session.add(ubicacion)
    db.session.commit()
    return {}, ubicacion


def actualizar_ubicacion(ubicacion, datos):
    errores = {}
    nombre = _validar_texto(datos, 'nombre', *LIMITES['ubicacion']['nombre'], errores, obligatorio=False)
    descripcion = _validar_texto(datos, 'descripcion', *LIMITES['ubicacion']['descripcion'], errores, obligatorio=False)
    activa = _validar_activa(datos, errores)
    if errores:
        return errores
    if nombre is not None:
        ubicacion.nombre = nombre
    if descripcion is not None:
        ubicacion.descripcion = descripcion
    if activa is not None:
        ubicacion.activa = activa
    db.session.commit()
    return {}


def listar_parametros():
    return Parametro.query.order_by(Parametro.clave).all()


def actualizar_parametro(parametro, datos):
    valor = datos.get('valor')
    if isinstance(valor, bool) or not isinstance(valor, int):
        return {'valor': 'El valor debe ser un número entero'}
    if not (parametro.minimo <= valor <= parametro.maximo):
        return {'valor': f'El valor debe estar entre {parametro.minimo} y {parametro.maximo}'}
    parametro.valor = valor
    db.session.commit()
    return {}
