/* Inicio de sesión. Si el correo aún no está verificado, ofrece reenviar el enlace. */

sesionLista.then(() => {
  const formulario = document.getElementById('form-login');
  const mensaje = document.getElementById('mensaje');
  const bloqueReenvio = document.getElementById('bloque-reenvio');
  const correo = document.getElementById('correo');
  const contrasena = document.getElementById('contrasena');
  const boton = document.getElementById('boton-entrar');

  activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErroresCampos(formulario);
    limpiarMensaje(mensaje);
    bloqueReenvio.classList.add('oculto');

    let valido = true;
    if (!correoValido(correo.value.trim())) { mostrarError(correo, 'Escribe un correo válido'); valido = false; }
    if (campoVacio(contrasena.value)) { mostrarError(contrasena, 'Escribe tu contraseña'); valido = false; }
    if (!valido) return;

    bloquearBoton(boton, 'Ingresando…');
    const resultado = await peticionSegura('/auth/login', { correo: correo.value.trim(), contrasena: contrasena.value });
    desbloquearBoton(boton);

    if (resultado.ok) {
      const siguiente = parametroUrl('siguiente');
      window.location.href = esPaginaInterna(siguiente) ? siguiente : panelDeRol(resultado.datos.usuario.rol);
      return;
    }
    mostrarMensaje(mensaje, resultado.status === 403 ? 'advertencia' : 'error', resultado.datos.mensaje || 'No fue posible iniciar sesión');
    if (resultado.datos.codigo === 'correo_no_verificado') bloqueReenvio.classList.remove('oculto');
  });

  document.getElementById('boton-reenviar').addEventListener('click', async (evento) => {
    const botonReenvio = evento.currentTarget;
    bloquearBoton(botonReenvio, 'Enviando…');
    const resultado = await peticionSegura('/auth/reenviar-verificacion', { correo: correo.value.trim() });
    desbloquearBoton(botonReenvio);
    bloqueReenvio.classList.add('oculto');
    mostrarMensaje(mensaje, resultado.ok ? 'info' : 'error', resultado.datos.mensaje);
  });
});
