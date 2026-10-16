/* Crear o editar un reporte (perdido o encontrado). La misma lógica sirve
   para reportar-perdido.html y reportar-encontrado.html; el tipo sale del
   atributo data-tipo del formulario.

   Edición: ?editar=<id>. Se envía la "versión" que se leyó; si otra pestaña
   o persona cambió el reporte mientras tanto, el backend responde 409
   (control de concurrencia optimista). */

sesionLista.then(async () => {
  const formulario = document.getElementById('form-reporte');
  const mensaje = document.getElementById('mensaje');
  const boton = document.getElementById('boton-guardar');
  const tipo = formulario.dataset.tipo;
  const idEditar = parametroUrl('editar');
  const campo = (id) => document.getElementById(id);
  let versionLeida = null;

  campo('fecha').max = hoyISO();
  campo('fecha').value = hoyISO();
  conectarContador(campo('descripcion'));

  const catalogos = await peticionGet('/catalogos');
  if (!catalogos.ok) {
    mostrarMensaje(mensaje, 'error', catalogos.datos.mensaje);
    return;
  }
  llenarSelect(campo('categoria'), catalogos.datos.categorias.map((c) => ({ valor: c.id, texto: c.nombre })), 'Selecciona…');
  llenarSelect(campo('ubicacion'), catalogos.datos.ubicaciones.map((u) => ({ valor: u.id, texto: u.nombre })), 'Selecciona…');

  if (idEditar) {
    const resultado = await peticionGet(`/objetos/${encodeURIComponent(idEditar)}`);
    if (!resultado.ok || !resultado.datos.es_propio) {
      mostrarMensaje(mensaje, 'error', 'No se encontró el reporte que quieres editar.');
      formulario.classList.add('oculto');
      return;
    }
    const objeto = resultado.datos.objeto;
    versionLeida = objeto.version;
    document.getElementById('titulo-pagina').textContent = 'Editar reporte';
    campo('nombre').value = objeto.nombre;
    campo('categoria').value = objeto.categoria_id;
    campo('ubicacion').value = objeto.ubicacion_id;
    campo('detalle-ubicacion').value = objeto.detalle_ubicacion || '';
    campo('fecha').value = objeto.fecha_evento;
    campo('descripcion').value = objeto.descripcion;
    campo('descripcion').dispatchEvent(new Event('input'));
    boton.textContent = 'Guardar cambios';
  }

  function validar() {
    limpiarErroresCampos(formulario);
    let valido = true;
    if (!longitudValida(campo('nombre').value, 3, 120)) { mostrarError(campo('nombre'), 'Entre 3 y 120 caracteres'); valido = false; }
    if (!campo('categoria').value) { mostrarError(campo('categoria'), 'Selecciona una categoría'); valido = false; }
    if (!campo('ubicacion').value) { mostrarError(campo('ubicacion'), 'Selecciona una ubicación'); valido = false; }
    if (!campo('fecha').value || campo('fecha').value > hoyISO()) { mostrarError(campo('fecha'), 'La fecha no puede ser futura'); valido = false; }
    if (!longitudValida(campo('descripcion').value, 10, 500)) { mostrarError(campo('descripcion'), 'Entre 10 y 500 caracteres'); valido = false; }
    return valido;
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarMensaje(mensaje);
    if (!validar()) return;

    const datos = {
      nombre: campo('nombre').value.trim(),
      categoria_id: Number(campo('categoria').value),
      ubicacion_id: Number(campo('ubicacion').value),
      detalle_ubicacion: campo('detalle-ubicacion').value.trim(),
      fecha_evento: campo('fecha').value,
      descripcion: campo('descripcion').value.trim(),
    };

    bloquearBoton(boton, 'Guardando…');
    const resultado = idEditar
      ? await peticionProtegida(`/objetos/${encodeURIComponent(idEditar)}`, 'PUT', { ...datos, version: versionLeida })
      : await peticionSegura('/objetos', { ...datos, tipo });
    desbloquearBoton(boton);

    if (resultado.ok) {
      window.location.href = `detalle-objeto.html?id=${encodeURIComponent(resultado.datos.objeto.id)}&creado=1`;
      return;
    }
    mostrarErroresCampos(formulario, resultado.datos.errores);
    mostrarMensaje(mensaje, resultado.status === 409 ? 'advertencia' : 'error', mensajeDeError(resultado));
  });
});
