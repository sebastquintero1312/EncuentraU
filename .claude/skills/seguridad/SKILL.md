---
name: seguridad
description: Skill principal de seguridad para EncuentraU. Contiene procedimientos para revisar, implementar y verificar seguridad en todos los componentes del sistema.
---

# SKILL: Seguridad

## 1. Propósito

Esta es una de las Skills MÁS IMPORTANTES del proyecto. Guía la revisión, implementación y verificación de seguridad en todos los componentes de EncuentraU. La seguridad no es un módulo: es un requisito transversal.

## 2. Cuándo utilizarla

- Antes de declarar cualquier funcionalidad como VERIFICADA.
- Al revisar código de autenticación o autorización.
- Al diseñar nuevos endpoints.
- Al revisar manejo de entradas del usuario.
- Al preparar el proyecto para producción.
- En cualquier decisión que afecte datos de usuarios.

## 3. Principios fundamentales

### DENY BY DEFAULT
Comenzar con todo prohibido. Abrir solo lo que se necesita explícitamente.

### DEFENSE IN DEPTH
Múltiples capas de seguridad. Si una falla, la siguiente detiene el ataque.

### LEAST PRIVILEGE
Cada componente accede solo a lo que necesita para su función.

### ZERO TRUST EN ENTRADAS DEL CLIENTE
Toda entrada del cliente es potencialmente maliciosa hasta que se valide.
No importa si viene del frontend "propio". Validar siempre en el backend.

## 4. Categorías de revisión

### SQL Injection
- [ ] ¿Se usan consultas parametrizadas? (SQLAlchemy previene automáticamente)
- [ ] ¿No hay concatenación de strings en consultas SQL?
- [ ] ¿No hay SQL crudo (raw SQL) sin parámetros?

### Cross-Site Scripting (XSS)
- [ ] ¿El HTML generado escapa correctamente los datos del usuario?
- [ ] ¿No se insertan datos no escapados en el DOM?
- [ ] ¿No se usa innerHTML con datos del servidor?
- [ ] ¿Hay Content-Security-Policy configurado?

### CSRF (Cross-Site Request Forgery)
- [ ] ¿Flask-WTF CSRFProtect está activo?
- [ ] ¿El frontend obtiene y envía el CSRF token?
- [ ] ¿Las peticiones que modifican datos envían X-CSRFToken?
- [ ] ¿La cookie tiene SameSite=Lax o Strict?

### IDOR / BOLA (Broken Object Level Authorization)
- [ ] Al acceder a un objeto por ID, ¿se verifica que pertenece al usuario?
- [ ] ¿Un usuario puede acceder a objetos de otro cambiando el ID?
- [ ] ¿Los IDs numéricos secuenciales están protegidos?

### Broken Access Control
- [ ] ¿Cada endpoint de admin verifica el rol?
- [ ] ¿Los endpoints protegidos verifican autenticación?
- [ ] ¿Existe algún endpoint sin protección que debería tenerla?

### Mass Assignment
- [ ] ¿Se filtran los campos que el usuario puede enviar?
- [ ] ¿Un usuario puede cambiar su propio rol enviando rol='administrador'?
- [ ] ¿Los campos permitidos están en una whitelist?

### Authentication Failures
- [ ] ¿Los mensajes de error de login son genéricos?
- [ ] ¿Hay rate limiting en login/registro/recuperación?
- [ ] ¿Las contraseñas se hashean correctamente?
- [ ] ¿Los tokens de recuperación son seguros y expiran?

### Session Fixation
- [ ] ¿Se llama session.clear() antes de iniciar sesión?
- [ ] ¿La cookie de sesión se regenera en cada login?

### Brute Force
- [ ] ¿Hay rate limiting en login?
- [ ] ¿Hay rate limiting en registro?
- [ ] ¿Hay rate limiting en recuperación?

### Rate Limiting
- [ ] ¿Flask-Limiter está configurado?
- [ ] ¿Los límites son razonables (no tan altos que sean inútiles)?
- [ ] ¿El almacenamiento del limiter es persistente? (en memoria en v0.25 = se reinicia)

### CORS
- [ ] ¿Solo los orígenes correctos están permitidos?
- [ ] ¿credentials: true solo para el origen específico, no *?
- [ ] ¿El origen está en variable de entorno?

### Content Security Policy
- [ ] ¿Existe CSP configurado? (PENDIENTE en v0.25)
- [ ] ¿Previene carga de scripts externos no autorizados?

### Security Headers
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY o SAMEORIGIN
- [ ] Referrer-Policy
- [ ] HSTS (solo en producción con HTTPS)

### File Upload
- [ ] ¿Se valida el tipo MIME real (no solo la extensión)?
- [ ] ¿Hay límite de tamaño?
- [ ] ¿Los archivos se guardan fuera del directorio de la aplicación?
- [ ] ¿Los nombres de archivo se sanean?
- [ ] (No implementado en v0.25)

### Path Traversal
- [ ] ¿No se usan nombres de archivo del usuario directamente en rutas del sistema?
- [ ] ¿Se sanean los nombres de archivo?

### Open Redirect
- [ ] ¿Los redirects no usan URLs del cliente sin validar?
- [ ] ¿Se valida que el redirect es a un dominio conocido?

### Request Size
- [ ] ¿Hay límite al tamaño del body de las peticiones?
- [ ] Flask tiene MAX_CONTENT_LENGTH configurado?

### Input Validation
- [ ] ¿Todos los campos del request se validan en el backend?
- [ ] ¿Se validan tipos, longitudes, formatos y valores permitidos?
- [ ] ¿Se rechazan payloads inesperadamente grandes?

### Secrets
- [ ] ¿SECRET_KEY viene de variable de entorno?
- [ ] ¿No hay secrets hardcodeados en el código?
- [ ] ¿El .env no está en el repositorio?
- [ ] ¿El .gitignore incluye .env?

### Logging
- [ ] ¿Los logs no incluyen contraseñas?
- [ ] ¿Los logs no incluyen tokens de seguridad?
- [ ] ¿Los logs no incluyen datos personales innecesarios?
- [ ] ¿Hay suficiente logging para detectar ataques?

### Errores
- [ ] ¿Los errores no exponen stack traces en producción?
- [ ] ¿Los errores no exponen consultas SQL?
- [ ] ¿Los mensajes de error son seguros y útiles?

### Configuración
- [ ] ¿DEBUG=False en producción?
- [ ] ¿FLASK_ENV=production en producción?
- [ ] ¿SESSION_COOKIE_SECURE=True en producción?
- [ ] ¿SECRET_KEY es suficientemente larga y aleatoria?

### Dependencias
- [ ] ¿Las versiones están fijadas en requirements.txt?
- [ ] ¿Hay dependencias con vulnerabilidades conocidas?

## 5. Reglas obligatorias

1. No asumir que el código es seguro. Verificar.
2. No marcar seguridad como VERIFICADA sin pruebas reales.
3. Todo input del cliente es sospechoso hasta que se valide.
4. Los errores nunca exponen información interna.
5. Las contraseñas nunca se guardan en texto plano.
6. Los tokens de seguridad usan `secrets`, no `random`.
7. El rol del usuario siempre viene de la base de datos.

## 6. Procedimiento de revisión de seguridad

```
1. Leer el código de cada endpoint.
2. Para cada endpoint, verificar la lista de la sección 4.
3. Identificar vulnerabilidades.
4. Documentar con severidad: CRÍTICA / ALTA / MEDIA / BAJA.
5. Proponer corrección.
6. Verificar corrección con prueba real.
7. Actualizar docs/SECURITY.md y docs/MATRIZ_SEGURIDAD.md.
```

## 7. Severidades

| Severidad | Descripción |
|-----------|-------------|
| CRÍTICA | Compromete datos de todos los usuarios. Acción inmediata. |
| ALTA | Compromete datos de usuarios específicos. Resolver en esta fase. |
| MEDIA | Aumenta la superficie de ataque. Resolver antes de v1.0. |
| BAJA | Mejora de hardening. Resolver si el tiempo lo permite. |

## 8. Checklist de seguridad mínima para v1.0

- [ ] SQL Injection: prevenido por SQLAlchemy
- [ ] XSS: validación de salida en frontend
- [ ] CSRF: Flask-WTF activo y funcionando
- [ ] IDOR: verificación de ownership en todos los endpoints
- [ ] Rate Limiting: en todos los endpoints sensibles
- [ ] Contraseñas: Argon2id
- [ ] Sesiones: HttpOnly + SameSite + Secure
- [ ] Secrets: todos en variables de entorno
- [ ] Errores: sin stack traces en producción
- [ ] CORS: solo orígenes permitidos

## 9. Criterios de finalización

La seguridad está verificada cuando:
- Todos los items del checklist están marcados.
- Las pruebas de seguridad controladas pasaron.
- La revisión OWASP Top 10 está completa.
- Las 100 reglas de docs/REGLAS_100.md están evaluadas.

## 10. Errores que debe evitar

- Asumir que el código es seguro porque "se ve bien".
- Marcar seguridad como VERIFICADA sin pruebas.
- Ignorar vulnerabilidades de severidad baja/media.
- Confiar en las validaciones del frontend.
- Dejar DEBUG=True en producción.

## 11. Documentación que debe actualizar

- `docs/SECURITY.md` — al cambiar configuraciones o políticas de seguridad.
- `docs/MATRIZ_SEGURIDAD.md` — al verificar o identificar vulnerabilidades.
- `docs/REGLAS_100.md` — al cambiar el estado de las reglas.
