/* ============================================
   API.JS
   ============================================
   Configuración y helpers para hablar con el backend Flask.
   El backend usa cookies de sesión (HttpOnly), así que siempre mandamos
   credentials: 'include'. También manejamos el token CSRF: se pide una
   vez y se reenvía en el header X-CSRFToken en cada petición que cambia
   datos (POST/PUT/DELETE).

   IMPORTANTE: nada de esto guarda contraseñas ni tokens sensibles en
   localStorage/sessionStorage. El token CSRF se guarda solo en una
   variable de JavaScript en memoria, se pierde al recargar la página
   (y se vuelve a pedir automáticamente).
*/

// Ruta relativa: el frontend se sirve desde el mismo origen que la API
// (Flask sirve frontend/public como estático), así que no hace falta un
// dominio absoluto ni CORS en producción.
const API_BASE = '/api';

const ERROR_DE_RED = { mensaje: 'No fue posible conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.' };

let csrfTokenEnMemoria = null;

async function obtenerCsrfToken() {
  const respuesta = await fetch(`${API_BASE}/auth/csrf-token`, { method: 'GET', credentials: 'include' });
  const datos = await respuesta.json();
  csrfTokenEnMemoria = datos.csrf_token;
  return csrfTokenEnMemoria;
}

function _actualizarCsrfSiVieneEnLaRespuesta(datos) {
  // Login y logout limpian la sesión del servidor (anti session-fixation),
  // lo que invalida el token CSRF que teníamos en memoria. El backend manda
  // uno nuevo en la respuesta cuando eso pasa.
  if (datos && datos.csrf_token) {
    csrfTokenEnMemoria = datos.csrf_token;
  }
}

// Petición GET simple, sin CSRF (las lecturas no lo necesitan).
// `parametros` es un objeto opcional que se convierte en ?clave=valor
// (URLSearchParams se encarga de codificar los valores).
async function peticionGet(ruta, parametros) {
  let url = `${API_BASE}${ruta}`;
  if (parametros) {
    const limpios = Object.entries(parametros).filter(([, v]) => v !== undefined && v !== null && v !== '');
    if (limpios.length) url += '?' + new URLSearchParams(limpios).toString();
  }
  try {
    const respuesta = await fetch(url, { credentials: 'include' });
    const datos = await respuesta.json().catch(() => ({}));
    return { ok: respuesta.ok, status: respuesta.status, datos };
  } catch (error) {
    return { ok: false, status: 0, datos: ERROR_DE_RED };
  }
}

// Petición que modifica datos (POST/PUT/DELETE): siempre lleva CSRF.
async function peticionProtegida(ruta, metodo, cuerpo) {
  try {
    if (!csrfTokenEnMemoria) {
      await obtenerCsrfToken();
    }
    const opciones = {
      method: metodo,
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfTokenEnMemoria },
    };
    if (cuerpo !== undefined) {
      opciones.headers['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(cuerpo);
    }
    const respuesta = await fetch(`${API_BASE}${ruta}`, opciones);
    const datos = await respuesta.json().catch(() => ({}));
    _actualizarCsrfSiVieneEnLaRespuesta(datos);
    return { ok: respuesta.ok, status: respuesta.status, datos };
  } catch (error) {
    return { ok: false, status: 0, datos: ERROR_DE_RED };
  }
}

// Alias: POST protegido (login, registro, recuperar, restablecer lo usan así).
function peticionSegura(ruta, cuerpo) {
  return peticionProtegida(ruta, 'POST', cuerpo);
}
