/* Verificación del correo con el token del enlace. El token se quita de la
   barra de direcciones apenas se lee, para que no quede en el historial. */

const tokenVerificacion = parametroUrl('token');
if (tokenVerificacion) window.history.replaceState(null, '', window.location.pathname);

sesionLista.then(async () => {
  const estado = document.getElementById('estado-verificacion');

  function mostrarFallo(texto) {
    estado.classList.add('oculto');
    mostrarMensaje(document.getElementById('mensaje-fallo'), 'error', texto);
    document.getElementById('verificacion-fallida').classList.remove('oculto');
  }

  if (!tokenVerificacion) {
    mostrarFallo('El enlace está incompleto. Ábrelo directamente desde el correo que te enviamos.');
  } else {
    const resultado = await peticionSegura('/auth/verificar-correo', { token: tokenVerificacion });
    if (resultado.ok) {
      estado.classList.add('oculto');
      document.getElementById('verificacion-exitosa').classList.remove('oculto');
    } else {
      mostrarFallo(resultado.datos.mensaje || 'El enlace no es válido o ya expiró.');
    }
  }

  const formulario = document.getElementById('form-reenvio');
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const correo = document.getElementById('correo');
    limpiarErroresCampos(formulario);
    if (!correoValido(correo.value.trim())) { mostrarError(correo, 'Escribe un correo válido'); return; }
    const boton = document.getElementById('boton-reenviar');
    bloquearBoton(boton, 'Enviando…');
    const resultado = await peticionSegura('/auth/reenviar-verificacion', { correo: correo.value.trim() });
    desbloquearBoton(boton);
    mostrarMensaje(document.getElementById('mensaje-reenvio'), resultado.ok ? 'info' : 'error', resultado.datos.mensaje);
  });
});
