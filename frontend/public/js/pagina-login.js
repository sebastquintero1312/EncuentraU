activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');

document.getElementById('form-login').addEventListener('submit', async function (evento) {
  evento.preventDefault();

  const correo = document.getElementById('correo');
  const contrasena = document.getElementById('contrasena');
  const mensajeGeneral = document.getElementById('mensaje-general-error');
  const boton = document.getElementById('btn-login');
  let valido = true;

  limpiarError(correo);
  limpiarError(contrasena);
  mensajeGeneral.classList.remove('visible');

  if (campoVacio(correo.value)) {
    mostrarError(correo, 'El correo es obligatorio');
    valido = false;
  } else if (!correoValido(correo.value)) {
    mostrarError(correo, 'Ingresa un correo válido');
    valido = false;
  }

  if (campoVacio(contrasena.value)) {
    mostrarError(contrasena, 'La contraseña es obligatoria');
    valido = false;
  }

  if (!valido) return;

  boton.disabled = true;
  boton.textContent = 'Ingresando...';

  try {
    const resultado = await peticionSegura('/auth/login', {
      correo: correo.value.trim(),
      contrasena: contrasena.value,
    });

    if (resultado.ok) {
      const rol = resultado.datos.usuario && resultado.datos.usuario.rol;
      window.location.href = rol === 'administrador' ? 'panel-admin.html' : 'panel-ciudadano.html';
    } else {
      mensajeGeneral.textContent = resultado.datos.mensaje || 'No fue posible iniciar sesión';
      mensajeGeneral.classList.add('visible');
    }
  } catch (error) {
    mensajeGeneral.textContent = 'No se pudo conectar con el servidor. Verifica que el backend Flask esté corriendo.';
    mensajeGeneral.classList.add('visible');
  } finally {
    boton.disabled = false;
    boton.textContent = 'Iniciar sesión';
  }
});
