---
name: autenticacion
description: Guía para implementar y revisar el sistema de autenticación de EncuentraU: registro, login, logout, sesiones y recuperación.
---

# SKILL: Autenticación

## 1. Propósito

Guiar la implementación y revisión del sistema de autenticación de EncuentraU. La autenticación es crítica para la seguridad: un error aquí compromete todo el sistema.

## 2. Cuándo utilizarla

- Al revisar o modificar el registro de usuarios.
- Al revisar o modificar el login/logout.
- Al implementar recuperación de contraseña.
- Al cambiar el algoritmo de hashing.
- Al revisar la gestión de sesiones.
- Al agregar verificación de correo.

## 3. Qué debe cubrir

### Registro
- [ ] Validación completa de campos (nombre, correo, contraseña)
- [ ] Verificación de correo único
- [ ] Política de contraseñas aplicada en el backend
- [ ] Contraseña hasheada antes de guardar (NUNCA texto plano)
- [ ] Mensaje de error no revela si el correo ya existe (en algunos contextos)
- [ ] Rol inicial siempre 'estudiante' (nunca confiar en el cliente para el rol)
- [ ] Solo correos del dominio institucional, y la cuenta no se usa hasta verificar el correo

### Login
- [ ] Verificación de correo y contraseña
- [ ] Mensaje genérico cuando fallan (no revelar si el correo existe)
- [ ] Rate limiting activo
- [ ] `session.clear()` antes de guardar la nueva sesión
- [ ] No guardar datos sensibles en la sesión

### Logout
- [ ] `session.clear()` completo
- [ ] Respuesta correcta al cliente
- [ ] CSRF protegido

### Sesiones
- [ ] Cookie con `HttpOnly=True`
- [ ] Cookie con `SameSite=Lax` o `Strict`
- [ ] Cookie con `Secure=True` en producción
- [ ] `SECRET_KEY` segura y en variable de entorno
- [ ] No guardar datos sensibles en la sesión

### Recuperación de contraseña
- [ ] Token generado con `secrets.token_urlsafe()` (no random, no UUID predecible)
- [ ] Token con tiempo de expiración (30 minutos)
- [ ] Token de un solo uso (marcado como usado al utilizarse)
- [ ] Respuesta genérica (no confirmar si el correo existe)
- [ ] Rate limiting en el endpoint de recuperación
- [ ] Envío real de correo (PENDIENTE en v0.25)

### Cambio de contraseña
- [ ] Verificar contraseña actual antes de cambiar
- [ ] Aplicar política de contraseñas a la nueva
- [ ] Invalidar sesiones activas después del cambio
- [ ] Rate limiting

### Verificación de correo
- [ ] Token de verificación generado al registrar
- [ ] Cuenta no activa hasta verificar
- [ ] Re-envío de verificación disponible
- [ ] (PENDIENTE en v0.25)

### Hashing
- [ ] Algoritmo: Argon2id (preferido) o scrypt (actual en v0.25)
- [ ] NUNCA MD5, SHA1, SHA256 sin sal para contraseñas
- [ ] NUNCA texto plano
- [ ] Parámetros de costo adecuados

## 4. Política de contraseñas (implementada en v0.25)

- Mínimo 12 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula
- Al menos 1 número
- Al menos 1 carácter especial (! @ # $ % ^ & * ( ) _ - + =)
- No debe contener contraseñas comunes
- No debe contener el correo o nombre del usuario

## 5. Reglas obligatorias

1. La contraseña NUNCA se guarda en texto plano. Sin excepciones.
2. La contraseña NUNCA se incluye en logs o respuestas de API.
3. Los mensajes de error de login son siempre genéricos.
4. Los tokens de recuperación usan `secrets` (no `random`).
5. `session.clear()` antes de establecer una nueva sesión.
6. El rol del usuario viene de la base de datos, nunca del cliente.
7. Rate limiting activo en todos los endpoints de autenticación.

## 6. Endpoints de autenticación actuales (v0.25)

| Método | Ruta | Descripción | Rate Limit |
|--------|------|-------------|-----------|
| GET | /api/auth/csrf-token | Obtener token CSRF | — |
| POST | /api/auth/registro | Registrar usuario | 5/min |
| POST | /api/auth/login | Iniciar sesión | 10/min |
| POST | /api/auth/logout | Cerrar sesión | — |
| GET | /api/auth/sesion | Verificar sesión actual | — |
| POST | /api/auth/recuperar | Solicitar recuperación | 5/min |
| POST | /api/auth/restablecer | Restablecer contraseña | 5/min |

## 7. Checklist de autenticación completa

- [ ] Registro valida todos los campos en el backend
- [ ] Registro no revela si el correo ya existe (considerar contexto)
- [ ] Login usa mensaje genérico de error
- [ ] Login tiene rate limiting
- [ ] Contraseñas hasheadas con algoritmo seguro
- [ ] Sesión usa cookie HttpOnly + SameSite + Secure(producción)
- [ ] Tokens de recuperación usan secrets.token_urlsafe()
- [ ] Tokens de recuperación expiran
- [ ] Tokens de recuperación son de un solo uso
- [ ] Rate limiting en recuperación

## 8. Criterios de finalización

La autenticación está completa cuando:
- Todos los flujos funcionan (registro, login, logout, recuperación).
- Los tests de autenticación pasan.
- Las contraseñas están hasheadas con Argon2id.
- Las cookies tienen las configuraciones de seguridad correctas.
- Los tokens de recuperación son seguros y tienen expiración.

## 9. Errores que debe evitar

- Usar MD5/SHA1 para contraseñas.
- Guardar contraseñas o tokens en logs.
- Usar `random.token_hex()` (no es criptográficamente seguro para tokens de seguridad).
- Revelar en el login si el correo existe.
- Olvidar `session.clear()` antes de autenticar.
- Confiar en el rol que envía el cliente.

## 10. Documentación que debe actualizar

- `docs/AUTHENTICATION.md` — al cambiar flujos de autenticación.
- `docs/API.md` — al cambiar endpoints.
- `docs/SECURITY.md` — al cambiar políticas de seguridad.
