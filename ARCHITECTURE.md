# Arquitectura de EncuentraU

Versión: **v0.2 — Frontend funcional**
(construida sobre la v0.1 — Arquitectura inicial, sin eliminar nada de ella)

## 1. Objetivo del proyecto

EncuentraU es una plataforma universitaria para gestionar objetos perdidos y
encontrados. Permite a los usuarios reportar objetos perdidos o encontrados,
consultar reportes existentes y realizar solicitudes relacionadas con la
recuperación de un objeto.

## 2. Roles

- **Ciudadano**: reporta objetos perdidos/encontrados, consulta reportes y
  realiza solicitudes de recuperación.
- **Administrador**: gestiona reportes, usuarios y solicitudes.

## 3. Tecnologías

| Capa | Tecnología | Motivo |
|---|---|---|
| Frontend | HTML, CSS, JavaScript | Simple, sin curva de aprendizaje adicional, fácil de modificar |
| Backend | Node.js + Express | Estructura sencilla de rutas/controladores, ampliamente documentado |
| Base de datos | MySQL | Relacional, se ajusta bien a usuarios, reportes, objetos y solicitudes |
| Seguridad | bcrypt, jsonwebtoken, express-validator, helmet, dotenv | Cubren cifrado de contraseñas, autenticación, validación y buenas prácticas |

## 4. Estructura de carpetas

```
EncuentraU/
├── frontend/
│   └── public/
│       ├── index.html
│       ├── css/styles.css
│       └── js/main.js
├── backend/
│   ├── server.js
│   ├── src/
│   │   ├── app.js
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── models/
│   │   ├── middlewares/
│   │   └── config/
│   └── .env.example
├── database/
│   └── scripts/
├── ARCHITECTURE.md
└── README.md
```

## 5. Responsabilidad de cada parte

- **frontend/**: interfaz de usuario. Se comunicará con el backend mediante
  peticiones HTTP (API REST). No tiene acceso directo a la base de datos.
- **backend/routes/**: define los endpoints disponibles (URLs).
- **backend/controllers/**: recibe la petición HTTP y decide qué hacer,
  delega la lógica al servicio correspondiente.
- **backend/services/**: contiene la lógica de negocio (reglas del sistema).
- **backend/models/**: representa las tablas de la base de datos y las
  consultas relacionadas.
- **backend/middlewares/**: funciones intermedias, por ejemplo validar datos
  de entrada o verificar autenticación (se implementarán en fases futuras).
- **backend/config/**: configuración general, incluida la futura conexión a
  la base de datos.
- **database/scripts/**: scripts SQL para crear las tablas del sistema
  (usuarios, objetos, reportes, estados, solicitudes).

## 6. Flujo general del sistema (a futuro)

1. El usuario interactúa con el frontend (por ejemplo, reporta un objeto perdido).
2. El frontend envía una petición HTTP al backend.
3. La ruta correspondiente recibe la petición y la pasa al controlador.
4. El controlador llama al servicio, que aplica las reglas de negocio.
5. El servicio usa el modelo para consultar o modificar la base de datos.
6. La respuesta regresa al frontend y se muestra al usuario.

## 7. Consideraciones iniciales de seguridad

Contempladas desde la arquitectura (se implementarán en fases posteriores):

- Validación de entradas con `express-validator`.
- Contraseñas cifradas con `bcrypt` (nunca en texto plano).
- Autenticación con `jsonwebtoken`.
- Autorización según el rol (ciudadano / administrador).
- Cabeceras de seguridad básicas con `helmet`.
- Uso de `mysql2` con consultas parametrizadas para evitar SQL Injection.
- Variables sensibles (contraseñas, claves) solo en `.env`, nunca en el código.
- Manejo centralizado de errores para no exponer información sensible.

## 7.1 Frontend construido en v0.2

Se crearon 14 páginas HTML dentro de `frontend/public/`, todas usando la
misma hoja de estilos (`css/styles.css`) para mantener una identidad visual
coherente:

- **Públicas**: `index.html`, `login.html`, `registro.html`, `recuperar-contrasena.html`
- **Ciudadano**: `panel-ciudadano.html`, `reportar-perdido.html`, `reportar-encontrado.html`, `mis-reportes.html`, `buscar-objetos.html`, `detalle-objeto.html`, `solicitud-recuperacion.html`
- **Administrador**: `panel-admin.html`, `gestion-reportes.html`, `gestion-usuarios.html`

**Datos temporales**: `js/datos-temporales.js` contiene usuarios, reportes y
solicitudes simulados, solo para poder visualizar la interfaz. No hay
ninguna base de datos conectada; los datos viven en memoria del navegador y
se pierden al recargar.

**Validaciones**: `js/validaciones.js` tiene funciones de validación básica
(campos vacíos, formato de correo, longitud de texto). Esto es solo
experiencia de usuario, no seguridad real.

## 8. Qué se desarrollará en las siguientes fases

- **Fase 1**: modelo de datos y scripts de base de datos (tablas: usuarios,
  objetos, reportes, estados, solicitudes).
- **Fase 2**: autenticación y autorización por roles.
- **Fase 3**: endpoints y lógica de reportes de objetos.
- **Fase 4**: endpoints y lógica de solicitudes de recuperación.
- **Fase 5**: páginas de frontend (login, registro, inicio, reportes, paneles).
- **Fase 6**: panel de administrador (gestión de usuarios, reportes y solicitudes).
- **Fase 7**: pruebas y ajustes de seguridad finales.
