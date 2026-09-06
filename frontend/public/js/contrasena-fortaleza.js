/* ============================================
   CONTRASENA-FORTALEZA.JS
   ============================================
   Validación visual de la contraseña mientras el usuario escribe.
   IMPORTANTE: esto es solo una AYUDA VISUAL para el usuario.
   La validación definitiva y obligatoria ocurre en el backend Python.
*/

// Lista corta para dar retroalimentación visual (la lista completa vive en el backend)
const CONTRASENAS_COMUNES_FRONTEND = [
  '12345678', '123456789', '1234567890', 'password', 'password123',
  'qwerty', 'qwerty123', 'admin123', 'contrasena', 'contraseña123',
];

function evaluarContrasena(password, correo, nombre) {
  const passwordMin = (password || '').toLowerCase();
  const requisitos = {
    longitud: password.length >= 12,
    mayuscula: /[A-Z]/.test(password),
    minuscula: /[a-z]/.test(password),
    numero: /[0-9]/.test(password),
    especial: /[!@#$%^&*()_\-+=]/.test(password),
    noComun: !CONTRASENAS_COMUNES_FRONTEND.includes(passwordMin),
  };
  return requisitos;
}

function calcularFortaleza(requisitos) {
  const cumplidos = Object.values(requisitos).filter(Boolean).length;
  if (cumplidos <= 3) return 'debil';
  if (cumplidos <= 5) return 'media';
  return 'fuerte';
}

// Conecta un input de contraseña con la lista de requisitos (<ul>) y el
// medidor de fortaleza (barra + etiqueta) para actualizarlos en tiempo real.
function activarIndicadorContrasena(inputPassword, listaId, barraId, etiquetaId, correoInput, nombreInput) {
  const lista = document.getElementById(listaId);
  const barra = document.getElementById(barraId);
  const etiqueta = document.getElementById(etiquetaId);

  const textos = {
    longitud: 'Mínimo 12 caracteres',
    mayuscula: 'Una mayúscula',
    minuscula: 'Una minúscula',
    numero: 'Un número',
    especial: 'Un carácter especial',
    noComun: 'No es una contraseña común',
  };

  function actualizar() {
    const correo = correoInput ? correoInput.value : '';
    const nombre = nombreInput ? nombreInput.value : '';
    const requisitos = evaluarContrasena(inputPassword.value, correo, nombre);

    lista.innerHTML = '';
    Object.keys(textos).forEach(clave => {
      const cumplido = requisitos[clave];
      const item = document.createElement('li');
      item.className = cumplido ? 'cumplido' : '';
      item.innerHTML = `<span class="marca">${cumplido ? '✓' : '○'}</span> ${textos[clave]}`;
      lista.appendChild(item);
    });

    const nivel = calcularFortaleza(requisitos);
    const anchos = { debil: '33%', media: '66%', fuerte: '100%' };
    const etiquetas = { debil: 'Débil', media: 'Media', fuerte: 'Fuerte' };

    barra.className = 'barra ' + nivel;
    barra.style.width = inputPassword.value ? anchos[nivel] : '0%';
    etiqueta.className = 'etiqueta-fortaleza ' + nivel;
    etiqueta.textContent = inputPassword.value ? etiquetas[nivel] : '';
  }

  inputPassword.addEventListener('input', actualizar);
  actualizar();
}

// Agrega el botón "Mostrar/Ocultar" a un campo de contraseña
function activarMostrarPassword(botonId, inputId) {
  const boton = document.getElementById(botonId);
  const input = document.getElementById(inputId);
  boton.addEventListener('click', function () {
    const oculto = input.type === 'password';
    input.type = oculto ? 'text' : 'password';
    boton.textContent = oculto ? 'Ocultar' : 'Mostrar';
  });
}
