/* Restablecimiento de contraseña con el token del enlace del correo. */

const tokenRecuperacion = parametroUrl('token');
if (tokenRecuperacion) window.history.replaceState(null, '', window.location.pathname);

sesionLista.then(() => {
  const formulario = document.getElementById('form-restablecer');
  const mensaje = document.getElementById('mensaje');
  const contrasena = document.getElementById('contrasena');
  const confirmar = document.getElementById('confirmar');

  activarIndicadorContrasena(contrasena, 'lista-requisitos', 'barra-fortaleza', 'etiqueta-fortaleza');
  activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');

  if (!tokenRecuperacion) {
    mostrarMensaje(mensaje, 'error', 'El enlace está incompleto. Ábrelo directamente desde el correo o pide uno nuevo.');
    formulario.classList.add('oculto');
    return;
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErroresCampos(formulario);
    limpiarMensaje(mensaje);
    if (!Object.values(evaluarContrasena(contrasena.value)).every(Boolean)) {
      mostrarError(contrasena, 'La contraseña no cumple todos los requisitos');
      return;
    }
    if (contrasena.value !== confirmar.value) { mostrarError(confirmar, 'Las contraseñas no coinciden'); return; }

    const boton = document.getElementById('boton-guardar');
    bloquearBoton(boton, 'Guardando…');
    const resultado = await peticionSegura('/auth/restablecer', {
      token: tokenRecuperacion, contrasena: contrasena.value, confirmar_contrasena: confirmar.value,
    });
    desbloquearBoton(boton);

    if (resultado.ok) {
      formulario.classList.add('oculto');
      mostrarMensaje(mensaje, 'exito', 'Tu contraseña se actualizó. Ya puedes iniciar sesión.');
      return;
    }
    if (resultado.datos.errores) {
      mostrarError(contrasena, [].concat(resultado.datos.errores).join('. '));
    }
    mostrarMensaje(mensaje, 'error', resultado.datos.mensaje);
  });
});
