# FRONTEND.md — Frontend de EncuentraU v1.0

HTML + CSS + JavaScript vanilla, sin framework ni build step. Servido por el propio backend Flask como estático (mismo origen que la API).

## Páginas (`frontend/public/*.html`)

| Página | Backend real | Auth requerida |
|---|---|---|
| `index.html` | — (estática) | No |
| `login.html`, `registro.html`, `recuperar-contrasena.html`, `restablecer-contrasena.html` | `/api/auth/*` | No |
| `panel-ciudadano.html` | `/api/auth/sesion` | Sí |
| `reportar-perdido.html`, `reportar-encontrado.html` | `POST /api/objetos` | Sí |
| `mis-reportes.html` | `/api/mis-reportes`, `DELETE /api/objetos/:id` | Sí |
| `buscar-objetos.html` | `GET /api/objetos` | No |
| `detalle-objeto.html` | `GET /api/objetos/:id`, `GET /api/objetos/:id/solicitudes` | No (Sí para ver solicitudes propias) |
| `solicitud-recuperacion.html` | `POST /api/solicitudes` | Sí |
| `panel-admin.html` | agregados de `/api/objetos`, `/api/admin/*` | Sí + admin |
| `gestion-reportes.html` | `/api/admin/objetos`, `PUT /api/admin/objetos/:id/estado` | Sí + admin |
| `gestion-solicitudes.html` (nueva en v1.0) | `/api/admin/solicitudes`, `PUT /api/admin/solicitudes/:id` | Sí + admin |
| `gestion-usuarios.html` | `/api/admin/usuarios`, `PUT /api/admin/usuarios/:id` | Sí + admin |

Todas las páginas protegidas llaman `protegerPagina()` / `protegerPagina({admin:true})` al cargar (`js/sesion.js`), que redirige si no hay sesión válida o rol suficiente. **Esto es solo experiencia de usuario** — el backend es quien realmente decide qué se permite (ver `docs/AUTHORIZATION.md`).

## JavaScript (`frontend/public/js/`)

```
api.js              → fetch con cookies + CSRF. peticionGet(), peticionProtegida(ruta, metodo, cuerpo).
sesion.js            → obtenerSesion(), protegerPagina(), logout real (conectarCerrarSesion).
main.js              → resaltado de nav activo, claseBadgeEstado(), textoEstado(),
                        crearElemento()/crearBadge() — construcción de DOM SIN innerHTML.
validaciones.js       → helpers de validación de formularios (solo UX).
contrasena-fortaleza.js → medidor visual de fortaleza de contraseña (solo UX).
pagina-*.js          → un archivo por página con su lógica específica (nunca inline).
```

### Por qué no hay `<script>` inline

El backend envía `Content-Security-Policy: script-src 'self'` (ver `docs/SECURITY.md`), que bloquea cualquier JavaScript embebido directamente en el HTML. Por eso cada página tiene su lógica en un archivo `js/pagina-*.js` separado, cargado con `<script src="...">`. Esto se verificó funcionando de extremo a extremo con un navegador real (Playwright) — si algún script inline hubiera quedado, esa página habría fallado silenciosamente.

### Por qué no se usa `innerHTML` con datos de la API

Los datos que vienen de la API (nombre de un reporte, mensaje de una solicitud, nombre de un usuario) son **texto ingresado por otros usuarios** y pueden contener HTML/JavaScript malicioso (confirmado en las pruebas de XSS, `docs/evidencia/`). El backend los guarda tal cual (no es su responsabilidad escapar HTML, solo persistir el dato); la responsabilidad de no ejecutarlos es del frontend al mostrarlos. Por eso `main.js` expone `crearElemento(etiqueta, texto, clase)` y `crearBadge(texto, clase)`, que usan siempre `textContent`, nunca `innerHTML`, y todas las páginas reescritas en v1.0 los usan en vez de plantillas de texto interpoladas.

## Comunicación con el backend

- `API_BASE = '/api'` (ruta relativa: mismo origen, sin CORS en producción).
- Cookies de sesión: `credentials: 'include'` en cada `fetch`.
- CSRF: `peticionProtegida()` obtiene el token una vez (`GET /api/auth/csrf-token`) y lo cachea en una variable de JS en memoria (nunca en `localStorage`/`sessionStorage`); lo renueva automáticamente si una respuesta de login/logout trae uno nuevo (ver `docs/AUTHENTICATION.md`).

## Identidad visual

Se conserva íntegra de v0.25: paleta de colores institucional, logo, estructura de páginas (`frontend/public/css/styles.css`, sin cambios). v1.0 solo reemplaza la fuente de los datos (de simulados a reales), no el diseño.
