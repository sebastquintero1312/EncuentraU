document.getElementById('form-recuperar').addEventListener('submit', async function (evento) {
  evento.preventDefault();

  const correo = document.getElementById('correo');
  const boton = document.getElementById('btn-recuperar');
  const mensajeConfirmacion = document.getElementById('mensaje-confirmacion');
  limpiarError(correo);
  let valido = true;

  if (campoVacio(correo.value)) {
    mostrarError(correo, 'El correo es obligatorio');
    valido = false;
  } else if (!correoValido(correo.value)) {
    mostrarError(correo, 'Ingresa un correo válido');
    valido = false;
  }

  if (!valido) return;

  boton.disabled = true;
  boton.textContent = 'Enviando...';

  try {
    const resultado = await peticionSegura('/auth/recuperar', { correo: correo.value.trim() });
    // Por seguridad, el backend SIEMPRE responde el mismo mensaje genérico,
    // exista o no el correo. Así no se puede saber qué correos están registrados.
    mensajeConfirmacion.textContent = resultado.datos.mensaje || 'Si el correo está registrado, recibirás instrucciones para continuar.';
    mensajeConfirmacion.classList.add('visible');
  } catch (error) {
    mensajeConfirmacion.textContent = 'No se pudo conectar con el servidor. Verifica que el backend Flask esté corriendo.';
    mensajeConfirmacion.classList.add('visible');
  } finally {
    boton.disabled = false;
    boton.textContent = 'Enviar enlace de recuperación';
  }
});
