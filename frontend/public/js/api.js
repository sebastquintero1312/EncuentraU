/* ============================================
   API.JS
   ============================================
   Configuración y helpers para hablar con el backend Flask.
   El backend usa cookies de sesión (HttpOnly), así que siempre mandamos
   credentials: 'include'. También manejamos el token CSRF: se pide una
   vez y se reenvía en el header X-CSRFToken en cada petición que cambia
   datos (POST).

   IMPORTANTE: nada de esto guarda contraseñas ni tokens sensibles en
   localStorage/sessionStorage. El token CSRF se guarda solo en una
   variable de JavaScript en memoria, se pierde al recargar la página
   (y se vuelve a pedir automáticamente).
*/

const API_BASE = 'http://127.0.0.1:5000/api';

let csrfTokenEnMemoria = null;

async function obtenerCsrfToken() {
  const respuesta = await fetch(`${API_BASE}/auth/csrf-token`, {
    method: 'GET',
    credentials: 'include',
  });
  const datos = await respuesta.json();
  csrfTokenEnMemoria = datos.csrf_token;
  return csrfTokenEnMemoria;
}

async function peticionSegura(ruta, cuerpo) {
  if (!csrfTokenEnMemoria) {
    await obtenerCsrfToken();
  }

  const respuesta = await fetch(`${API_BASE}${ruta}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfTokenEnMemoria,
    },
    body: JSON.stringify(cuerpo),
  });

  const datos = await respuesta.json().catch(() => ({}));
  return { ok: respuesta.ok, status: respuesta.status, datos };
}
