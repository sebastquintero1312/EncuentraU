/* Panel del encargado: indicadores y colas de trabajo. */

sesionLista.then(async () => {
  const [estadisticas, pendientes, reclamaciones] = await Promise.all([
    peticionGet('/encargado/estadisticas'),
    peticionGet('/encargado/objetos', { estado: 'pendiente_entrega', por_pagina: 5 }),
    peticionGet('/encargado/solicitudes', { estado: 'pendiente', por_pagina: 5 }),
  ]);

  if (estadisticas.ok) {
    const g = estadisticas.datos.generales;
    document.getElementById('kpi-pendientes').textContent = g.pendientes_de_recibir;
    document.getElementById('kpi-reclamaciones').textContent = g.reclamaciones_pendientes;
    document.getElementById('kpi-reservados').textContent = g.reservados;
    document.getElementById('kpi-custodia').textContent = g.en_custodia - g.reservados;
  }

  const listaPendientes = document.getElementById('lista-pendientes');
  if (pendientes.ok && pendientes.datos.datos.length) {
    listaPendientes.append(el('ul', { clase: 'lista-items' }, pendientes.datos.datos.map((objeto) => el('li', { clase: 'item' }, [
      el('div', { clase: 'principal' }, [
        el('h4', {}, el('a', { href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}`, texto: objeto.nombre })),
        el('div', { clase: 'meta' }, [
          el('span', {}, [icono('user'), ' ', objeto.reportado_por ? objeto.reportado_por.nombre : '']),
          el('span', {}, [icono('calendar'), ' ', formatearFecha(objeto.fecha_evento)]),
        ]),
      ]),
      el('a', { clase: 'boton boton-primario boton-pequeno', href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}#recepcion` }, [icono('box-archive'), 'Recibir']),
    ]))));
  } else {
    listaPendientes.append(estadoVacio('No hay objetos por recibir.', 'circle-check'));
  }

  const listaReclamaciones = document.getElementById('lista-reclamaciones');
  if (reclamaciones.ok && reclamaciones.datos.datos.length) {
    listaReclamaciones.append(el('ul', { clase: 'lista-items' }, reclamaciones.datos.datos.map((solicitud) => el('li', { clase: 'item' }, [
      el('div', { clase: 'principal' }, [
        el('h4', { texto: solicitud.objeto ? solicitud.objeto.nombre : 'Objeto' }),
        el('div', { clase: 'meta' }, [
          el('span', {}, [icono('user'), ' ', solicitud.solicitante ? solicitud.solicitante.nombre : '']),
          el('span', {}, [icono('clock'), ' ', formatearFechaHora(solicitud.created_at)]),
        ]),
      ]),
      el('a', { clase: 'boton boton-primario boton-pequeno', href: `encargado-reclamacion.html?id=${encodeURIComponent(solicitud.id)}` }, [icono('scale-balanced'), 'Revisar']),
    ]))));
  } else {
    listaReclamaciones.append(estadoVacio('No hay reclamaciones pendientes.', 'circle-check'));
  }
});
