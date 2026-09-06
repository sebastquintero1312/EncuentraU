/* ============================================
   MAIN.JS
   ============================================
   Funciones generales que se usan en varias páginas
   (no son específicas de un formulario en particular).
*/

// Resalta en el menú el enlace de la página en la que estamos
document.querySelectorAll('.nav-links a').forEach(link => {
  const paginaActual = window.location.pathname.split('/').pop();
  if (link.getAttribute('href') === paginaActual) {
    link.classList.add('activo');
  }
});

// Convierte un estado (ej: "en_proceso") en la clase CSS del badge (ej: "badge-proceso")
// Se usa en varias páginas que muestran listas de reportes
function claseBadgeEstado(estado) {
  const mapa = {
    activo: 'activo',
    en_proceso: 'proceso',
    resuelto: 'resuelto',
    cerrado: 'cerrado',
    cancelado: 'cancelado',
    pendiente: 'pendiente',
    en_revision: 'proceso',
    aprobada: 'resuelto',
    rechazada: 'cerrado',
    cancelada: 'cancelado',
  };
  return 'badge-' + (mapa[estado] || 'activo');
}

// Texto legible para un estado (los valores que vienen de la API usan
// guión bajo, ej. "en_proceso"; aquí se muestran como "en proceso").
function textoEstado(estado) {
  return (estado || '').replace(/_/g, ' ');
}

/* ---- Construcción segura de elementos con datos del usuario ----
   NUNCA se usa innerHTML con datos que vienen de un reporte, usuario o
   solicitud: esos textos pueden contener HTML/JS (ver prueba de XSS
   almacenado en docs/evidencia/). Se usa siempre textContent. */

// Crea un elemento con texto plano y clases opcionales.
function crearElemento(etiqueta, texto, claseCss) {
  const el = document.createElement(etiqueta);
  if (texto !== undefined && texto !== null) el.textContent = texto;
  if (claseCss) el.className = claseCss;
  return el;
}

// Crea un <span class="badge badge-X">texto</span> a partir de un valor de
// estado/tipo controlado (viene de un enum fijo de la API, no de texto libre).
function crearBadge(texto, claseExtra) {
  return crearElemento('span', textoEstado(texto), `badge ${claseExtra}`);
}
