# Consulta de la auditoría (solo lectura) y exportación de datos.
#
# La auditoría la escribe la base de datos con triggers; aquí solo se filtra
# y se pagina para el panel del administrador.

import csv
import io
from datetime import datetime, time, timedelta

from app.config.config import ZONA_HORARIA_COLOMBIA
from app.models.auditoria import OPERACIONES, TABLAS_AUDITADAS, AuditoriaDetallada
from app.models import reportes
from app.utils import entero_o_none, fecha_o_none


def listar(filtros, pagina, por_pagina):
    query = AuditoriaDetallada.query

    tabla = filtros.get('tabla')
    if tabla in TABLAS_AUDITADAS:
        query = query.filter(AuditoriaDetallada.tabla == tabla)
    operacion = filtros.get('operacion')
    if operacion in OPERACIONES:
        query = query.filter(AuditoriaDetallada.operacion == operacion)
    registro_id = entero_o_none(filtros.get('registro_id'))
    if registro_id:
        query = query.filter(AuditoriaDetallada.registro_id == registro_id)
    usuario_id = entero_o_none(filtros.get('usuario_id'))
    if usuario_id:
        query = query.filter(AuditoriaDetallada.usuario_id == usuario_id)
    transaccion_id = entero_o_none(filtros.get('transaccion_id'))
    if transaccion_id:
        query = query.filter(AuditoriaDetallada.transaccion_id == transaccion_id)

    # Las fechas se interpretan en hora de Colombia (día completo)
    desde = fecha_o_none(filtros.get('desde'))
    if desde:
        query = query.filter(AuditoriaDetallada.fecha >= datetime.combine(desde, time.min, ZONA_HORARIA_COLOMBIA))
    hasta = fecha_o_none(filtros.get('hasta'))
    if hasta:
        query = query.filter(AuditoriaDetallada.fecha < datetime.combine(hasta + timedelta(days=1), time.min,
                                                                         ZONA_HORARIA_COLOMBIA))

    query = query.order_by(AuditoriaDetallada.id.desc())
    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)


def _celda_segura(valor):
    """Evita la "inyección de fórmulas" en Excel: si un usuario nombra su
    objeto "=HYPERLINK(...)", Excel podría ejecutarlo al abrir el archivo.
    Se antepone un apóstrofo a los valores que empiezan como una fórmula."""
    if valor is None:
        return ''
    if isinstance(valor, datetime):
        return valor.astimezone(ZONA_HORARIA_COLOMBIA).strftime('%Y-%m-%d %H:%M')
    valor = str(valor)
    if valor[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + valor
    return valor


def _a_csv(columnas, filas):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow([titulo for _, titulo in columnas])
    for fila in filas:
        escritor.writerow([_celda_segura(fila.get(clave)) for clave, _ in columnas])
    # BOM al inicio: así Excel abre bien las tildes (UTF-8)
    return '﻿' + salida.getvalue()


def csv_objetos():
    columnas = [
        ('id', 'ID'), ('tipo', 'Tipo'), ('nombre', 'Objeto'), ('categoria', 'Categoría'),
        ('ubicacion', 'Ubicación'), ('fecha_evento', 'Fecha del evento'), ('estado', 'Estado'),
        ('created_at', 'Reportado'), ('recibido_en', 'Recibido en oficina'),
    ]
    return _a_csv(columnas, reportes.objetos_para_exportar())


def csv_estadisticas_mensuales():
    columnas = [('mes', 'Mes'), ('perdidos', 'Perdidos'), ('encontrados', 'Encontrados'), ('entregados', 'Entregados')]
    return _a_csv(columnas, reportes.estadisticas_mensuales(meses=120))
