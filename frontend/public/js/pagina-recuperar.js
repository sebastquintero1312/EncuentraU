/* Solicitud de recuperación de contraseña. La respuesta es la misma exista o
   no el correo (no se revela qué cuentas están registradas). */

sesionLista.then(() => {
  const formulario = document.getElementById('form-recuperar');
  const mensaje = document.getElementById('mensaje');

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const correo = document.getElementById('correo');
    limpiarErroresCampos(formulario);
    limpiarMensaje(mensaje);
    if (!correoValido(correo.value.trim())) { mostrarError(correo, 'Escribe un correo válido'); return; }

    const boton = document.getElementById('boton-recuperar');
    bloquearBoton(boton, 'Enviando…');
    const resultado = await peticionSegura('/auth/recuperar', { correo: correo.value.trim() });
    desbloquearBoton(boton);
    mostrarMensaje(mensaje, resultado.ok ? 'info' : 'error', resultado.datos.mensaje);
    if (resultado.ok) formulario.reset();
  });
});
