# REGLAS_100.md — 100 Reglas de Seguridad y Desarrollo para EncuentraU

**Proyecto**: EncuentraU
**Estado inicial**: TODAS en estado PENDIENTE
**Nota**: IMPLEMENTADO =/= VERIFICADO. Una regla solo es VERIFICADO cuando existe evidencia real.

---

## CATEGORÍA A: AUTENTICACIÓN (RU-001 a RU-015)

### RU-001
- **Descripción**: Las contraseñas nunca se almacenan en texto plano.
- **Objetivo**: Proteger las contraseñas aunque la base de datos sea comprometida.
- **Criterio de cumplimiento**: El hash se guarda usando Argon2id con parámetros adecuados.
- **Prueba sugerida**: Verificar en la BD que password_hash no contiene la contraseña original.
- **Estado**: PENDIENTE

### RU-002
- **Descripción**: Se usa Argon2id para el hashing de contraseñas.
- **Objetivo**: Usar el algoritmo de hashing más resistente disponible.
- **Criterio de cumplimiento**: argon2-cffi instalado y usado en auth_service.py.
- **Prueba sugerida**: Revisar requirements.txt e implementación de crear_hash().
- **Estado**: PENDIENTE

### RU-003
- **Descripción**: Las contraseñas tienen mínimo 12 caracteres.
- **Objetivo**: Resistir ataques de diccionario y fuerza bruta básicos.
- **Criterio de cumplimiento**: Backend rechaza contraseñas cortas con código 400.
- **Prueba sugerida**: POST /api/auth/registro con contraseña de 11 caracteres → esperar 400.
- **Estado**: PENDIENTE

### RU-004
- **Descripción**: Las contraseñas requieren mayúsculas, minúsculas, números y caracteres especiales.
- **Objetivo**: Aumentar la entropía y resistencia a ataques.
- **Criterio de cumplimiento**: Backend valida cada requisito y retorna errores específicos.
- **Prueba sugerida**: POST /api/auth/registro sin cada requisito → esperar 400.
- **Estado**: PENDIENTE

### RU-005
- **Descripción**: Las contraseñas comunes están bloqueadas.
- **Objetivo**: Prevenir contraseñas fácilmente adivinables.
- **Criterio de cumplimiento**: Lista de contraseñas comunes configurada y validada en el backend.
- **Prueba sugerida**: POST /api/auth/registro con "password123" → esperar 400.
- **Estado**: PENDIENTE

### RU-006
- **Descripción**: La contraseña no debe contener el nombre o correo del usuario.
- **Objetivo**: Prevenir contraseñas predecibles basadas en datos personales.
- **Criterio de cumplimiento**: Backend verifica que la contraseña no contiene nombre ni parte del correo.
- **Prueba sugerida**: POST /api/auth/registro con contraseña que contiene el nombre → esperar 400.
- **Estado**: PENDIENTE

### RU-007
- **Descripción**: Los mensajes de error de login son genéricos.
- **Objetivo**: Prevenir enumeración de usuarios.
- **Criterio de cumplimiento**: Login retorna el mismo mensaje para correo inexistente y contraseña incorrecta.
- **Prueba sugerida**: Comparar respuesta correo inexistente vs correo correcto con contraseña incorrecta.
- **Estado**: PENDIENTE

### RU-008
- **Descripción**: Hay rate limiting en el endpoint de login.
- **Objetivo**: Prevenir ataques de fuerza bruta.
- **Criterio de cumplimiento**: Después de 10 intentos por minuto, retorna 429.
- **Prueba sugerida**: 11 peticiones de login en 1 minuto → esperar 429 en la 11a.
- **Estado**: PENDIENTE

### RU-009
- **Descripción**: Hay rate limiting en el endpoint de registro.
- **Objetivo**: Prevenir creación masiva de cuentas.
- **Criterio de cumplimiento**: Después de 5 intentos por minuto, retorna 429.
- **Prueba sugerida**: 6 peticiones de registro en 1 minuto → esperar 429 en la 6a.
- **Estado**: PENDIENTE

### RU-010
- **Descripción**: session.clear() se llama antes de establecer una nueva sesión.
- **Objetivo**: Prevenir Session Fixation.
- **Criterio de cumplimiento**: En el controlador de login, session.clear() precede a session['usuario_id'].
- **Prueba sugerida**: Revisar auth_controller.py → función iniciar_sesion().
- **Estado**: PENDIENTE

### RU-011
- **Descripción**: La cookie de sesión tiene HttpOnly=True.
- **Objetivo**: Prevenir acceso a la cookie desde JavaScript (XSS).
- **Criterio de cumplimiento**: SESSION_COOKIE_HTTPONLY=True en config.py.
- **Prueba sugerida**: Revisar la cookie en el navegador → debe tener flag HttpOnly.
- **Estado**: PENDIENTE

### RU-012
- **Descripción**: La cookie de sesión tiene SameSite=Lax o Strict.
- **Objetivo**: Protección básica contra CSRF cross-origin.
- **Criterio de cumplimiento**: SESSION_COOKIE_SAMESITE='Lax' en config.py.
- **Prueba sugerida**: Revisar la cookie → debe tener SameSite.
- **Estado**: PENDIENTE

### RU-013
- **Descripción**: La cookie de sesión tiene Secure=True en producción.
- **Objetivo**: La cookie solo se envía por HTTPS.
- **Criterio de cumplimiento**: SESSION_COOKIE_SECURE=True cuando FLASK_ENV=production.
- **Prueba sugerida**: En producción → verificar flag Secure en la cookie.
- **Estado**: PENDIENTE

### RU-014
- **Descripción**: Los tokens de recuperación usan secrets.token_urlsafe().
- **Objetivo**: Generador criptográficamente seguro, no random.
- **Criterio de cumplimiento**: recuperacion_service.py usa secrets.token_urlsafe(32).
- **Prueba sugerida**: Revisar el código de recuperacion_service.py.
- **Estado**: PENDIENTE

### RU-015
- **Descripción**: Los tokens de recuperación expiran en 30 minutos.
- **Objetivo**: Limitar la ventana de uso de un token comprometido.
- **Criterio de cumplimiento**: Token tiene campo expira_en y se verifica antes de usarlo.
- **Prueba sugerida**: Usar un token después de 31 minutos → esperar 400.
- **Estado**: PENDIENTE

---

## CATEGORÍA B: AUTORIZACIÓN (RU-016 a RU-030)

### RU-016
- **Descripción**: El rol del usuario viene de la base de datos, nunca del cliente.
- **Objetivo**: Prevenir escalamiento de privilegios por Mass Assignment.
- **Criterio de cumplimiento**: El campo 'rol' del body del request se ignora.
- **Prueba sugerida**: POST /api/auth/registro con "rol": "administrador" → usuario debe ser 'ciudadano'.
- **Estado**: PENDIENTE

### RU-017
- **Descripción**: Los endpoints de administrador verifican el rol en el backend.
- **Objetivo**: Prevenir acceso no autorizado a funciones administrativas.
- **Criterio de cumplimiento**: Cada endpoint de admin tiene verificación de rol=='administrador'.
- **Prueba sugerida**: Acceder a /api/admin/* con sesión de ciudadano → esperar 403.
- **Estado**: PENDIENTE

### RU-018
- **Descripción**: Los endpoints protegidos verifican autenticación.
- **Objetivo**: Prevenir acceso anónimo a recursos que requieren login.
- **Criterio de cumplimiento**: Endpoints de escritura retornan 401 sin sesión activa.
- **Prueba sugerida**: POST /api/objetos sin sesión → esperar 401.
- **Estado**: PENDIENTE

### RU-019
- **Descripción**: La verificación de ownership protege modificaciones de objetos.
- **Objetivo**: Prevenir IDOR — que un usuario modifique datos de otro.
- **Criterio de cumplimiento**: Al modificar un objeto, se verifica que pertenece al usuario actual.
- **Prueba sugerida**: Usuario A intenta PUT /api/objetos/{id_de_B} → esperar 403.
- **Estado**: PENDIENTE

### RU-020
- **Descripción**: La verificación de ownership protege eliminaciones.
- **Objetivo**: Prevenir que un usuario elimine datos de otro.
- **Criterio de cumplimiento**: Al eliminar un objeto, se verifica ownership o rol admin.
- **Prueba sugerida**: Usuario A intenta DELETE /api/objetos/{id_de_B} → esperar 403.
- **Estado**: PENDIENTE

### RU-021
- **Descripción**: Los campos permitidos en actualizaciones están en whitelist.
- **Objetivo**: Prevenir Mass Assignment.
- **Criterio de cumplimiento**: Solo los campos explícitamente listados se aceptan en PUT/PATCH.
- **Prueba sugerida**: PUT /api/objetos/:id con campo 'usuario_id' → campo debe ignorarse.
- **Estado**: PENDIENTE

### RU-022
- **Descripción**: Un usuario no puede reclamar su propio objeto.
- **Objetivo**: Integridad del proceso de reclamación.
- **Criterio de cumplimiento**: Solicitud rechazada si usuario_solicitante == usuario_reportante.
- **Prueba sugerida**: Usuario A intenta reclamar su propio reporte → esperar error.
- **Estado**: PENDIENTE

### RU-023
- **Descripción**: Las solicitudes de reclamación requieren verificación humana.
- **Objetivo**: Prevenir apropiación automática de objetos.
- **Criterio de cumplimiento**: Las solicitudes pasan por estado 'en_revision' antes de aprobarse.
- **Prueba sugerida**: Crear solicitud → verificar que estado inicial es 'pendiente'.
- **Estado**: PENDIENTE

### RU-024
- **Descripción**: Los errores de autorización retornan 403, no 404.
- **Objetivo**: Comportamiento correcto de la API.
- **Criterio de cumplimiento**: Acceder a recurso existente sin permiso → 403.
- **Prueba sugerida**: Usuario A intenta ver recurso privado de B → verificar código 403.
- **Estado**: PENDIENTE

### RU-025
- **Descripción**: Los endpoints sin autenticación son explícitamente declarados públicos.
- **Objetivo**: DENY BY DEFAULT.
- **Criterio de cumplimiento**: Solo los endpoints documentados como públicos son accesibles sin sesión.
- **Prueba sugerida**: Inventariar endpoints y verificar que cada uno tiene política definida.
- **Estado**: PENDIENTE

### RU-026
- **Descripción**: El frontend no toma decisiones de seguridad basadas en el rol del cliente.
- **Objetivo**: El backend es la única autoridad de permisos.
- **Criterio de cumplimiento**: Ocultar elementos de UI no es suficiente; el backend rechaza peticiones no autorizadas.
- **Prueba sugerida**: Modificar JS para acceder a función de admin → backend debe rechazar.
- **Estado**: PENDIENTE

### RU-027
- **Descripción**: Los filtros de listado de recursos respetan la autorización.
- **Objetivo**: Un usuario solo ve sus propios datos privados.
- **Criterio de cumplimiento**: GET /api/mis-reportes solo retorna reportes del usuario autenticado.
- **Prueba sugerida**: Usuario A llama /api/mis-reportes → no debe ver reportes de B.
- **Estado**: PENDIENTE

### RU-028
- **Descripción**: El administrador puede acceder a todos los recursos.
- **Objetivo**: El admin puede gestionar el sistema completo.
- **Criterio de cumplimiento**: Con rol administrador, se pueden ver y gestionar todos los reportes.
- **Prueba sugerida**: Admin accede a recurso de cualquier usuario → 200.
- **Estado**: PENDIENTE

### RU-029
- **Descripción**: No hay endpoints de admin accesibles sin autenticación.
- **Objetivo**: Seguridad básica de las funciones administrativas.
- **Criterio de cumplimiento**: /api/admin/* sin sesión → 401.
- **Prueba sugerida**: GET /api/admin/usuarios sin sesión → esperar 401.
- **Estado**: PENDIENTE

### RU-030
- **Descripción**: Los tokens de recuperación se invalidan al cambiar la contraseña.
- **Objetivo**: Prevenir uso de tokens antiguos.
- **Criterio de cumplimiento**: Al restablecer contraseña exitosamente, el token se marca como usado.
- **Prueba sugerida**: Usar el mismo token dos veces → segundo intento retorna 400.
- **Estado**: PENDIENTE

---

## CATEGORÍA C: INYECCIÓN Y XSS (RU-031 a RU-040)

### RU-031
- **Descripción**: No hay SQL Injection posible en ningún endpoint.
- **Objetivo**: Proteger la base de datos contra manipulación.
- **Criterio de cumplimiento**: SQLAlchemy ORM usado en todas las consultas, sin SQL crudo concatenado.
- **Prueba sugerida**: Enviar payloads SQL en campos de login y registro → comportamiento normal.
- **Estado**: PENDIENTE

### RU-032
- **Descripción**: Las consultas parametrizadas se usan en toda interacción con la BD.
- **Objetivo**: Prevenir SQL Injection a nivel de implementación.
- **Criterio de cumplimiento**: No hay f-strings ni concatenación en consultas SQL.
- **Prueba sugerida**: Revisar código de models/ → no debe haber SQL dinámico sin parámetros.
- **Estado**: PENDIENTE

### RU-033
- **Descripción**: Los datos del usuario se escapan correctamente al mostrarlos en HTML.
- **Objetivo**: Prevenir XSS almacenado.
- **Criterio de cumplimiento**: El frontend no inserta datos sin escapar en innerHTML.
- **Prueba sugerida**: Registrar objeto con nombre con script → no debe ejecutarse.
- **Estado**: PENDIENTE

### RU-034
- **Descripción**: No se usa innerHTML con datos del servidor.
- **Objetivo**: Prevenir XSS DOM.
- **Criterio de cumplimiento**: El JS del frontend usa textContent para insertar datos.
- **Prueba sugerida**: Inspeccionar el JS → buscar usos de innerHTML con variables.
- **Estado**: PENDIENTE

### RU-035
- **Descripción**: Content-Security-Policy está configurado.
- **Objetivo**: Capa adicional de protección contra XSS.
- **Criterio de cumplimiento**: Header CSP presente en todas las respuestas.
- **Prueba sugerida**: curl -I → verificar header Content-Security-Policy.
- **Estado**: PENDIENTE

### RU-036
- **Descripción**: Los nombres de archivo subidos se sanean.
- **Objetivo**: Prevenir Path Traversal.
- **Criterio de cumplimiento**: Nombres de archivo saneados con werkzeug.utils.secure_filename.
- **Prueba sugerida**: Subir archivo con nombre malicioso → verificar que se sanea.
- **Estado**: PENDIENTE

### RU-037
- **Descripción**: Los tipos de archivo subidos se validan por contenido, no solo extensión.
- **Objetivo**: Prevenir subida de archivos maliciosos.
- **Criterio de cumplimiento**: Se verifica el tipo MIME real del archivo.
- **Prueba sugerida**: Subir script PHP con extensión .jpg → debe rechazarse.
- **Estado**: PENDIENTE

### RU-038
- **Descripción**: Los archivos subidos se almacenan fuera del directorio de la aplicación.
- **Objetivo**: Prevenir ejecución de archivos subidos.
- **Criterio de cumplimiento**: Directorio de uploads fuera de static/ y de la app.
- **Prueba sugerida**: Verificar configuración de UPLOAD_FOLDER.
- **Estado**: PENDIENTE

### RU-039
- **Descripción**: No hay Open Redirect posible.
- **Objetivo**: Prevenir redireccionamiento a sitios maliciosos.
- **Criterio de cumplimiento**: URLs de redirect validadas contra dominios permitidos.
- **Prueba sugerida**: Si hay parámetros de redirect, intentar redirigir a google.com → debe fallar.
- **Estado**: PENDIENTE

### RU-040
- **Descripción**: Los filtros de búsqueda son seguros contra inyección.
- **Objetivo**: Prevenir SQLi en búsquedas.
- **Criterio de cumplimiento**: Los filtros de búsqueda usan SQLAlchemy con parámetros.
- **Prueba sugerida**: Enviar caracteres especiales en parámetros de búsqueda → comportamiento normal.
- **Estado**: PENDIENTE

---

## CATEGORÍA D: CSRF Y SESIONES (RU-041 a RU-050)

### RU-041
- **Descripción**: Flask-WTF CSRFProtect está activo en peticiones POST/PUT/DELETE.
- **Objetivo**: Prevenir CSRF.
- **Criterio de cumplimiento**: CSRFProtect inicializado en extensions.py y activo.
- **Prueba sugerida**: POST /api/auth/login sin X-CSRFToken → esperar 400.
- **Estado**: PENDIENTE

### RU-042
- **Descripción**: El frontend obtiene el token CSRF antes de cada formulario.
- **Objetivo**: El CSRF token es válido y fresco.
- **Criterio de cumplimiento**: El JS llama GET /api/auth/csrf-token antes de cada operación sensible.
- **Prueba sugerida**: Verificar en el código JS que se obtiene el token antes de enviar.
- **Estado**: PENDIENTE

### RU-043
- **Descripción**: El CSRF token se envía en el header X-CSRFToken.
- **Objetivo**: El backend puede validar el token.
- **Criterio de cumplimiento**: Todas las peticiones POST/PUT/DELETE incluyen X-CSRFToken.
- **Prueba sugerida**: Hacer petición con token incorrecto → esperar 400.
- **Estado**: PENDIENTE

### RU-044
- **Descripción**: La SECRET_KEY es suficientemente larga y aleatoria.
- **Objetivo**: La firma de la sesión es imposible de predecir.
- **Criterio de cumplimiento**: SECRET_KEY tiene al menos 32 bytes de entropía.
- **Prueba sugerida**: Verificar en config.py que no hay SECRET_KEY hardcodeada en producción.
- **Estado**: PENDIENTE

### RU-045
- **Descripción**: La SECRET_KEY viene de variable de entorno.
- **Objetivo**: No exponer la clave secreta en el código fuente.
- **Criterio de cumplimiento**: SECRET_KEY = os.environ.get('SECRET_KEY') sin valor usable por defecto.
- **Prueba sugerida**: Revisar config.py → no hay clave por defecto para producción.
- **Estado**: PENDIENTE

### RU-046
- **Descripción**: No se guarda información sensible en la sesión.
- **Objetivo**: Limitar el impacto si la sesión es comprometida.
- **Criterio de cumplimiento**: La sesión solo guarda usuario_id, nunca contraseñas o tokens.
- **Prueba sugerida**: Revisar todo el código que escribe en session[].
- **Estado**: PENDIENTE

### RU-047
- **Descripción**: La sesión se invalida completamente en logout.
- **Objetivo**: Que el logout sea efectivo.
- **Criterio de cumplimiento**: cerrar_sesion() llama session.clear().
- **Prueba sugerida**: Logout → intentar acceder a endpoint protegido → esperar 401.
- **Estado**: PENDIENTE

### RU-048
- **Descripción**: No se guarda el token CSRF o la sesión en localStorage.
- **Objetivo**: Proteger tokens contra acceso JavaScript (XSS).
- **Criterio de cumplimiento**: El JS no guarda tokens en localStorage ni sessionStorage.
- **Prueba sugerida**: Revisar el código JS → buscar localStorage.setItem con tokens.
- **Estado**: PENDIENTE

### RU-049
- **Descripción**: La sesión tiene tiempo de expiración configurado.
- **Objetivo**: Limitar la duración de sesiones abandonadas.
- **Criterio de cumplimiento**: PERMANENT_SESSION_LIFETIME configurado o session.permanent=False.
- **Prueba sugerida**: Revisar config.py → verificar configuración de expiración.
- **Estado**: PENDIENTE

### RU-050
- **Descripción**: Los tokens de recuperación son de un solo uso.
- **Objetivo**: Prevenir reutilización de tokens.
- **Criterio de cumplimiento**: El token se marca como 'usado=True' tras restablecimiento exitoso.
- **Prueba sugerida**: Usar token dos veces → segundo uso retorna 400.
- **Estado**: PENDIENTE

---
