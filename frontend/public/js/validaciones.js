/* ============================================
   VALIDACIONES.JS
   ============================================
   Funciones básicas de validación del lado del frontend.
   IMPORTANTE: esto NO es seguridad real, solo evita errores obvios
   del usuario mientras no existe un backend que valide de verdad.
*/

function campoVacio(valor) {
  return !valor || valor.trim() === '';
}

function correoValido(correo) {
  const patron = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return patron.test(correo);
}

function longitudValida(valor, min, max) {
  const largo = valor.trim().length;
  return largo >= min && largo <= max;
}

// Muestra un mensaje de error debajo del campo indicado
function mostrarError(input, mensaje) {
  const grupo = input.closest('.form-group');
  if (!grupo) return;
  const error = grupo.querySelector('.mensaje-error');
  if (error) error.textContent = mensaje;
  input.classList.add('input-error');
}

// Limpia el error de un campo (se llama antes de validar de nuevo)
function limpiarError(input) {
  const grupo = input.closest('.form-group');
  if (!grupo) return;
  const error = grupo.querySelector('.mensaje-error');
  if (error) error.textContent = '';
  input.classList.remove('input-error');
}
