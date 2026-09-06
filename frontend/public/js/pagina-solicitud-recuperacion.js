(async function () {
  const usuario = await protegerPagina();
  if (!usuario) return;

  const parametros = new URLSearchParams(window.location.search);
  const objetoId = parametros.get('id');

  const resultadoObjeto = await peticionGet(`/objetos/${objetoId}`);
  const tituloObjeto = document.getElementById('nombre-objeto');
  if (!resultadoObjeto.ok) {
    tituloObjeto.textContent = 'Objeto no encontrado';
    document.getElementById('form-solicitud').style.display = 'none';
    return;
  }
  tituloObjeto.textContent = 'Objeto: ' + resultadoObjeto.datos.objeto.nombre;

  document.getElementById('form-solicitud').addEventListener('submit', async function (evento) {
    evento.preventDefault();

    const contacto = document.getElementById('contacto');
    const mensaje = document.getElementById('mensaje');
    const mensajeGeneral = document.getElementById('mensaje-general-error');
    let valido = true;

    [contacto, mensaje].forEach(limpiarError);
    if (mensajeGeneral) mensajeGeneral.classList.remove('visible');

    if (campoVacio(contacto.value)) {
      mostrarError(contacto, 'El contacto es obligatorio');
      valido = false;
    }
    if (campoVacio(mensaje.value)) {
      mostrarError(mensaje, 'Cuéntanos por qué el objeto es tuyo');
      valido = false;
    } else if (!longitudValida(mensaje.value, 15, 400)) {
      mostrarError(mensaje, 'El mensaje debe tener entre 15 y 400 caracteres');
      valido = false;
    }

    if (!valido) return;

    const resultado = await peticionProtegida('/solicitudes', 'POST', {
      objeto_id: Number(objetoId),
      contacto: contacto.value.trim(),
      mensaje: mensaje.value.trim(),
    });

    if (resultado.ok) {
      document.getElementById('mensaje-confirmacion').textContent =
        'Tu solicitud fue enviada. El administrador la revisará y el dueño del reporte podrá ver tu mensaje para verificarla.';
      document.getElementById('mensaje-confirmacion').classList.add('visible');
      document.getElementById('form-solicitud').reset();
      document.getElementById('form-solicitud').style.display = 'none';
    } else {
      const texto = resultado.datos.mensaje || 'No fue posible enviar la solicitud';
      const errores = resultado.datos.errores || {};
      const detalle = errores.objeto_id || errores.contacto || errores.mensaje || '';
      if (mensajeGeneral) {
        mensajeGeneral.textContent = detalle ? `${texto}: ${detalle}` : texto;
        mensajeGeneral.classList.add('visible');
      }
    }
  });
})();
