# FRONTEND.md — Frontend de EncuentraU v2.0

HTML + CSS + JavaScript vanilla, sin framework ni build step, servido por Flask desde el mismo origen que la API.

## Identidad visual

Rediseño completo inspirado en el sitio de la Fundación Universitaria San Mateo (sanmateo.edu.co): fuente **Poppins**, naranja institucional `#F47920`, azul marino `#0F172A`, barra superior oscura ("Soy estudiante / Soy encargado / Soy administrador"), menú blanco fijo con el logo, encabezados oscuros con una palabra en naranja, tarjeta de filtros "flotante" con filtros tipo píldora, tarjetas muy redondeadas y pie de página oscuro con borde naranja. Capturas reales: `docs/evidencia/capturas_v2/`.

- **Accesibilidad (WCAG AA)**: el naranja con texto blanco no alcanza el contraste mínimo, así que los botones naranjas llevan texto azul marino (6.9:1) y el texto naranja sobre blanco usa un tono más oscuro (`--naranja-texto`). Foco visible, etiquetas en todos los campos, `aria-*` en menús y filtros.
- **Responsive**: menú desplegable en celular (verificado en `17_inicio_movil.png`).
- **Sin recursos externos**: Poppins (`fuentes/poppins/`, licencia SIL OFL) y Font Awesome Free 6.5.2 (`vendor/fontawesome/`, verificado contra el hash SRI de cdnjs) se sirven desde el propio servidor. Por eso la CSP puede ser estricta: `default-src 'self'`, `script-src 'self'`, `style-src 'self'` (sin `unsafe-inline`).
- El pie aclara: "Proyecto académico… No es un canal oficial de la universidad".

## Páginas (25)

| Acceso | Páginas |
|---|---|
| Pública | `index.html`, `verificar-correo.html`, `restablecer-contrasena.html` |
| Solo sin sesión | `login.html`, `registro.html`, `recuperar-contrasena.html` |
| Estudiante | `panel-estudiante.html`, `buscar-objetos.html`, `detalle-objeto.html`, `reclamar-objeto.html`, `reportar-perdido.html`, `reportar-encontrado.html` (también editan con `?editar=id`), `mis-reportes.html`, `mis-reclamaciones.html` |
| Encargado | `panel-encargado.html`, `encargado-objetos.html`, `encargado-reclamaciones.html`, `encargado-reclamacion.html` (comparación a ciegas) |
| Encargado o admin | `oficina-objeto.html` (el encargado opera; el admin solo lee) |
| Administrador | `panel-admin.html`, `admin-usuarios.html`, `admin-catalogos.html`, `admin-objetos.html`, `admin-auditoria.html` |
| Cualquier sesión | `notificaciones.html` |

Cada página declara `<body data-acceso="…">`. `js/layout.js` consulta la sesión una sola vez, redirige si el rol no corresponde, arma el encabezado y el pie **del rol** y entrega el usuario a la página con la promesa `sesionLista`. Mientras tanto, el contenido de las páginas protegidas está oculto (sin parpadeo). **Es solo experiencia de usuario**: el backend vuelve a verificar todo (ver `docs/AUTHORIZATION.md`).

## JavaScript (`frontend/public/js/`)

```
api.js              fetch con cookies + CSRF en memoria (nunca localStorage); errores de red manejados
main.js             el(): construye el DOM con createElement/textContent; fechas en hora local;
                    insignias de estado; tarjetaObjeto(); paginación; esPaginaInterna()
sesion.js           obtenerSesion(), panelDeRol(), cerrarSesion()
layout.js           encabezado, menú por rol, campana de notificaciones, pie, control de acceso de la interfaz
validaciones.js     ayudas de validación de formularios (solo UX)
contrasena-fortaleza.js  medidor de fortaleza (solo UX)
pagina-*.js         uno por página (nunca <script> inline: la CSP lo bloquearía)
```

## Seguridad en el navegador

- **Nunca `innerHTML`** (ni `outerHTML`, `insertAdjacentHTML`, `document.write` o `eval`): todo texto que viene de la API se inserta como nodo de texto. Comprobado con un objeto llamado `<img src=x onerror=alert(1)>`, que se muestra literal y no ejecuta nada (verificación E2E).
- **Open redirect**: `?siguiente=` del login solo acepta páginas internas (`esPaginaInterna`); los enlaces de las notificaciones se validan igual (y la base de datos los restringe con un CHECK).
- **Tokens en la URL** (verificación y recuperación): se borran de la barra de direcciones al leerlos y esas páginas no envían `Referer`.
- **Código de retiro**: se muestra una sola vez en una ventana con aviso de no compartirlo; al cerrarla se borra del DOM.
- La CSP es tan estricta que bloqueó la función `wait_for_function` de Playwright (evalúa texto como JavaScript): prueba práctica de que la política impide `eval`.

## Comunicación con el backend

`API_BASE = '/api'` (mismo origen). `credentials: 'include'` en cada `fetch`. El token CSRF se pide una vez y se renueva automáticamente cuando login/logout devuelven uno nuevo. Los filtros de la búsqueda se reflejan en la URL (`?q=…&categoria_id=…`) como en el buscador de programas de la universidad.
