# Reglas de negocio de los reportes de objetos perdidos y encontrados.
#
# Igual que auth_service: esta es la validación DEFINITIVA. El frontend
# valida solo para dar buena experiencia, nunca hay que confiar en lo que
# llega del navegador. (La base de datos vuelve a validar con CHECK, claves
# foráneas y triggers: defensa en profundidad.)
#
# Flujo de un objeto ENCONTRADO:
#   pendiente_entrega -> (el estudiante lo lleva a la oficina) -> en_oficina
#   -> (reclamación pre-aprobada) -> reservado -> (entrega presencial) -> entregado
# Un objeto encontrado solo aparece en la búsqueda cuando ya está en la
# oficina: así no hay publicaciones falsas y lo que se ve se puede entregar.
#
# Flujo de un objeto PERDIDO:
#   buscando -> recuperado (cuando se le entrega un objeto encontrado) / cancelado / cerrado
# Los reportes de pérdida NO son públicos: solo los ven su dueño y la oficina.

from app.extensions import db
from app.models.catalogo import Categoria, Ubicacion
from app.models.objeto import (
    ESTADO_INICIAL, ESTADOS_DISPONIBLES, TIPO_ENCONTRADO, TIPO_PERDIDO, TIPOS_VALIDOS,
    EstadoObjeto, Objeto, transicion_permitida,
)
from app.models.usuario import ROL_ENCARGADO
from app.services import notificaciones_service
from app.utils import entero_o_none, fecha_o_none, texto, validar_fecha_pasada

LONGITUD_MIN_NOMBRE = 3
LONGITUD_MAX_NOMBRE = 120
LONGITUD_MIN_DESCRIPCION = 10
LONGITUD_MAX_DESCRIPCION = 500
LONGITUD_MAX_DETALLE_UBICACION = 150
LONGITUD_MAX_BUSQUEDA = 80

# Campos que un estudiante puede escribir al crear o editar su reporte.
# Todo lo demás (estado, usuario_id, recibido_por_id, version...) se ignora
# aunque venga en el body: whitelist explícita contra mass assignment.
CAMPOS_EDITABLES = ('nombre', 'categoria_id', 'ubicacion_id', 'fecha_evento', 'descripcion', 'detalle_ubicacion')


def patron_busqueda(valor):
    """Texto para ILIKE: se escapan los comodines % y _ para que el usuario
    busque literalmente lo que escribió. (La consulta igual va parametrizada:
    esto no tiene que ver con inyección SQL, sino con resultados correctos.)"""
    valor = texto(valor)[:LONGITUD_MAX_BUSQUEDA]
    valor = valor.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{valor}%'


def validar_datos_objeto(datos, requiere_tipo=True):
    """Devuelve (errores: dict, valores_limpios: dict)."""
    errores = {}
    limpio = {}

    if requiere_tipo:
        tipo = texto(datos.get('tipo'))
        if tipo not in TIPOS_VALIDOS:
            errores['tipo'] = 'El tipo debe ser "perdido" o "encontrado"'
        else:
            limpio['tipo'] = tipo

    nombre = texto(datos.get('nombre'))
    if not (LONGITUD_MIN_NOMBRE <= len(nombre) <= LONGITUD_MAX_NOMBRE):
        errores['nombre'] = f'El nombre debe tener entre {LONGITUD_MIN_NOMBRE} y {LONGITUD_MAX_NOMBRE} caracteres'
    else:
        limpio['nombre'] = nombre

    categoria = db.session.get(Categoria, entero_o_none(datos.get('categoria_id')) or 0)
    if categoria is None or not categoria.activa:
        errores['categoria_id'] = 'Selecciona una categoría válida'
    else:
        limpio['categoria_id'] = categoria.id

    ubicacion = db.session.get(Ubicacion, entero_o_none(datos.get('ubicacion_id')) or 0)
    if ubicacion is None or not ubicacion.activa:
        errores['ubicacion_id'] = 'Selecciona una ubicación válida'
    else:
        limpio['ubicacion_id'] = ubicacion.id

    descripcion = texto(datos.get('descripcion'))
    if not (LONGITUD_MIN_DESCRIPCION <= len(descripcion) <= LONGITUD_MAX_DESCRIPCION):
        errores['descripcion'] = (f'La descripción debe tener entre {LONGITUD_MIN_DESCRIPCION} '
                                  f'y {LONGITUD_MAX_DESCRIPCION} caracteres')
    else:
        limpio['descripcion'] = descripcion

    detalle = texto(datos.get('detalle_ubicacion'))
    if len(detalle) > LONGITUD_MAX_DETALLE_UBICACION:
        errores['detalle_ubicacion'] = f'Máximo {LONGITUD_MAX_DETALLE_UBICACION} caracteres'
    else:
        limpio['detalle_ubicacion'] = detalle

    fecha = validar_fecha_pasada(datos.get('fecha_evento'), errores, 'fecha_evento')
    if fecha:
        limpio['fecha_evento'] = fecha

    return errores, limpio


def crear_objeto(estudiante, datos):
    """Devuelve (errores, objeto)."""
    if not estudiante.correo_verificado:
        return {'correo': 'Debes verificar tu correo institucional antes de reportar'}, None

    errores, limpio = validar_datos_objeto(datos, requiere_tipo=True)
    if errores:
        return errores, None

    objeto = Objeto(
        tipo=limpio['tipo'],
        nombre=limpio['nombre'],
        categoria_id=limpio['categoria_id'],
        ubicacion_id=limpio['ubicacion_id'],
        fecha_evento=limpio['fecha_evento'],
        descripcion=limpio['descripcion'],
        detalle_ubicacion=limpio['detalle_ubicacion'],
        estado=ESTADO_INICIAL[limpio['tipo']],
        usuario_id=estudiante.id,
    )
    db.session.add(objeto)
    db.session.flush()

    notificaciones = []
    if objeto.tipo == TIPO_ENCONTRADO:
        notificaciones.append(notificaciones_service.crear(
            estudiante, 'objeto_por_entregar', 'Lleva el objeto a la oficina',
            f'Gracias por reportar "{objeto.nombre}". Llévalo a la oficina de objetos perdidos: '
            'solo después de que un encargado lo reciba aparecerá en la búsqueda para que su dueño lo reclame.',
            'mis-reportes.html',
        ))
        notificaciones += notificaciones_service.crear_para_rol(
            ROL_ENCARGADO, 'objeto_reportado', 'Nuevo objeto encontrado',
            f'{estudiante.nombre_completo} reportó "{objeto.nombre}". Está pendiente de que lo lleve a la oficina.',
            'encargado-objetos.html',
        )
    db.session.commit()
    notificaciones_service.enviar_correos(notificaciones)
    return {}, objeto


def actualizar_objeto(objeto, datos):
    """Solo se puede editar mientras el reporte está en su estado inicial:
    un objeto que ya está en custodia de la oficina no se modifica.
    Devuelve (errores, conflicto_de_version)."""
    if objeto.estado != ESTADO_INICIAL[objeto.tipo]:
        return {'estado': 'Este reporte ya no se puede editar'}, False

    # Concurrencia optimista: el cliente envía la versión que leyó. Si no
    # coincide, alguien más cambió el reporte mientras tanto.
    version_cliente = entero_o_none(datos.get('version'))
    if version_cliente is None:
        return {'version': 'Falta la versión del reporte'}, False
    if version_cliente != objeto.version:
        return {}, True

    errores, limpio = validar_datos_objeto(datos, requiere_tipo=False)
    if errores:
        return errores, False

    for campo in CAMPOS_EDITABLES:
        if campo in limpio:
            setattr(objeto, campo, limpio[campo])
    db.session.commit()
    return {}, False


def cancelar_objeto(objeto):
    if not transicion_permitida(objeto.tipo, objeto.estado, 'cancelado', 'estudiante'):
        return False
    objeto.estado = 'cancelado'
    db.session.commit()
    return True


def buscar_disponibles(filtros, pagina, por_pagina):
    """Búsqueda de los estudiantes: solo objetos ENCONTRADOS que están en la
    oficina. Filtra únicamente por campos públicos (nunca por la descripción
    privada: si se pudiera, alguien podría adivinar los detalles probando
    búsquedas)."""
    query = Objeto.query.filter(Objeto.tipo == TIPO_ENCONTRADO, Objeto.estado.in_(ESTADOS_DISPONIBLES))

    categoria_id = entero_o_none(filtros.get('categoria_id'))
    if categoria_id:
        query = query.filter(Objeto.categoria_id == categoria_id)
    ubicacion_id = entero_o_none(filtros.get('ubicacion_id'))
    if ubicacion_id:
        query = query.filter(Objeto.ubicacion_id == ubicacion_id)

    desde = fecha_o_none(filtros.get('desde'))
    if desde:
        query = query.filter(Objeto.fecha_evento >= desde)
    hasta = fecha_o_none(filtros.get('hasta'))
    if hasta:
        query = query.filter(Objeto.fecha_evento <= hasta)

    if texto(filtros.get('q')):
        query = query.filter(Objeto.nombre.ilike(patron_busqueda(filtros.get('q')), escape='\\'))

    query = query.order_by(Objeto.recibido_en.desc().nullslast(), Objeto.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def mis_reportes(estudiante, filtros, pagina, por_pagina):
    query = Objeto.query.filter(Objeto.usuario_id == estudiante.id)
    tipo = filtros.get('tipo')
    if tipo in TIPOS_VALIDOS:
        query = query.filter(Objeto.tipo == tipo)
    estado = texto(filtros.get('estado'))
    if estado:
        query = query.filter(Objeto.estado == estado)
    query = query.order_by(Objeto.created_at.desc(), Objeto.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def listar_para_oficina(filtros, pagina, por_pagina):
    """Vista del encargado y del administrador: todos los reportes, en
    cualquier estado, con búsqueda también en la descripción privada."""
    query = Objeto.query
    tipo = filtros.get('tipo')
    if tipo in TIPOS_VALIDOS:
        query = query.filter(Objeto.tipo == tipo)
    estado = texto(filtros.get('estado'))
    if estado:
        query = query.filter(Objeto.estado == estado)
    categoria_id = entero_o_none(filtros.get('categoria_id'))
    if categoria_id:
        query = query.filter(Objeto.categoria_id == categoria_id)
    if texto(filtros.get('q')):
        patron = patron_busqueda(filtros.get('q'))
        query = query.filter(db.or_(
            Objeto.nombre.ilike(patron, escape='\\'),
            Objeto.descripcion.ilike(patron, escape='\\'),
        ))
    query = query.order_by(Objeto.created_at.desc(), Objeto.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def estados_por_tipo():
    """Catálogo de estados para los filtros del frontend."""
    estados = EstadoObjeto.query.order_by(EstadoObjeto.tipo, EstadoObjeto.es_final, EstadoObjeto.codigo).all()
    resultado = {TIPO_PERDIDO: [], TIPO_ENCONTRADO: []}
    for estado in estados:
        resultado[estado.tipo].append({'codigo': estado.codigo, 'nombre': estado.nombre, 'es_final': estado.es_final})
    return resultado
