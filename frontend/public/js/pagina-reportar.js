// Compartido por reportar-perdido.html y reportar-encontrado.html.
// El tipo ('perdido' o 'encontrado') viene del atributo data-tipo-reporte
// en <body> de cada página (evita scripts inline, ver CSP en el backend).

(async function () {
  const tipoReporte = document.body.dataset.tipoReporte;
  const usuario = await protegerPagina();
  if (!usuario) return;

  const formulario = document.getElementById('form-reporte');
  const mensajeGeneral = document.getElementById('mensaje-general-error');

  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();

    const nombreObjeto = document.getElementById('nombreObjeto');
    const categoria = document.getElementById('categoria');
    const descripcion = document.getElementById('descripcion');
    const ubicacion = document.getElementById('ubicacion');
    const fecha = document.getElementById('fecha');
    const boton = formulario.querySelector('button[type="submit"]');
    let valido = true;

    [nombreObjeto, categoria, descripcion, ubicacion, fecha].forEach(limpiarError);
    if (mensajeGeneral) mensajeGeneral.classList.remove('visible');

    if (campoVacio(nombreObjeto.value)) {
      mostrarError(nombreObjeto, 'El nombre del objeto es obligatorio');
      valido = false;
    }
    if (campoVacio(categoria.value)) {
      mostrarError(categoria, 'Selecciona una categoría');
      valido = false;
    }
    if (campoVacio(descripcion.value)) {
      mostrarError(descripcion, 'La descripción es obligatoria');
      valido = false;
    } else if (!longitudValida(descripcion.value, 10, 300)) {
      mostrarError(descripcion, 'La descripción debe tener entre 10 y 300 caracteres');
      valido = false;
    }
    if (campoVacio(ubicacion.value)) {
      mostrarError(ubicacion, 'Indica la ubicación');
      valido = false;
    }
    if (campoVacio(fecha.value)) {
      mostrarError(fecha, 'Selecciona una fecha');
      valido = false;
    }

    if (!valido) return;

    boton.disabled = true;
    boton.textContent = 'Enviando...';

    const resultado = await peticionProtegida('/objetos', 'POST', {
      tipo: tipoReporte,
      nombre: nombreObjeto.value.trim(),
      categoria: categoria.value,
      descripcion: descripcion.value.trim(),
      ubicacion: ubicacion.value.trim(),
      fecha_evento: fecha.value,
    });

    if (resultado.ok) {
      document.getElementById('mensaje-confirmacion').classList.add('visible');
      formulario.reset();
      formulario.style.display = 'none';
    } else if (mensajeGeneral) {
      const errores = resultado.datos.errores || {};
      const primerError = Object.values(errores)[0];
      mensajeGeneral.textContent = primerError || resultado.datos.mensaje || 'No fue posible enviar el reporte';
      mensajeGeneral.classList.add('visible');
    }

    boton.disabled = false;
    boton.textContent = 'Enviar reporte';
  });
})();
