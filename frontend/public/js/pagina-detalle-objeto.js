/* Detalle de un objeto para un estudiante.
   - Si es su propio reporte: ve la descripción privada y puede editarlo o
     cancelarlo; si es una pérdida, ve posibles coincidencias en la oficina.
   - Si es un objeto de la oficina: ve solo los datos públicos y puede
     reclamarlo (verificación a ciegas). */

const ESTADOS_EDITABLES = ['buscando', 'pendiente_entrega'];

function filaDato(etiqueta, valor) {
  return [el('dt', { texto: etiqueta }), el('dd', {}, valor)];
}

function pintarDatos(objeto, esPropio) {
  const panel = document.getElementById('panel-datos');
  vaciar(panel);
  panel.append(
    el('div', { clase: 'grupo-botones mb-2' }, [insigniaTipo(objeto.tipo), insigniaEstado(objeto.estado, objeto.estado_nombre)]),
    el('dl', { clase: 'datos' }, [
      ...filaDato('Categoría', objeto.categoria),
      ...filaDato(objeto.tipo === 'perdido' ? 'Lugar donde se perdió' : 'Lugar donde se encontró', objeto.ubicacion),
      ...filaDato('Fecha', formatearFecha(objeto.fecha_evento)),
      ...(objeto.recibido_en ? filaDato('En la oficina desde', formatearFechaHora(objeto.recibido_en)) : []),
    ]),
  );

  if (esPropio) {
    panel.append(el('div', { clase: 'privado mt-3' }, [
      el('div', { clase: 'titulo-privado' }, [icono('lock'), 'Solo lo ves tú y la oficina']),
      el('p', { clase: 'mb-0', texto: objeto.descripcion }),
      objeto.detalle_ubicacion ? el('p', { clase: 'texto-suave texto-pequeno mt-1 mb-0' }, [icono('location-dot'), ' ', objeto.detalle_ubicacion]) : null,
    ]));
    if (objeto.motivo_cierre) {
      panel.append(el('div', { clase: 'alerta alerta-info mt-2' }, [icono('circle-info'), el('span', { texto: `Motivo del cierre: ${objeto.motivo_cierre}` })]));
    }
  } else {
    panel.append(el('div', { clase: 'alerta alerta-naranja mt-3' }, [
      icono('eye-slash'),
      el('span', { texto: 'Los detalles que identifican este objeto (marca, color, señas, contenido) no se publican. Si es tuyo, tendrás que describirlos al reclamarlo: así nadie más puede llevárselo.' }),
    ]));
  }
}

function pintarAccionesPropias(objeto) {
  const panel = document.getElementById('panel-acciones');
  vaciar(panel);
  panel.append(el('h3', { texto: 'Tu reporte' }));

  if (objeto.tipo === 'encontrado' && objeto.estado === 'pendiente_entrega') {
    panel.append(el('div', { clase: 'alerta alerta-advertencia' }, [icono('box-archive'),
      el('span', { texto: 'Lleva el objeto a la oficina de objetos perdidos. Aparecerá en la búsqueda cuando un encargado confirme que lo recibió.' })]));
  } else if (objeto.tipo === 'encontrado' && objeto.estado === 'en_oficina') {
    panel.append(el('p', { clase: 'texto-suave', texto: 'La oficina ya tiene el objeto. Te avisaremos cuando vuelva a su dueño. ¡Gracias!' }));
  } else if (objeto.tipo === 'perdido' && objeto.estado === 'buscando') {
    panel.append(el('p', { clase: 'texto-suave', texto: 'Te avisaremos por correo si llega a la oficina algo parecido.' }));
  }

  const acciones = el('div', { clase: 'grupo-botones mt-2' });
  if (ESTADOS_EDITABLES.includes(objeto.estado)) {
    const pagina = objeto.tipo === 'perdido' ? 'reportar-perdido.html' : 'reportar-encontrado.html';
    acciones.append(el('a', { clase: 'boton boton-secundario', href: `${pagina}?editar=${encodeURIComponent(objeto.id)}` }, [icono('pen'), 'Editar']));
    const cancelar = el('button', { clase: 'boton boton-peligro', type: 'button' }, [icono('ban'), 'Cancelar reporte']);
    cancelar.addEventListener('click', async () => {
      if (!window.confirm('¿Seguro que quieres cancelar este reporte? No se puede deshacer.')) return;
      bloquearBoton(cancelar, 'Cancelando…');
      const resultado = await peticionProtegida(`/objetos/${encodeURIComponent(objeto.id)}/cancelar`, 'POST');
      if (resultado.ok) { window.location.reload(); return; }
      desbloquearBoton(cancelar);
      mostrarMensaje(document.getElementById('mensaje'), 'error', resultado.datos.mensaje);
    });
    acciones.append(cancelar);
  }
  acciones.append(el('a', { clase: 'boton boton-secundario', href: 'mis-reportes.html' }, [icono('arrow-left'), 'Mis reportes']));
  panel.append(acciones);
}

function pintarAccionesReclamar(objeto, reclamacionAbiertaId) {
  const panel = document.getElementById('panel-acciones');
  vaciar(panel);
  panel.append(el('h3', { texto: '¿Es tuyo?' }));
  if (reclamacionAbiertaId) {
    panel.append(
      el('div', { clase: 'alerta alerta-info' }, [icono('circle-info'), el('span', { texto: 'Ya tienes una reclamación abierta para este objeto.' })]),
      el('a', { clase: 'boton boton-secundario mt-2', href: 'mis-reclamaciones.html' }, [icono('file-signature'), 'Ver mis reclamaciones']),
    );
    return;
  }
  panel.append(
    el('p', { clase: 'texto-suave', texto: 'Reclámalo describiendo el objeto. Un encargado comparará tu descripción con lo que tiene la oficina.' }),
    el('a', { clase: 'boton boton-primario boton-bloque', href: `reclamar-objeto.html?id=${encodeURIComponent(objeto.id)}` }, [icono('hand'), 'Es mío, quiero reclamarlo']),
    el('p', { clase: 'texto-suave texto-pequeno mt-2', texto: 'Reclamar un objeto ajeno puede constituir una falta disciplinaria. Cada reclamación queda registrada con tu cuenta.' }),
  );
}

async function pintarCoincidencias(objeto) {
  const resultado = await peticionGet(`/objetos/${encodeURIComponent(objeto.id)}/coincidencias`);
  if (!resultado.ok || !resultado.datos.datos.length) return;
  const lista = document.getElementById('lista-coincidencias');
  resultado.datos.datos.forEach((candidato) => lista.append(tarjetaObjeto(candidato, `detalle-objeto.html?id=${encodeURIComponent(candidato.id)}`)));
  document.getElementById('panel-coincidencias').classList.remove('oculto');
}

sesionLista.then(async () => {
  const id = parametroUrl('id');
  const mensaje = document.getElementById('mensaje');
  const resultado = await peticionGet(`/objetos/${encodeURIComponent(id || '')}`);
  if (!resultado.ok) {
    document.getElementById('titulo-objeto').textContent = 'Objeto no disponible';
    mostrarMensaje(mensaje, 'error', resultado.status === 403
      ? 'Este objeto no está disponible para consulta.'
      : (resultado.datos.mensaje || 'No se encontró el objeto.'));
    document.getElementById('panel-datos').classList.add('oculto');
    document.getElementById('panel-acciones').classList.add('oculto');
    return;
  }

  const { objeto, es_propio: esPropio, reclamacion_abierta_id: reclamacionAbiertaId } = resultado.datos;
  document.title = `${objeto.nombre} · EncuentraU`;
  document.getElementById('titulo-objeto').textContent = objeto.nombre;
  document.getElementById('subtitulo-objeto').textContent = `${objeto.categoria} · ${objeto.ubicacion}`;
  document.getElementById('icono-hero').className = `fa-solid fa-${iconoCategoria(objeto.categoria)} icono-fondo`;
  if (esPropio) {
    const migas = document.getElementById('migas');
    vaciar(migas);
    migas.append(el('a', { href: 'mis-reportes.html', texto: 'Mis reportes' }), ' / Detalle');
  }
  if (parametroUrl('creado')) mostrarMensaje(mensaje, 'exito', 'Reporte guardado correctamente.');

  pintarDatos(objeto, esPropio);
  if (esPropio) {
    pintarAccionesPropias(objeto);
    if (objeto.tipo === 'perdido' && objeto.estado === 'buscando') pintarCoincidencias(objeto);
  } else {
    pintarAccionesReclamar(objeto, reclamacionAbiertaId);
  }
});
