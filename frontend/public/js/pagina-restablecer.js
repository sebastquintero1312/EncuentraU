// Si llegan por un enlace tipo restablecer-contrasena.html?token=xxxx,
// precargamos el campo para que no tengan que pegarlo a mano.
const parametrosRestablecer = new URLSearchParams(window.location.search);
const tokenDeLaUrl = parametrosRestablecer.get('token');
if (tokenDeLaUrl) {
  document.getElementById('token').value = tokenDeLaUrl;
}

activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');
activarMostrarPassword('btn-mostrar-confirmar', 'confirmar');
activarIndicadorContrasena(
  document.getElementById('contrasena'),
  'lista-requisitos', 'barra-fortaleza', 'etiqueta-fortaleza'
);

document.getElementById('form-restablecer').addEventListener('submit', async function (evento) {
  evento.preventDefault();

  const token = document.getElementById('token');
  const contrasena = document.getElementById('contrasena');
  const confirmar = document.getElementById('confirmar');
  const mensajeGeneral = document.getElementById('mensaje-general-error');
  const mensajeConfirmacion = document.getElementById('mensaje-confirmacion');
  const boton = document.getElementById('btn-restablecer');
  let valido = true;

  [token, contrasena, confirmar].forEach(limpiarError);
  mensajeGeneral.classList.remove('visible');

  if (campoVacio(token.value)) {
    mostrarError(token, 'Pega el token que recibiste');
    valido = false;
  }

  const requisitos = evaluarContrasena(contrasena.value);
  if (campoVacio(contrasena.value)) {
    mostrarError(contrasena, 'La nueva contraseña es obligatoria');
    valido = false;
  } else if (!Object.values(requisitos).every(Boolean)) {
    mostrarError(contrasena, 'La contraseña no cumple todos los requisitos de arriba');
    valido = false;
  }

  if (confirmar.value !== contrasena.value) {
    mostrarError(confirmar, 'Las contraseñas no coinciden');
    valido = false;
  }

  if (!valido) return;

  boton.disabled = true;
  boton.textContent = 'Cambiando...';

  try {
    const resultado = await peticionSegura('/auth/restablecer', {
      token: token.value.trim(),
      contrasena: contrasena.value,
      confirmar_contrasena: confirmar.value,
    });

    if (resultado.ok) {
      mensajeConfirmacion.textContent = 'Tu contraseña fue actualizada. Ya puedes iniciar sesión.';
      mensajeConfirmacion.classList.add('visible');
      document.getElementById('form-restablecer').reset();
    } else {
      mensajeGeneral.textContent = resultado.datos.mensaje || 'No fue posible cambiar la contraseña';
      mensajeGeneral.classList.add('visible');
    }
  } catch (error) {
    mensajeGeneral.textContent = 'No se pudo conectar con el servidor. Verifica que el backend Flask esté corriendo.';
    mensajeGeneral.classList.add('visible');
  } finally {
    boton.disabled = false;
    boton.textContent = 'Cambiar contraseña';
  }
});
