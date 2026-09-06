# Seguridad de EncuentraU

Versión: **v0.25**

Este documento explica, con honestidad, qué medidas de seguridad están
implementadas en esta versión, cómo funcionan, y qué limitaciones tienen
todavía (para no dar una falsa sensación de que todo está resuelto).

## 1. Política de contraseñas

Se exige, tanto en el frontend (visual) como en el backend (obligatorio):

- Mínimo 12 caracteres.
- Al menos una mayúscula, una minúscula, un número y un carácter especial
  (`! @ # $ % ^ & * ( ) _ - + =`).
- No se permite una lista de contraseñas comunes (`12345678`, `password`,
  `qwerty`, `admin123`, etc. — ver `backend/app/services/auth_service.py`).
- No se permite que la contraseña contenga el correo o el nombre de la
  persona.

**El frontend solo ayuda visualmente** (checklist en tiempo real + barra de
fortaleza). La regla que de verdad se aplica es la del backend
(`validar_contrasena` en `auth_service.py`), porque nunca se debe confiar en
lo que llega del navegador.

## 2. Hashing de contraseñas

Las contraseñas se cifran con `werkzeug.security.generate_password_hash`
(usa el algoritmo `scrypt` por defecto en Werkzeug moderno). Nunca se
guardan en texto plano, nunca se devuelven por la API, y nunca se escriben
en logs.

## 3. Recuperación de contraseña

Flujo implementado:

1. El usuario pide recuperación con su correo (`POST /api/auth/recuperar`).
2. El backend **siempre responde el mismo mensaje genérico**
   ("Si el correo está registrado, recibirás instrucciones para continuar."),
   exista o no el correo, para evitar que alguien pueda enumerar qué correos
   están registrados.
3. Si el correo sí existe, se genera un token con `secrets.token_urlsafe(32)`
   (generador criptográficamente seguro, no `random`, no IDs secuenciales).
4. El token expira a los **30 minutos** (`Config.MINUTOS_EXPIRACION_TOKEN`).
5. El usuario usa el token en `restablecer-contrasena.html`, que llama a
   `POST /api/auth/restablecer`.
6. Al usarse (con éxito o no), el token queda marcado como `usado` y no puede
   reutilizarse.

**Limitación honesta**: todavía no hay envío real de correos. El token se
imprime en la consola del servidor Flask para poder probar el flujo
completo sin depender de un servicio de correo (eso queda para una fase
posterior).

## 4. Rate limiting (Flask-Limiter)

Límites aplicados por IP:

- `POST /api/auth/login`: 10 intentos por minuto.
- `POST /api/auth/registro`: 5 por minuto.
- `POST /api/auth/recuperar`: 5 por minuto.
- `POST /api/auth/restablecer`: 5 por minuto.

Son límites moderados a propósito, para no entorpecer las pruebas del
equipo, pero sí frenar intentos automatizados de fuerza bruta.

**Limitación honesta**: no se pudo instalar `Flask-Limiter` en este entorno
de desarrollo (sin acceso a internet para `pip install`), así que el código
está escrito y lógicamente correcto, pero no se ejecutó de punta a punta
aquí. Ver `CHANGELOG.md` para más detalle sobre qué se probó y qué no.

## 5. Sesión

- Se usa la sesión de Flask (cookie firmada con `SECRET_KEY`).
- La cookie se configura con `HttpOnly` (JavaScript no puede leerla),
  `SameSite=Lax` (protección básica contra CSRF) y `Secure` activado
  automáticamente cuando `FLASK_ENV=production` (en desarrollo por HTTP no
  aplica).
- No se guarda ningún dato sensible en `localStorage` ni `sessionStorage`.

## 6. CSRF

Se usa `Flask-WTF` (`CSRFProtect`) de forma real, no simulada:

1. El frontend pide un token en `GET /api/auth/csrf-token`.
2. Lo reenvía en el header `X-CSRFToken` en cada petición que cambia datos
   (login, registro, recuperación, restablecimiento).
3. Flask-WTF valida ese token contra la sesión antes de procesar la
   petición.

## 7. Validación en el backend

Cada dato que llega del frontend se vuelve a validar en Python: campos
obligatorios, formato de correo, coincidencia de contraseñas, y la política
de contraseñas completa. El frontend nunca es la única barrera.

## 8. Mensajes de error

Los errores nunca exponen detalles internos (sin stack traces, sin
consultas, sin nombres de variables). Ver
`backend/app/middlewares/manejo_errores.py`.

## 9. Lo que NO se implementó todavía (a propósito)

- Envío real de correos para la recuperación.
- Conexión a una base de datos real (los usuarios viven en memoria en
  `backend/app/models/usuario.py`; se pierden al reiniciar el servidor).
  Esto es intencional en esta fase: el objetivo era dejar la seguridad del
  flujo de autenticación bien resuelta antes de conectar la base de datos
  definitiva.
- Verificación de correo institucional (dominio específico de la
  universidad).
- Confirmación de cuenta por correo antes de poder iniciar sesión.
