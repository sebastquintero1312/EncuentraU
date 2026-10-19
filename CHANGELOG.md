# Changelog de EncuentraU

## Preparación del despliegue v2.0 (Supabase + Render + Brevo)

- `render.yaml` reescrito para v2.0: se quita la base de datos de Render
  (vencía a los 30 días; ahora es Supabase), la migración ya no corre al
  arrancar (el usuario de la app no puede crear tablas), Gunicorn con 1
  proceso y 4 hilos (límites de peticiones exactos) y variables de v2.0
  (`NUM_PROXIES`, Brevo, `URL_PUBLICA`), con los secretos en `sync: false`.
- Se elimina el `Procfile` (de v1.0; Render usa `render.yaml`).
- Nuevo `database/scripts/crear_usuario_app_supabase.sql` para crear
  `encuentrau_app` en Supabase.
- Desplegado en https://encuentrau.onrender.com (Render, rama `despliegue-v2`)
  con la base en Supabase. Verificado: migración, permisos mínimos, RLS,
  `/health`, HTTPS/HSTS/CSP y cookie `Secure`. Pendiente: correo real de
  Brevo, primer administrador y secretos de respaldo (ver docs/DEPLOYMENT.md).
- Corrección: la verificación de correo y el restablecimiento de contraseña
  fallaban en producción ("The referrer header is missing"): las páginas
  usaban `no-referrer` y Flask-WTF exige el Referer en HTTPS. Ahora usan
  `same-origin` (el token se borra de la URL antes del POST).
- `User-Agent` explícito en las peticiones a Brevo (Cloudflare bloqueó el de
  Python por defecto en una prueba).

## EncuentraU v2.0 — PostgreSQL, tres roles, reclamación segura y rediseño

Cambio mayor (rompe compatibilidad con v1.0: nuevos roles, nueva API, nuevo
esquema). No se migraron datos: no había datos reales que conservar. Informe
completo en `docs/VERSION_2.0.md`.

### Base de datos (reescrita)
- PostgreSQL en desarrollo, pruebas y producción; SQLite eliminado. La app no
  arranca sin PostgreSQL.
- Esquema en SQL legible (`backend/migrations/sql/`), aplicado por una única
  migración transaccional `0001_esquema_v2`. Se eliminó la migración de v1.0.
- Normalización a 3FN: catálogos `roles`, `estados_objeto`,
  `transiciones_objeto`, `estados_solicitud`, `parametros`, `categorias`,
  `ubicaciones`; tablas nuevas `entregas`, `notificaciones`, `auditoria`;
  `tokens_recuperacion` pasa a `tokens_usuario` (solo hashes).
- Triggers: máquina de estados, reglas contra el abuso de reclamaciones,
  marcado de cuentas por rechazos, `updated_at`, auditoría de 8 tablas y
  auditoría inmutable.
- Procedimientos almacenados para recepción, pre-aprobación, rechazo, entrega
  y cierre, con bloqueo de filas en orden fijo (ACID y concurrencia).
- Concurrencia optimista con columna `version`.
- Índices: FK, compuestos, parciales, únicos parciales, sobre expresión, GIN
  de trigramas y BRIN.
- Vistas de estadísticas e integración.
- Dos usuarios de BD (dueño y aplicación con permisos mínimos y por columna),
  Row Level Security y endurecimiento para Supabase.
- Respaldo y restauración (`database/scripts/respaldo.py`, `restaurar.py`),
  respaldo diario cifrado en GitHub Actions, usuario lector para BI.

### Roles y reclamaciones
- Roles `estudiante`, `encargado`, `administrador` (antes `ciudadano` y
  `administrador`) con funciones separadas.
- Nuevo proceso: el objeto encontrado se publica solo cuando la oficina lo
  recibe; reclamación a ciegas; pre-aprobación; código de retiro de un solo
  uso (HMAC, 5 intentos, 72 h); entrega presencial con carné y prueba; acta de
  entrega; límites de reclamaciones; cuentas en revisión tras 3 rechazos.
- Los administradores solo se crean con `flask crear-admin` (requiere correo
  verificado). Nuevos comandos `flask verificar-correo` y `flask vencer-reservas`.

### Cuentas y correo
- Registro solo con correo `@sanmateo.edu.co` y verificación por enlace.
- Registro, reenvío y recuperación sin enumeración de cuentas.
- Envío de correos (consola en desarrollo, Brevo por API HTTPS en producción)
  y notificaciones dentro de la aplicación.

### Frontend (rediseño completo)
- Estilo del sitio de la universidad (Poppins, naranja, azul marino), con
  fuentes e íconos servidos localmente y contraste AA.
- 25 páginas: paneles y pantallas propias para cada rol, comparación a ciegas,
  código de retiro, auditoría, catálogos, notificaciones.
- `js/layout.js` arma encabezado, menú y pie por rol; DOM construido sin
  `innerHTML`; CSP sin `unsafe-inline`.
- Eliminadas: `panel-ciudadano`, `gestion-reportes`, `gestion-solicitudes`,
  `gestion-usuarios`, `solicitud-recuperacion` (reemplazadas por las nuevas).

### Seguridad
- `ProxyFix` configurable (IP real detrás de Render) para límites y auditoría.
- `Cache-Control: no-store` en la API.
- Guardrails de producción: Brevo y `URL_PUBLICA` https obligatorios.
- Eliminado el campo `imagen_url`.

### Bugs corregidos
1. **Debug activado por defecto** (heredado de v1.0): `app.py` activaba el
   debugger interactivo si `FLASK_ENV` no estaba definida. Ahora solo con
   `FLASK_ENV=development` explícito.
2. `generar_codigo_retiro` se tapaba a sí misma (nombre repetido con la
   utilidad importada). Detectado por pytest antes de publicarse.

### Pruebas y documentación
- Suite reescrita sobre PostgreSQL real, con la app conectada como el usuario
  de permisos mínimos; incluye pruebas de esquema, permisos, RLS, índices,
  concurrencia con dos conexiones reales, configuración y una prueba que
  compara `docs/API.md` con las rutas reales.
- Verificación E2E reescrita para los tres roles con Microsoft Edge y
  capturas en `docs/evidencia/capturas_v2/`.
- Documentación actualizada: API, base de datos, autenticación, autorización,
  arquitectura, backend, frontend, pruebas, despliegue, matriz OWASP,
  diagramas y las 100 reglas.

### Pendiente
- Despliegue con Supabase + Render + Brevo (ver `docs/DEPLOYMENT.md`).

---

## EncuentraU v1.0 — Base de datos real, núcleo funcional completo y seguridad verificada

Migración completa de v0.25 (autenticación real en memoria + resto simulado) a un
sistema con backend, base de datos y frontend genuinamente integrados. Ver
`docs/VERSION_1.0.md` para el informe de cierre completo.

### Auditoría previa (Fase 0)
- `docs/ESTADO_V025.md`: auditoría honesta del estado real de v0.25 antes de
  tocar cualquier código. Encontró que solo autenticación era real; el resto
  del "núcleo funcional" (objetos perdidos/encontrados) era 100% simulado en
  `datos-temporales.js`; `docs/REGLAS_100.md` solo tenía 50 de 100 reglas;
  `ARCHITECTURE.md` describía un stack Node.js ya eliminado.
- Punto de restauración creado con `git init` + commit inicial antes de
  cualquier modificación.

### Base de datos (nuevo)
- SQLAlchemy + Flask-Migrate/Alembic. SQLite en desarrollo, PostgreSQL en
  producción vía `DATABASE_URL`.
- 4 tablas: `usuarios`, `tokens_recuperacion` (migradas de listas en memoria
  a modelos reales), `objetos` y `solicitudes` (nuevas).
- Claves foráneas reales, `CheckConstraint` a nivel de BD para campos de
  valores fijos, migración inicial generada y aplicada realmente.

### Backend — núcleo funcional (nuevo, no existía en v0.25)
- Endpoints completos de objetos (CRUD, búsqueda con filtros y paginación,
  transiciones de estado validadas), solicitudes de reclamación (con
  verificación humana obligatoria, nunca automática) y administración
  (usuarios, reportes, solicitudes). Ver `docs/API.md`.
- Motor de coincidencias: sugiere posibles pares perdido/encontrado por
  categoría, ubicación, fecha y palabras en común — nunca transfiere
  propiedad automáticamente.
- Autorización real: decoradores `login_requerido`/`admin_requerido` que
  releen el rol desde la BD; verificación de ownership (IDOR) en cada
  modificación; whitelist explícita contra mass assignment; un admin no
  puede modificar su propia cuenta desde el panel.
- CLI `flask crear-admin` para promover administradores sin exponer ningún
  mecanismo de autopromoción por HTTP.

### Autenticación — cambios
- Hashing de contraseñas migrado de `scrypt` (Werkzeug) a **Argon2id**.
- Modo debug de Flask cambiado a deny-by-default (antes: activo salvo
  `FLASK_ENV=production` explícito; ahora: activo solo si
  `FLASK_ENV=development` explícito).
- Guardrail que impide arrancar en producción con `SECRET_KEY` insegura o
  sin `DATABASE_URL`.

### Bugs reales encontrados y corregidos (con evidencia de ejecución)
1. **CSRF invalidado tras login/logout**: `session.clear()` borraba también
   el `csrf_token` de la sesión; cualquier petición protegida inmediatamente
   después de iniciar sesión fallaba. Corregido: login/logout devuelven un
   token nuevo, el frontend lo actualiza automáticamente.
2. **CSRFError devolvía 500 en vez de 400**: el manejador genérico de
   `Exception` interceptaba cualquier `HTTPException` sin handler
   específico. Bug ya presente en v0.25, nunca detectado por falta de
   pruebas. Corregido con un manejador para `HTTPException`.
3. **`recuperacion_service.py` trataba el modelo migrado a SQLAlchemy como
   diccionario** (`registro['usuario_id']`), causando un 500 en cualquier
   restablecimiento de contraseña. Detectado por pytest, corregido a
   `registro.usuario_id`.
4. **Sin límite de tamaño de petición**: Flask no tenía `MAX_CONTENT_LENGTH`
   configurado, aceptando cuerpos de tamaño ilimitado. Corregido: 1 MB.
5. **El aislamiento de la suite de pruebas no funcionaba de verdad**
   (encontrado en la revisión final independiente antes de declarar v1.0):
   `app.config['SQLALCHEMY_DATABASE_URI'] = ...` aplicado después de
   `create_app()` no tenía ningún efecto, porque Flask-SQLAlchemy fija el
   engine dentro de `db.init_app()`. Las 88 pruebas "aisladas" en realidad
   corrían todas contra `backend/instance/encuentrau_dev.db`, la misma
   base de datos de desarrollo manual — funcionaba solo por casualidad de
   orden de ejecución secuencial. Corregido con un parámetro
   `config_overrides` en `create_app()`, aplicado antes de inicializar las
   extensiones; se agregó también `tests/integration/test_esquema_migraciones.py`
   para detectar a futuro cualquier desincronización entre modelos y
   migraciones de Alembic.

### Frontend — conectado por completo (eliminada la simulación)
- `js/datos-temporales.js` eliminado. Las 9 páginas que dependían de él
  (buscar, detalle, mis-reportes, paneles, gestión de reportes/usuarios,
  solicitud de recuperación) ahora usan la API real.
- `reportar-perdido.html`/`reportar-encontrado.html` ahora persisten de
  verdad (antes: ni siquiera fingían guardar nada).
- Página nueva `gestion-solicitudes.html`: panel de aprobación/rechazo de
  reclamaciones (el backend ya tenía los endpoints, ninguna página los
  consumía).
- Todos los `<script>` inline se movieron a archivos `js/pagina-*.js`
  externos, para poder aplicar una Content-Security-Policy sin
  `unsafe-inline` en `script-src`.
- `main.js`: nuevas utilidades `crearElemento`/`crearBadge` que usan
  `textContent` (nunca `innerHTML`) para construir la interfaz a partir de
  datos de la API — previene XSS DOM con contenido generado por usuarios.
- Frontend y backend se sirven desde el mismo origen (Flask sirve
  `frontend/public` como estático); `API_BASE` pasó de una URL absoluta
  (`http://127.0.0.1:5000/api`) a una ruta relativa (`/api`).

### Seguridad — nuevo en v1.0
- Cabeceras: Content-Security-Policy, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy, Permissions-Policy,
  Strict-Transport-Security (producción).
- `/health` mínimo, sin información interna.
- Ver `docs/MATRIZ_SEGURIDAD.md` (revisión OWASP Top 10) y
  `docs/REGLAS_100.md` (100 reglas, ahora completas, con evidencia real).

### Pruebas — nuevo en v1.0 (v0.25 no tenía ninguna)
- 89 pruebas de pytest (unitarias, integración, seguridad), con aislamiento
  de base de datos confirmado real tras el bug #5 de arriba.
- Verificación de extremo a extremo con navegador real (Playwright +
  Chromium): registro, login, reportar, buscar, coincidencias, solicitud,
  panel admin, gestión de reportes/solicitudes/usuarios, logout real.
- Evidencia de todas las ejecuciones guardada en `docs/evidencia/`.

### Documentación
- `docs/ESTADO_V025.md`, `docs/ARQUITECTURA.md` (nuevos — reemplazan al
  `ARCHITECTURE.md` desactualizado de la raíz, que ahora solo redirige),
  `docs/API.md`, `docs/BACKEND.md`, `docs/FRONTEND.md`, `docs/DATABASE.md`,
  `docs/AUTHENTICATION.md`, `docs/AUTHORIZATION.md`, `docs/TESTING.md`,
  `docs/MATRIZ_SEGURIDAD.md`, `docs/DEPLOYMENT.md`, `docs/VERSION_1.0.md`.
- `README.md` y `SECURITY.md` actualizados para reflejar v1.0.
- `docs/REGLAS_100.md` completado (RU-051 a RU-100 agregadas) y con estado
  real evaluado para las 100 reglas.

### Qué falta (ver docs/VERSION_1.0.md y docs/DEPLOYMENT.md)
- Despliegue real en producción con HTTPS, PostgreSQL y URL pública:
  preparado por completo (Procfile, configuración, guardrails), pero
  bloqueado por requerir una cuenta de un proveedor de hosting y un
  repositorio en GitHub que solo su propietario puede autorizar.
- Envío real de correos electrónicos.

---

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
