# Changelog de EncuentraU

## EncuentraU v0.25 — Rediseño visual basado en el logo + autenticación segura + backend Python Flask

### Cambio visual
- Nueva paleta de colores basada en el logo institucional (variables CSS en
  `frontend/public/css/styles.css`): azul marino `#0B172A` (institucional),
  rojo/borgoña `#C32734` (botones y acciones principales), naranja/dorado
  `#C57415` (acentos), gris `#353535` (texto secundario), blanco `#FFFFFF`
  (fondos y tarjetas).
- Referencia de estética institucional/organización visual tomada de la
  Fundación Universitaria San Mateo, sin copiar código ni contenido.

### Integración del logo
- Logo guardado en `frontend/public/img/logo-sanmateo.png`.
- Agregado en la barra de navegación de las 14 páginas existentes, en el
  hero de `index.html`, y en las tarjetas de login, registro, recuperación
  y restablecimiento de contraseña.

### Mejoras de login
- Botón mostrar/ocultar contraseña.
- Conectado al backend real (`POST /api/auth/login`) con manejo de errores
  sin revelar si el correo existe o no.

### Mejoras de registro
- Campos ampliados: primer nombre, segundo nombre (opcional), primer
  apellido, segundo apellido (opcional), correo, contraseña, confirmar
  contraseña.
- Checklist de requisitos de contraseña en tiempo real + medidor de
  fortaleza (Débil/Media/Fuerte) con los colores de la nueva identidad.
- Conectado al backend real (`POST /api/auth/registro`).

### Recuperación segura
- Nuevo flujo de 2 pasos: `recuperar-contrasena.html` (solicitar) y
  `restablecer-contrasena.html` (nueva página, usar el token y cambiar la
  contraseña).
- Mensaje genérico que no revela si un correo está registrado.
- Token generado con `secrets.token_urlsafe(32)`, expira en 30 minutos, de
  un solo uso.

### Política de contraseñas
- Mínimo 12 caracteres, mayúscula, minúscula, número, carácter especial,
  bloqueo de contraseñas comunes, y bloqueo si la contraseña contiene el
  correo o el nombre. Validado en frontend (ayuda visual) y backend
  (obligatorio).

### Migración a Python
- El backend Node.js/Express de la v0.1 fue **eliminado por completo**
  (`server.js`, `package.json`, `src/`). Python + Flask es ahora el único
  backend oficial del proyecto.

### Flask
- Nueva estructura en `backend/app/` con `routes/`, `controllers/`,
  `services/`, `models/`, `middlewares/`, `config/`.
- Endpoints: `POST /api/auth/registro`, `POST /api/auth/login`,
  `POST /api/auth/logout`, `GET /api/auth/sesion`,
  `POST /api/auth/recuperar`, `POST /api/auth/restablecer`,
  `GET /api/auth/csrf-token`.

### Nuevas dependencias (Python)
- `Flask`, `Flask-Limiter` (rate limiting), `Flask-WTF` (CSRF),
  `Flask-CORS`, `python-dotenv`. Ver `backend/requirements.txt`.

### Medidas de seguridad
- Hashing de contraseñas con `werkzeug.security`.
- Rate limiting en login, registro, recuperación y restablecimiento.
- Protección CSRF real con token (no simulada).
- Cookie de sesión `HttpOnly` + `SameSite=Lax` (+ `Secure` en producción).
- Mensajes de error genéricos, sin detalles internos.
- Ver `SECURITY.md` para el detalle completo, incluidas las limitaciones
  actuales.

### Archivos modificados
- `frontend/public/css/styles.css` (paleta nueva)
- `frontend/public/login.html`, `registro.html`, `recuperar-contrasena.html`
- `frontend/public/index.html` (logo en el hero)
- Las 14 páginas existentes (logo agregado a la barra de navegación)
- `.gitignore` (patrones de Python)
- `README.md`

### Archivos nuevos
- `frontend/public/restablecer-contrasena.html`
- `frontend/public/img/logo-sanmateo.png`
- `frontend/public/js/api.js`
- `frontend/public/js/contrasena-fortaleza.js`
- Todo `backend/` (estructura Flask completa)
- `SECURITY.md`
- `CHANGELOG.md`

### Archivos eliminados
- `backend/server.js`
- `backend/package.json`
- `backend/src/` (rutas, controladores, servicios, modelos, middlewares y
  config de la versión Node.js)

### No se avanzó a v0.3
Esta versión se detiene exactamente en lo solicitado: seguridad de
autenticación, rediseño visual y migración a Flask. No se implementó el
sistema completo de objetos, coincidencia automática, ni el panel
administrativo completo.
