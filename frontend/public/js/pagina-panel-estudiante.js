/* Panel del estudiante: resumen de reclamaciones, avisos y reportes. */

function itemReclamacion(solicitud) {
  return el('li', { clase: 'item' }, [
    el('div', { clase: 'principal' }, [
      el('h4', { texto: solicitud.objeto ? solicitud.objeto.nombre : 'Objeto' }),
      el('div', { clase: 'meta' }, [el('span', { texto: `Enviada el ${formatearFecha(solicitud.created_at)}` })]),
    ]),
    insigniaEstado(solicitud.estado, solicitud.estado_nombre),
  ]);
}

function itemAviso(aviso) {
  const contenido = [
    el('div', { clase: 'principal' }, [
      el('h4', { texto: aviso.titulo }),
      el('div', { clase: 'meta' }, [el('span', { texto: formatearFechaHora(aviso.created_at) })]),
    ]),
  ];
  return el('li', { clase: 'item' + (aviso.leida ? '' : ' no-leida') }, contenido);
}

function itemReporte(objeto) {
  return el('li', { clase: 'item' }, [
    el('div', { clase: 'principal' }, [
      el('h4', {}, [el('a', { href: `detalle-objeto.html?id=${encodeURIComponent(objeto.id)}`, texto: objeto.nombre })]),
      el('div', { clase: 'meta' }, [
        insigniaTipo(objeto.tipo),
        el('span', {}, [icono('location-dot'), ' ', objeto.ubicacion]),
        el('span', {}, [icono('calendar'), ' ', formatearFecha(objeto.fecha_evento)]),
      ]),
    ]),
    insigniaEstado(objeto.estado, objeto.estado_nombre),
  ]);
}

async function pintarLista(idContenedor, ruta, parametros, crearItem, textoVacio, nombreIcono) {
  const contenedor = document.getElementById(idContenedor);
  vaciar(contenedor);
  contenedor.append(estadoCargando());
  const resultado = await peticionGet(ruta, parametros);
  vaciar(contenedor);
  if (!resultado.ok) {
    contenedor.append(el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }));
    return;
  }
  const datos = resultado.datos.datos || [];
  if (!datos.length) {
    contenedor.append(estadoVacio(textoVacio, nombreIcono));
    return;
  }
  contenedor.append(el('ul', { clase: 'lista-items' }, datos.slice(0, 5).map(crearItem)));
}

sesionLista.then((usuario) => {
  document.getElementById('nombre-estudiante').textContent = usuario.primer_nombre;
  pintarLista('lista-reclamaciones', '/mis-solicitudes', { por_pagina: 5 }, itemReclamacion,
    'Aún no has reclamado ningún objeto.', 'file-circle-question');
  pintarLista('lista-avisos', '/notificaciones', null, itemAviso, 'No tienes avisos todavía.', 'bell-slash');
  pintarLista('lista-reportes', '/mis-reportes', { por_pagina: 5 }, itemReporte,
    'No has hecho ningún reporte.', 'clipboard');
});
