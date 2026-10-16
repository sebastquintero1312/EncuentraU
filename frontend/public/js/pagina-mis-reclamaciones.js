/* Reclamaciones del estudiante: estado, línea de tiempo, código de retiro
   y cancelación. */

const PASOS_RECLAMACION = ['Enviada', 'Pre-aprobada', 'Entregada'];

function lineaDeTiempo(estado) {
  const indiceActual = { pendiente: 0, preaprobada: 1, entregada: 2 }[estado];
  return el('ol', { clase: 'linea-tiempo', 'aria-label': 'Progreso de la reclamación' }, PASOS_RECLAMACION.map((paso, indice) => {
    let clase = '';
    if (indiceActual !== undefined) {
      if (indice < indiceActual || estado === 'entregada') clase = 'hecho';
      else if (indice === indiceActual) clase = 'actual';
    }
    return el('li', { clase, texto: paso });
  }));
}

function mostrarCodigo(codigo, venceEn) {
  document.getElementById('codigo-retiro').textContent = codigo;
  document.getElementById('vence-codigo').textContent = `Debes retirar el objeto antes del ${formatearFechaHora(venceEn)}.`;
  document.getElementById('modal-codigo').classList.remove('oculto');
  document.getElementById('cerrar-modal-codigo').focus();
}

function tarjetaReclamacion(solicitud) {
  const objeto = solicitud.objeto || {};
  const acciones = el('div', { clase: 'grupo-botones mt-2' });
  const mensaje = document.getElementById('mensaje');

  if (solicitud.estado === 'preaprobada') {
    const generar = el('button', { clase: 'boton boton-primario', type: 'button' }, [icono('key'), solicitud.tiene_codigo ? 'Generar un código nuevo' : 'Generar código de retiro']);
    generar.addEventListener('click', async () => {
      if (solicitud.tiene_codigo && !window.confirm('Si generas un código nuevo, el anterior dejará de funcionar. ¿Continuar?')) return;
      bloquearBoton(generar, 'Generando…');
      const resultado = await peticionProtegida(`/solicitudes/${encodeURIComponent(solicitud.id)}/codigo`, 'POST');
      desbloquearBoton(generar);
      if (resultado.ok) {
        mostrarCodigo(resultado.datos.codigo, resultado.datos.vence_en);
        solicitud.tiene_codigo = true;
        generar.textContent = 'Generar un código nuevo';
      } else {
        mostrarMensaje(mensaje, 'error', resultado.datos.mensaje);
      }
    });
    acciones.append(generar);
  }

  if (['pendiente', 'preaprobada'].includes(solicitud.estado)) {
    const cancelar = el('button', { clase: 'boton boton-peligro', type: 'button' }, [icono('ban'), 'Cancelar reclamación']);
    cancelar.addEventListener('click', async () => {
      if (!window.confirm('¿Seguro que quieres cancelar esta reclamación?')) return;
      bloquearBoton(cancelar, 'Cancelando…');
      const resultado = await peticionProtegida(`/solicitudes/${encodeURIComponent(solicitud.id)}/cancelar`, 'POST');
      if (resultado.ok) { cargarReclamaciones(1); return; }
      desbloquearBoton(cancelar);
      mostrarMensaje(mensaje, 'error', resultado.datos.mensaje);
    });
    acciones.append(cancelar);
  }

  const avisos = [];
  if (solicitud.estado === 'pendiente') {
    avisos.push(el('div', { clase: 'alerta alerta-info mt-2' }, [icono('hourglass-half'), el('span', { texto: 'Un encargado está revisando tu descripción. Te avisaremos por correo.' })]));
  }
  if (solicitud.estado === 'preaprobada') {
    avisos.push(el('div', { clase: 'alerta alerta-naranja mt-2' }, [icono('id-card'), el('span', {
      texto: `¡Tu descripción coincide! Genera tu código y ve a la oficina con tu carné antes del ${formatearFechaHora(solicitud.vence_en)}. Lleva una prueba de que es tuyo.`,
    })]));
  }
  if (solicitud.respuesta) {
    avisos.push(el('p', { clase: 'texto-suave texto-pequeno mt-2 mb-0' }, [el('strong', { texto: 'Respuesta de la oficina: ' }), solicitud.respuesta]));
  }

  return el('article', { clase: 'panel' }, [
    el('div', { clase: 'panel-titulo mb-0' }, [
      el('div', {}, [
        el('span', { clase: 'etiqueta-seccion', texto: objeto.categoria || '' }),
        el('h3', { clase: 'mb-0', texto: objeto.nombre || 'Objeto' }),
        el('div', { clase: 'texto-suave texto-pequeno', texto: `Reclamación enviada el ${formatearFechaHora(solicitud.created_at)}` }),
      ]),
      insigniaEstado(solicitud.estado, solicitud.estado_nombre),
    ]),
    lineaDeTiempo(solicitud.estado),
    ...avisos,
    acciones,
  ]);
}

async function cargarReclamaciones(pagina) {
  const lista = document.getElementById('lista-reclamaciones');
  vaciar(lista);
  lista.append(estadoCargando());
  const resultado = await peticionGet('/mis-solicitudes', { pagina, por_pagina: 10 });
  vaciar(lista);
  if (!resultado.ok) {
    lista.append(el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }));
    return;
  }
  if (!resultado.datos.datos.length) {
    lista.append(el('div', { clase: 'panel' }, [
      estadoVacio('Todavía no has reclamado ningún objeto.', 'file-circle-question'),
      el('div', { clase: 'centrado' }, el('a', { clase: 'boton boton-primario', href: 'buscar-objetos.html' }, [icono('magnifying-glass'), 'Buscar en la oficina'])),
    ]));
  }
  resultado.datos.datos.forEach((solicitud) => lista.append(tarjetaReclamacion(solicitud)));
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, cargarReclamaciones);
}

sesionLista.then(() => {
  if (parametroUrl('enviada')) {
    mostrarMensaje(document.getElementById('mensaje'), 'exito', 'Reclamación enviada. Te avisaremos por correo cuando la revisen.');
  }
  document.getElementById('cerrar-modal-codigo').addEventListener('click', () => {
    document.getElementById('codigo-retiro').textContent = '';
    document.getElementById('modal-codigo').classList.add('oculto');
  });
  cargarReclamaciones(1);
});
