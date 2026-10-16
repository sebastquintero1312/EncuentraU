/* ============================================
   SESION.JS
   ============================================
   Consulta y cierre de la sesión real del usuario.

   IMPORTANTE: esto es solo para la EXPERIENCIA de usuario (llevar a cada
   persona a su panel y no mostrar pantallas que no puede usar). La
   autorización real siempre la verifica el backend en cada petición:
   aunque alguien modifique este archivo en su navegador, el servidor le
   responderá 401/403.
*/

const PANEL_POR_ROL = {
  estudiante: 'panel-estudiante.html',
  encargado: 'panel-encargado.html',
  administrador: 'panel-admin.html',
};

async function obtenerSesion() {
  const resultado = await peticionGet('/auth/sesion');
  return (resultado.ok && resultado.datos.usuario) || null;
}

function panelDeRol(rol) {
  return PANEL_POR_ROL[rol] || 'index.html';
}

async function cerrarSesion() {
  await peticionProtegida('/auth/logout', 'POST');
  window.location.href = 'index.html';
}
