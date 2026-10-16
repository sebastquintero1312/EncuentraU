/* Reclamación de un objeto (verificación a ciegas). */

sesionLista.then(async () => {
  const id = parametroUrl('id');
  const formulario = document.getElementById('form-reclamar');
  const mensaje = document.getElementById('mensaje');
  const campo = (idCampo) => document.getElementById(idCampo);

  campo('fecha').max = hoyISO();
  campo('fecha').value = hoyISO();
  conectarContador(campo('descripcion'));
  campo('enlace-volver').href = `detalle-objeto.html?id=${encodeURIComponent(id || '')}`;

  const [respuestaObjeto, respuestaReportes] = await Promise.all([
    peticionGet(`/objetos/${encodeURIComponent(id || '')}`),
    peticionGet('/mis-reportes', { tipo: 'perdido', estado: 'buscando', por_pagina: 50 }),
  ]);

  if (!respuestaObjeto.ok || respuestaObjeto.datos.es_propio || respuestaObjeto.datos.reclamacion_abierta_id) {
    mostrarMensaje(mensaje, 'error', respuestaObjeto.datos.reclamacion_abierta_id
      ? 'Ya tienes una reclamación abierta para este objeto.'
      : 'Este objeto no está disponible para reclamar.');
    formulario.classList.add('oculto');
    return;
  }

  const objeto = respuestaObjeto.datos.objeto;
  const resumen = campo('resumen-objeto');
  resumen.append(el('div', { clase: 'item' }, [
    el('div', { clase: 'icono-circulo mb-0' }, icono(iconoCategoria(objeto.categoria))),
    el('div', { clase: 'principal' }, [
      el('h4', { texto: objeto.nombre }),
      el('div', { clase: 'meta' }, [
        el('span', { texto: objeto.categoria }),
        el('span', {}, [icono('location-dot'), ' ', objeto.ubicacion]),
        el('span', {}, [icono('calendar'), ' ', formatearFecha(objeto.fecha_evento)]),
      ]),
    ]),
  ]));

  const reportes = respuestaReportes.ok ? respuestaReportes.datos.datos : [];
  llenarSelect(campo('reporte-perdida'),
    reportes.map((r) => ({ valor: r.id, texto: `${r.nombre} · reportado el ${formatearFecha(r.created_at)}` })),
    reportes.length ? 'No, no lo había reportado' : 'No tienes reportes de pérdida activos');

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErroresCampos(formulario);
    limpiarMensaje(mensaje);
    campo('error-declaracion').textContent = '';

    let valido = true;
    if (!longitudValida(campo('descripcion').value, 20, 500)) { mostrarError(campo('descripcion'), 'Describe el objeto con al menos 20 caracteres'); valido = false; }
    if (!longitudValida(campo('lugar').value, 3, 150)) { mostrarError(campo('lugar'), 'Indica dónde lo perdiste'); valido = false; }
    if (!campo('fecha').value || campo('fecha').value > hoyISO()) { mostrarError(campo('fecha'), 'La fecha no puede ser futura'); valido = false; }
    if (!campo('declaracion').checked) { campo('error-declaracion').textContent = 'Debes aceptar la declaración para continuar'; valido = false; }
    if (!valido) return;

    const boton = campo('boton-enviar');
    bloquearBoton(boton, 'Enviando…');
    const resultado = await peticionSegura('/solicitudes', {
      objeto_id: Number(id),
      descripcion: campo('descripcion').value.trim(),
      lugar_perdida: campo('lugar').value.trim(),
      fecha_perdida: campo('fecha').value,
      evidencia: campo('evidencia').value.trim(),
      reporte_perdida_id: campo('reporte-perdida').value ? Number(campo('reporte-perdida').value) : null,
    });
    desbloquearBoton(boton);

    if (resultado.ok) {
      window.location.href = 'mis-reclamaciones.html?enviada=1';
      return;
    }
    mostrarErroresCampos(formulario, resultado.datos.errores);
    mostrarMensaje(mensaje, 'error', mensajeDeError(resultado));
  });
});
