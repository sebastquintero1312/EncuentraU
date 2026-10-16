/* Registro de estudiantes. La validación real (dominio institucional,
   fortaleza de la contraseña) la vuelve a hacer el backend. */

const DOMINIO_INSTITUCIONAL = '@sanmateo.edu.co';

sesionLista.then(() => {
  const formulario = document.getElementById('form-registro');
  const mensaje = document.getElementById('mensaje');
  const boton = document.getElementById('boton-registro');
  const campo = (id) => document.getElementById(id);

  activarIndicadorContrasena(campo('contrasena'), 'lista-requisitos', 'barra-fortaleza', 'etiqueta-fortaleza');
  activarMostrarPassword('btn-mostrar-contrasena', 'contrasena');
  activarMostrarPassword('btn-mostrar-confirmar', 'confirmar');

  function validar() {
    limpiarErroresCampos(formulario);
    let valido = true;
    if (campoVacio(campo('primerNombre').value)) { mostrarError(campo('primerNombre'), 'El primer nombre es obligatorio'); valido = false; }
    if (campoVacio(campo('primerApellido').value)) { mostrarError(campo('primerApellido'), 'El primer apellido es obligatorio'); valido = false; }
    const correo = campo('correo').value.trim().toLowerCase();
    if (!correoValido(correo)) { mostrarError(campo('correo'), 'Escribe un correo válido'); valido = false; }
    else if (!correo.endsWith(DOMINIO_INSTITUCIONAL)) { mostrarError(campo('correo'), `Debes usar tu correo institucional (${DOMINIO_INSTITUCIONAL})`); valido = false; }
    const requisitos = evaluarContrasena(campo('contrasena').value);
    if (!Object.values(requisitos).every(Boolean)) { mostrarError(campo('contrasena'), 'La contraseña no cumple todos los requisitos'); valido = false; }
    if (campo('contrasena').value !== campo('confirmar').value) { mostrarError(campo('confirmar'), 'Las contraseñas no coinciden'); valido = false; }
    return valido;
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarMensaje(mensaje);
    if (!validar()) return;

    bloquearBoton(boton, 'Creando cuenta…');
    const resultado = await peticionSegura('/auth/registro', {
      primer_nombre: campo('primerNombre').value.trim(),
      segundo_nombre: campo('segundoNombre').value.trim(),
      primer_apellido: campo('primerApellido').value.trim(),
      segundo_apellido: campo('segundoApellido').value.trim(),
      correo: campo('correo').value.trim().toLowerCase(),
      contrasena: campo('contrasena').value,
      confirmar_contrasena: campo('confirmar').value,
    });
    desbloquearBoton(boton);

    if (resultado.ok) {
      document.getElementById('texto-exito').textContent = resultado.datos.mensaje;
      document.getElementById('bloque-formulario').classList.add('oculto');
      document.getElementById('registro-exitoso').classList.remove('oculto');
      return;
    }
    mostrarErroresCampos(formulario, resultado.datos.errores);
    mostrarMensaje(mensaje, 'error', resultado.datos.mensaje || 'No fue posible completar el registro');
  });
});
