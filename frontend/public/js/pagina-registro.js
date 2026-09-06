activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');
activarMostrarPassword('btn-mostrar-confirmar', 'confirmar');
activarIndicadorContrasena(
  document.getElementById('contrasena'),
  'lista-requisitos', 'barra-fortaleza', 'etiqueta-fortaleza',
  document.getElementById('correo'), document.getElementById('primerNombre')
);

document.getElementById('form-registro').addEventListener('submit', async function (evento) {
  evento.preventDefault();

  const primerNombre = document.getElementById('primerNombre');
  const segundoNombre = document.getElementById('segundoNombre');
  const primerApellido = document.getElementById('primerApellido');
  const segundoApellido = document.getElementById('segundoApellido');
  const correo = document.getElementById('correo');
  const contrasena = document.getElementById('contrasena');
  const confirmar = document.getElementById('confirmar');
  const mensajeGeneral = document.getElementById('mensaje-general-error');
  const boton = document.getElementById('btn-registro');
  let valido = true;

  [primerNombre, segundoNombre, primerApellido, segundoApellido, correo, contrasena, confirmar].forEach(limpiarError);
  mensajeGeneral.classList.remove('visible');

  if (campoVacio(primerNombre.value)) {
    mostrarError(primerNombre, 'El primer nombre es obligatorio');
    valido = false;
  } else if (!longitudValida(primerNombre.value, 2, 40)) {
    mostrarError(primerNombre, 'Debe tener entre 2 y 40 caracteres');
    valido = false;
  }

  if (campoVacio(primerApellido.value)) {
    mostrarError(primerApellido, 'El primer apellido es obligatorio');
    valido = false;
  } else if (!longitudValida(primerApellido.value, 2, 40)) {
    mostrarError(primerApellido, 'Debe tener entre 2 y 40 caracteres');
    valido = false;
  }

  if (campoVacio(correo.value)) {
    mostrarError(correo, 'El correo es obligatorio');
    valido = false;
  } else if (!correoValido(correo.value)) {
    mostrarError(correo, 'Ingresa un correo válido');
    valido = false;
  }

  // Validación visual de la contraseña. La validación real y obligatoria la hace el backend.
  const requisitos = evaluarContrasena(contrasena.value, correo.value, primerNombre.value);
  const cumpleTodo = Object.values(requisitos).every(Boolean);
  if (campoVacio(contrasena.value)) {
    mostrarError(contrasena, 'La contraseña es obligatoria');
    valido = false;
  } else if (!cumpleTodo) {
    mostrarError(contrasena, 'La contraseña no cumple todos los requisitos de arriba');
    valido = false;
  }

  if (campoVacio(confirmar.value)) {
    mostrarError(confirmar, 'Confirma tu contraseña');
    valido = false;
  } else if (confirmar.value !== contrasena.value) {
    mostrarError(confirmar, 'Las contraseñas no coinciden');
    valido = false;
  }

  if (!valido) return;

  boton.disabled = true;
  boton.textContent = 'Creando cuenta...';

  try {
    const resultado = await peticionSegura('/auth/registro', {
      primer_nombre: primerNombre.value.trim(),
      segundo_nombre: segundoNombre.value.trim(),
      primer_apellido: primerApellido.value.trim(),
      segundo_apellido: segundoApellido.value.trim(),
      correo: correo.value.trim(),
      contrasena: contrasena.value,
      confirmar_contrasena: confirmar.value,
    });

    if (resultado.ok) {
      window.location.href = 'login.html';
    } else {
      mensajeGeneral.textContent = resultado.datos.mensaje || 'No fue posible completar el registro';
      mensajeGeneral.classList.add('visible');

      // Si el backend devuelve errores por campo, los mostramos también ahí
      const errores = resultado.datos.errores || {};
      if (errores.correo) mostrarError(correo, errores.correo);
      if (errores.primer_nombre) mostrarError(primerNombre, errores.primer_nombre);
      if (errores.primer_apellido) mostrarError(primerApellido, errores.primer_apellido);
      if (errores.confirmar_contrasena) mostrarError(confirmar, errores.confirmar_contrasena);
      if (errores.contrasena) mostrarError(contrasena, Array.isArray(errores.contrasena) ? errores.contrasena[0] : errores.contrasena);
    }
  } catch (error) {
    mensajeGeneral.textContent = 'No se pudo conectar con el servidor. Verifica que el backend Flask esté corriendo.';
    mensajeGeneral.classList.add('visible');
  } finally {
    boton.disabled = false;
    boton.textContent = 'Registrarme';
  }
});
