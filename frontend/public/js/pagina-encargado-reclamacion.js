/* Revisión de una reclamación: comparación lado a lado entre lo que
   escribió el estudiante y los detalles privados del objeto. */

function bloqueTexto(titulo, texto) {
  return el('div', { clase: 'mb-2' }, [
    el('div', { clase: 'etiqueta-seccion', texto: titulo }),
    el('p', { clase: 'mb-0', texto: texto || '—' }),
  ]);
}

function pintarReclamacion(solicitud) {
  const objeto = solicitud.objeto;
  const cabecera = document.getElementById('cabecera-reclamacion');
  cabecera.append(
    el('div', {}, [
      el('span', { clase: 'etiqueta-seccion', texto: `Reclamación #${solicitud.id}` }),
      el('h2', { clase: 'mb-0', texto: objeto.nombre }),
      el('div', { clase: 'texto-suave texto-pequeno' }, [
        'Reclamada por ', el('strong', { texto: solicitud.solicitante.nombre }), ` (${solicitud.solicitante.correo}) el ${formatearFechaHora(solicitud.created_at)}`,
      ]),
    ]),
    el('div', { clase: 'grupo-botones' }, [
      insigniaEstado(solicitud.estado, solicitud.estado_nombre),
      el('a', { clase: 'boton boton-secundario boton-pequeno', href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}` }, [icono('box-open'), 'Ver objeto']),
    ]),
  );

  const evidencias = document.getElementById('evidencias');
  if (solicitud.dias_reporte_previo !== null) {
    evidencias.append(solicitud.dias_reporte_previo >= 0
      ? el('span', { clase: 'insignia insignia-verde' }, [icono('shield-halved'), textoReportePrevio(solicitud.dias_reporte_previo)])
      : el('span', { clase: 'insignia insignia-ambar' }, [icono('triangle-exclamation'), textoReportePrevio(solicitud.dias_reporte_previo)]));
  } else {
    evidencias.append(el('span', { clase: 'insignia insignia-gris' }, [icono('circle-info'), 'Sin reporte de pérdida previo']));
  }
  if (solicitud.solicitante.marcado_revision) {
    evidencias.append(el('span', { clase: 'insignia insignia-rojo' }, [icono('flag'), 'Cuenta en revisión por reclamaciones rechazadas']));
  }

  const estudiante = document.getElementById('columna-estudiante');
  estudiante.append(
    el('h4', {}, [icono('user'), ' Lo que dice el estudiante']),
    bloqueTexto('Descripción', solicitud.descripcion),
    bloqueTexto('Dónde lo perdió', solicitud.lugar_perdida),
    bloqueTexto('Cuándo', formatearFecha(solicitud.fecha_perdida)),
    bloqueTexto('Prueba que puede mostrar', solicitud.evidencia || 'No indicó ninguna'),
  );
  if (solicitud.reporte_perdida) {
    estudiante.append(el('div', { clase: 'privado' }, [
      el('div', { clase: 'titulo-privado' }, [icono('clipboard'), `Su reporte de pérdida (del ${formatearFechaHora(solicitud.reporte_perdida.created_at)})`]),
      el('p', { clase: 'mb-0', texto: solicitud.reporte_perdida.descripcion }),
    ]));
  }

  const oficina = document.getElementById('columna-oficina');
  oficina.append(
    el('h4', {}, [icono('lock'), ' Lo que sabe la oficina (privado)']),
    bloqueTexto('Descripción privada', objeto.descripcion),
    bloqueTexto('Dónde se encontró', `${objeto.ubicacion}${objeto.detalle_ubicacion ? ' · ' + objeto.detalle_ubicacion : ''}`),
    bloqueTexto('Cuándo', formatearFecha(objeto.fecha_evento)),
    objeto.observaciones_custodia ? bloqueTexto('Observaciones de la oficina', objeto.observaciones_custodia) : null,
  );

  if (solicitud.estado !== 'pendiente') {
    document.getElementById('panel-decision').classList.add('oculto');
    if (solicitud.respuesta) {
      mostrarMensaje(document.getElementById('mensaje'), 'info', `Respuesta registrada: ${solicitud.respuesta}`);
    }
  }
}

function pintarOtras(otras) {
  if (!otras.length) return;
  document.getElementById('lista-otras').append(el('ul', { clase: 'lista-items' }, otras.map((s) => el('li', { clase: 'item' }, [
    el('div', { clase: 'principal' }, [
      el('h4', { texto: s.solicitante.nombre }),
      el('div', { clase: 'meta' }, [el('span', { texto: formatearFechaHora(s.created_at) })]),
    ]),
    el('div', { clase: 'grupo-botones' }, [
      insigniaEstado(s.estado, s.estado_nombre),
      el('a', { clase: 'boton boton-secundario boton-pequeno', href: `encargado-reclamacion.html?id=${encodeURIComponent(s.id)}` }, ['Ver', icono('arrow-right')]),
    ]),
  ]))));
  document.getElementById('panel-otras').classList.remove('oculto');
}

sesionLista.then(async () => {
  const id = parametroUrl('id');
  const mensaje = document.getElementById('mensaje');
  const resultado = await peticionGet(`/encargado/solicitudes/${encodeURIComponent(id || '')}`);
  if (!resultado.ok) {
    mostrarMensaje(mensaje, 'error', resultado.datos.mensaje);
    document.getElementById('panel-decision').classList.add('oculto');
    return;
  }
  pintarReclamacion(resultado.datos.solicitud);
  pintarOtras(resultado.datos.otras_solicitudes);

  const ruta = (accion) => `/encargado/solicitudes/${encodeURIComponent(id)}/${accion}`;

  document.getElementById('form-preaprobar').addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const boton = document.getElementById('boton-preaprobar');
    bloquearBoton(boton, 'Guardando…');
    const respuesta = await peticionSegura(ruta('preaprobar'), { respuesta: document.getElementById('respuesta').value.trim() });
    desbloquearBoton(boton);
    if (respuesta.ok) { window.location.reload(); return; }
    mostrarMensaje(mensaje, 'error', respuesta.datos.mensaje);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  document.getElementById('form-rechazar').addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const motivo = document.getElementById('motivo');
    limpiarErroresCampos(evento.target);
    if (!longitudValida(motivo.value, 5, 300)) { mostrarError(motivo, 'Escribe el motivo (mínimo 5 caracteres)'); return; }
    if (!window.confirm('¿Rechazar esta reclamación?')) return;
    const boton = document.getElementById('boton-rechazar');
    bloquearBoton(boton, 'Guardando…');
    const respuesta = await peticionSegura(ruta('rechazar'), { motivo: motivo.value.trim() });
    desbloquearBoton(boton);
    if (respuesta.ok) { window.location.reload(); return; }
    mostrarMensaje(mensaje, 'error', respuesta.datos.mensaje);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
});
