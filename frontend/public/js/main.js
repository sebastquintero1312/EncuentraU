/* ============================================
   MAIN.JS
   ============================================
   Funciones generales que se usan en varias páginas
   (no son específicas de un formulario en particular).
*/

console.log('EncuentraU frontend cargado');

// Resalta en el menú el enlace de la página en la que estamos
document.querySelectorAll('.nav-links a').forEach(link => {
  const paginaActual = window.location.pathname.split('/').pop();
  if (link.getAttribute('href') === paginaActual) {
    link.classList.add('activo');
  }
});

// Convierte un estado (ej: "en proceso") en la clase CSS del badge (ej: "badge-proceso")
// Se usa en varias páginas que muestran listas de reportes
function claseBadgeEstado(estado) {
  const mapa = {
    activo: 'activo',
    'en proceso': 'proceso',
    resuelto: 'resuelto',
    cerrado: 'cerrado',
    pendiente: 'pendiente'
  };
  return 'badge-' + (mapa[estado] || 'activo');
}

// En el futuro, cuando exista backend, aquí se harán las peticiones con fetch. Ejemplo:
// fetch('http://localhost:3000/api/reportes')
//   .then(res => res.json())
//   .then(data => console.log(data));
