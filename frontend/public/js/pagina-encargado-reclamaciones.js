/* Cola de reclamaciones del encargado (las más antiguas primero). */

let estadoReclamaciones = 'pendiente';

async function cargarColaReclamaciones(pagina) {
  const lista = document.getElementById('lista-reclamaciones');
  vaciar(lista);
  lista.append(estadoCargando());
  const resultado = await peticionGet('/encargado/solicitudes', { estado: estadoReclamaciones, pagina, por_pagina: 10 });
  vaciar(lista);
  if (!resultado.ok) {
    lista.append(el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }));
    return;
  }
  if (!resultado.datos.datos.length) {
    lista.append(estadoVacio('No hay reclamaciones en este estado.', 'circle-check'));
  } else {
    lista.append(el('ul', { clase: 'lista-items' }, resultado.datos.datos.map((solicitud) => el('li', { clase: 'item' }, [
      el('div', { clase: 'icono-circulo mb-0' }, icono(iconoCategoria(solicitud.objeto ? solicitud.objeto.categoria : ''))),
      el('div', { clase: 'principal' }, [
        el('h4', { texto: solicitud.objeto ? solicitud.objeto.nombre : 'Objeto' }),
        el('div', { clase: 'meta' }, [
          el('span', {}, [icono('user'), ' ', solicitud.solicitante ? solicitud.solicitante.nombre : '']),
          el('span', {}, [icono('clock'), ' ', formatearFechaHora(solicitud.created_at)]),
          solicitud.solicitante && solicitud.solicitante.marcado_revision ? el('span', { clase: 'insignia insignia-rojo' }, [icono('flag'), 'Cuenta en revisión']) : null,
          solicitud.dias_reporte_previo !== null && solicitud.dias_reporte_previo >= 0
            ? el('span', { clase: 'insignia insignia-verde' }, [icono('shield-halved'), 'Reportó la pérdida antes']) : null,
        ]),
      ]),
      el('div', { clase: 'grupo-botones' }, [
        insigniaEstado(solicitud.estado, solicitud.estado_nombre),
        el('a', { clase: 'boton boton-primario boton-pequeno', href: `encargado-reclamacion.html?id=${encodeURIComponent(solicitud.id)}` }, [icono('scale-balanced'), 'Revisar']),
      ]),
    ]))));
  }
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, cargarColaReclamaciones);
}

sesionLista.then(() => {
  document.querySelectorAll('#pildoras-estado .pildora').forEach((pildora) => {
    pildora.addEventListener('click', () => {
      document.querySelectorAll('#pildoras-estado .pildora').forEach((p) => p.classList.remove('activa'));
      pildora.classList.add('activa');
      estadoReclamaciones = pildora.dataset.estado;
      cargarColaReclamaciones(1);
    });
  });
  cargarColaReclamaciones(1);
});
