/* ============================================
   SESION.JS
   ============================================
   Maneja la sesión real del usuario en el frontend: consultarla,
   exigirla en páginas protegidas, y cerrar sesión.

   IMPORTANTE: esto es solo para la EXPERIENCIA de usuario (evitar que
   alguien vea una página vacía o rota). La autorización real siempre la
   verifica el backend en cada petición; el frontend nunca es la autoridad.
*/

async function obtenerSesion() {
  const resultado = await peticionGet('/auth/sesion');
  return resultado.datos.usuario || null;
}

// Llamar al inicio de páginas que requieren estar autenticado.
// Si se pasa {admin: true}, además exige rol de administrador.
// Devuelve el usuario si todo está en orden (para poder usarlo en la página).
async function protegerPagina(opciones) {
  opciones = opciones || {};
  const usuario = await obtenerSesion();

  if (!usuario) {
    window.location.href = 'login.html';
    return null;
  }
  if (opciones.admin && usuario.rol !== 'administrador') {
    window.location.href = 'panel-ciudadano.html';
    return null;
  }
  return usuario;
}

// Conecta el link "Cerrar sesión" del menú (todas las páginas internas lo
// tienen) para que realmente cierre la sesión en el backend antes de volver
// al inicio, en vez de solo navegar a index.html.
function conectarCerrarSesion() {
  document.querySelectorAll('a[href="index.html"]').forEach(enlace => {
    if (enlace.textContent.trim() !== 'Cerrar sesión') return;
    enlace.addEventListener('click', async function (evento) {
      evento.preventDefault();
      await peticionProtegida('/auth/logout', 'POST');
      window.location.href = 'index.html';
    });
  });
}

document.addEventListener('DOMContentLoaded', conectarCerrarSesion);
