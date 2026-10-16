/* Detalle de un objeto para la OFICINA.
   - Encargado: puede confirmar la recepción, registrar la entrega
     presencial (código + carné + prueba) y cerrar el reporte.
   - Administrador: solo lectura (separación de funciones). */

let objetoIdOficina = null;
let esEncargado = false;

function datosObjetoOficina(objeto, entrega) {
  const panel = document.getElementById('panel-datos');
  vaciar(panel);
  const fila = (etiqueta, valor) => [el('dt', { texto: etiqueta }), el('dd', {}, valor)];
  panel.append(
    el('div', { clase: 'grupo-botones mb-2' }, [insigniaTipo(objeto.tipo), insigniaEstado(objeto.estado, objeto.estado_nombre)]),
    el('dl', { clase: 'datos' }, [
      ...fila('Categoría', objeto.categoria),
      ...fila('Ubicación', objeto.ubicacion),
      ...fila('Fecha del evento', formatearFecha(objeto.fecha_evento)),
      ...fila('Reportado por', objeto.reportado_por ? `${objeto.reportado_por.nombre} (${objeto.reportado_por.correo})` : '—'),
      ...fila('Reportado el', formatearFechaHora(objeto.created_at)),
      ...(objeto.recibido_en ? fila('Recibido en la oficina', `${formatearFechaHora(objeto.recibido_en)} por ${objeto.recibido_por || '—'}`) : []),
    ]),
    el('div', { clase: 'privado mt-3' }, [
      el('div', { clase: 'titulo-privado' }, [icono('lock'), 'Detalles privados (no se publican)']),
      el('p', { clase: 'mb-0', texto: objeto.descripcion }),
      objeto.detalle_ubicacion ? el('p', { clase: 'texto-suave texto-pequeno mt-1 mb-0' }, [icono('location-dot'), ' ', objeto.detalle_ubicacion]) : null,
      objeto.observaciones_custodia ? el('p', { clase: 'texto-pequeno mt-1 mb-0' }, [el('strong', { texto: 'Observaciones de la oficina: ' }), objeto.observaciones_custodia]) : null,
    ]),
  );
  if (objeto.motivo_cierre) {
    panel.append(el('div', { clase: 'alerta alerta-info mt-2' }, [icono('circle-info'), el('span', { texto: `Motivo del cierre: ${objeto.motivo_cierre}` })]));
  }
  if (entrega) {
    panel.append(el('div', { clase: 'alerta alerta-exito mt-2' }, [icono('handshake'), el('span', {
      texto: `Entregado el ${formatearFechaHora(entrega.entregado_en)} a ${entrega.recibido_por} por ${entrega.entregado_por}. Carné verificado. Prueba: ${entrega.prueba_propiedad}`,
    })]));
  }
}

function formularioAccion({ id, titulo, iconoTitulo, descripcion, campos, textoBoton, claseBoton, alEnviar }) {
  const mensaje = el('div', { clase: 'alerta' });
  const boton = el('button', { type: 'submit', clase: `boton ${claseBoton || 'boton-primario'} boton-bloque` }, textoBoton);
  const formulario = el('form', { clase: 'formulario', novalidate: true }, [...campos, boton]);
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarMensaje(mensaje);
    bloquearBoton(boton, 'Guardando…');
    const resultado = await alEnviar(formulario);
    desbloquearBoton(boton);
    if (resultado && resultado.ok) {
      window.location.hash = '';
      window.location.reload();
      return;
    }
    if (resultado) mostrarMensaje(mensaje, 'error', resultado.datos.mensaje);
  });
  return el('section', { clase: 'panel', id }, [
    el('h3', {}, [icono(iconoTitulo, 'texto-naranja'), ' ', titulo]),
    descripcion ? el('p', { clase: 'texto-suave texto-pequeno', texto: descripcion }) : null,
    mensaje,
    formulario,
  ]);
}

function campoTexto(nombre, etiqueta, opciones) {
  const id = `campo-${nombre}`;
  const control = opciones.area
    ? el('textarea', { id, name: nombre, maxlength: opciones.max, placeholder: opciones.placeholder || '' })
    : el('input', { id, name: nombre, type: 'text', maxlength: opciones.max, placeholder: opciones.placeholder || '', inputmode: opciones.inputmode, autocomplete: 'off' });
  return el('div', { clase: 'campo form-group' }, [el('label', { for: id, texto: etiqueta }), control, el('span', { clase: 'mensaje-error' })]);
}

function accionesEncargado(objeto, solicitudes) {
  const panel = document.getElementById('panel-acciones');
  vaciar(panel);
  const ruta = (accion) => `/encargado/objetos/${encodeURIComponent(objeto.id)}/${accion}`;

  if (objeto.estado === 'pendiente_entrega') {
    panel.append(formularioAccion({
      id: 'recepcion', titulo: 'Confirmar recepción', iconoTitulo: 'box-archive',
      descripcion: 'Confírmalo solo cuando tengas el objeto en la mano. Desde ese momento aparecerá en la búsqueda y se avisará a quienes reportaron algo parecido.',
      campos: [campoTexto('observaciones', 'Observaciones (opcional, privadas)', { max: 500, area: true, placeholder: 'Ej: tiene la pantalla rota; se guardó en el estante B' })],
      textoBoton: 'Recibir en la oficina',
      alEnviar: (f) => peticionSegura(ruta('recepcion'), { observaciones: f.observaciones.value.trim() }),
    }));
  }

  if (objeto.estado === 'reservado') {
    const preaprobada = solicitudes.find((s) => s.estado === 'preaprobada');
    const casilla = el('label', { clase: 'casilla' }, [
      el('input', { type: 'checkbox', name: 'carne_verificado' }),
      el('span', { texto: `Verifiqué el carné: la persona es ${preaprobada && preaprobada.solicitante ? preaprobada.solicitante.nombre : 'el estudiante pre-aprobado'}.` }),
    ]);
    const datosReclamante = preaprobada ? el('div', { clase: 'alerta alerta-naranja' }, [icono('user-check'), el('span', {
      texto: `Pre-aprobada para ${preaprobada.solicitante.nombre} (${preaprobada.solicitante.correo}). Vence: ${formatearFechaHora(preaprobada.vence_en)}. ${preaprobada.tiene_codigo ? 'Ya generó su código.' : 'Todavía NO ha generado su código.'}`,
    })]) : null;
    const seccion = formularioAccion({
      id: 'entrega', titulo: 'Entrega presencial', iconoTitulo: 'handshake',
      descripcion: 'Pide el carné, el código de 6 dígitos y una prueba de que el objeto es suyo (desbloquearlo, factura, IMEI…).',
      campos: [
        datosReclamante,
        campoTexto('codigo', 'Código de retiro', { max: 6, inputmode: 'numeric', placeholder: '6 dígitos' }),
        casilla,
        campoTexto('prueba_propiedad', 'Prueba de propiedad que presentó', { max: 300, placeholder: 'Ej: desbloqueó el celular con su huella' }),
        campoTexto('observaciones', 'Observaciones (opcional)', { max: 300 }),
      ],
      textoBoton: 'Registrar entrega', claseBoton: 'boton-exito',
      alEnviar: (f) => {
        if (!/^\d{6}$/.test(f.codigo.value.trim())) { mostrarError(f.codigo, 'El código tiene 6 dígitos'); return null; }
        return peticionSegura(ruta('entrega'), {
          codigo: f.codigo.value.trim(),
          carne_verificado: f.carne_verificado.checked,
          prueba_propiedad: f.prueba_propiedad.value.trim(),
          observaciones: f.observaciones.value.trim(),
        });
      },
    });
    panel.append(seccion);
  }

  if (['pendiente_entrega', 'en_oficina', 'buscando'].includes(objeto.estado)) {
    panel.append(formularioAccion({
      id: 'cierre', titulo: 'Cerrar reporte', iconoTitulo: 'box-archive',
      descripcion: objeto.estado === 'pendiente_entrega'
        ? 'Por ejemplo, si el objeto nunca llegó a la oficina.'
        : 'Por ejemplo, después del tiempo máximo de custodia. Las reclamaciones pendientes se descartarán.',
      campos: [campoTexto('motivo', 'Motivo del cierre', { max: 300, area: true })],
      textoBoton: 'Cerrar reporte', claseBoton: 'boton-peligro',
      alEnviar: (f) => {
        if (!window.confirm('¿Cerrar este reporte? No se puede deshacer.')) return null;
        return peticionSegura(ruta('cerrar'), { motivo: f.motivo.value.trim() });
      },
    }));
  }

  if (!panel.children.length) {
    panel.append(el('div', { clase: 'panel' }, [el('p', { clase: 'texto-suave mb-0', texto: 'Este reporte está en un estado final: no hay acciones pendientes.' })]));
  }
}

function listaSolicitudesOficina(solicitudes) {
  const contenedor = document.getElementById('lista-solicitudes');
  vaciar(contenedor);
  if (!solicitudes.length) {
    contenedor.append(estadoVacio('Nadie ha reclamado este objeto.', 'file-circle-question'));
    return;
  }
  contenedor.append(el('ul', { clase: 'lista-items' }, solicitudes.map((solicitud) => el('li', { clase: 'item' }, [
    el('div', { clase: 'principal' }, [
      el('h4', { texto: solicitud.solicitante ? solicitud.solicitante.nombre : '—' }),
      el('div', { clase: 'meta' }, [
        el('span', {}, [icono('clock'), ' ', formatearFechaHora(solicitud.created_at)]),
        solicitud.dias_reporte_previo !== null && solicitud.dias_reporte_previo >= 0
          ? el('span', { clase: 'insignia insignia-verde' }, [icono('shield-halved'), textoReportePrevio(solicitud.dias_reporte_previo)])
          : null,
      ]),
    ]),
    el('div', { clase: 'grupo-botones' }, [
      insigniaEstado(solicitud.estado, solicitud.estado_nombre),
      esEncargado ? el('a', { clase: 'boton boton-secundario boton-pequeno', href: `encargado-reclamacion.html?id=${encodeURIComponent(solicitud.id)}` }, ['Ver', icono('arrow-right')]) : null,
    ]),
  ]))));
}

function listaCoincidenciasOficina(objeto, coincidencias) {
  if (!coincidencias.length) return;
  document.getElementById('texto-coincidencias').textContent = objeto.tipo === 'encontrado'
    ? 'Reportes de pérdida parecidos (misma categoría, fechas cercanas). A sus dueños ya se les avisó al recibir el objeto.'
    : 'Objetos en la oficina parecidos a esta pérdida.';
  const contenedor = document.getElementById('lista-coincidencias');
  contenedor.append(el('ul', { clase: 'lista-items' }, coincidencias.map((c) => el('li', { clase: 'item' }, [
    el('div', { clase: 'principal' }, [
      el('h4', {}, el('a', { href: `oficina-objeto.html?id=${encodeURIComponent(c.id)}`, texto: c.nombre })),
      el('p', { clase: 'texto-suave texto-pequeno mb-0', texto: c.descripcion }),
      el('div', { clase: 'meta' }, [
        el('span', {}, [icono('user'), ' ', c.reportado_por ? c.reportado_por.nombre : '']),
        el('span', {}, [icono('calendar'), ' ', formatearFecha(c.fecha_evento)]),
        el('span', {}, [icono('location-dot'), ' ', c.ubicacion]),
      ]),
    ]),
    el('span', { clase: 'insignia insignia-naranja', texto: `Puntaje ${c.puntaje}` }),
  ]))));
  document.getElementById('panel-coincidencias').classList.remove('oculto');
}

sesionLista.then(async (usuario) => {
  if (!['encargado', 'administrador'].includes(usuario.rol)) {
    window.location.replace(`detalle-objeto.html?id=${encodeURIComponent(parametroUrl('id') || '')}`);
    return;
  }
  esEncargado = usuario.rol === 'encargado';
  objetoIdOficina = parametroUrl('id');
  if (!esEncargado) document.getElementById('enlace-lista').href = 'admin-objetos.html';

  const ruta = esEncargado ? '/encargado/objetos/' : '/admin/objetos/';
  const resultado = await peticionGet(ruta + encodeURIComponent(objetoIdOficina || ''));
  if (!resultado.ok) {
    document.getElementById('titulo-objeto').textContent = 'Objeto no encontrado';
    mostrarMensaje(document.getElementById('mensaje'), 'error', resultado.datos.mensaje);
    return;
  }
  const { objeto, solicitudes, entrega, coincidencias } = resultado.datos;
  document.title = `${objeto.nombre} · Oficina · EncuentraU`;
  document.getElementById('titulo-objeto').textContent = objeto.nombre;
  document.getElementById('subtitulo-objeto').textContent = `${objeto.categoria} · ${objeto.ubicacion} · reporte #${objeto.id}`;
  document.getElementById('icono-hero').className = `fa-solid fa-${iconoCategoria(objeto.categoria)} icono-fondo`;

  datosObjetoOficina(objeto, entrega);
  if (esEncargado) {
    accionesEncargado(objeto, solicitudes);
  } else {
    const panel = document.getElementById('panel-acciones');
    panel.append(el('div', { clase: 'panel' }, [
      el('h3', {}, [icono('eye', 'texto-naranja'), ' Solo lectura']),
      el('p', { clase: 'texto-suave mb-0', texto: 'Como administrador puedes consultar y auditar este reporte, pero recibir, aprobar y entregar objetos es tarea exclusiva de los encargados.' }),
      el('a', { clase: 'boton boton-secundario mt-2', href: `admin-auditoria.html?tabla=objetos&registro_id=${encodeURIComponent(objeto.id)}` }, [icono('clipboard-list'), 'Ver su auditoría']),
    ]));
  }
  listaSolicitudesOficina(solicitudes);
  listaCoincidenciasOficina(objeto, coincidencias);

  // Si se llegó con #recepcion o #entrega, llevar la vista al formulario
  if (/^#[a-z]+$/.test(window.location.hash)) {
    const destino = document.getElementById(window.location.hash.slice(1));
    if (destino) destino.scrollIntoView({ behavior: 'smooth' });
  }
});
