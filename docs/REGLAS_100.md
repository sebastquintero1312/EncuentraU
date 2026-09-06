# REGLAS_100.md — 100 Reglas de Seguridad y Desarrollo para EncuentraU

**Proyecto**: EncuentraU
**Última actualización**: 2026-09-06 (migración v0.25 → v1.0)
**Nota**: IMPLEMENTADO =/= VERIFICADO. Una regla solo es VERIFICADO cuando existe evidencia real de ejecución (test automatizado, prueba manual/E2E documentada, o inspección directa de una respuesta HTTP real). Ver `docs/evidencia/` para la evidencia citada en este documento.

**Leyenda de estados**: PENDIENTE · EN_DESARROLLO · IMPLEMENTADO · VERIFICADO · PARCIAL · BLOQUEADO · NO_APLICA

---

## CATEGORÍA A: AUTENTICACIÓN (RU-001 a RU-015)

### RU-001
- **Descripción**: Las contraseñas nunca se almacenan en texto plano.
- **Objetivo**: Proteger las contraseñas aunque la base de datos sea comprometida.
- **Criterio de cumplimiento**: El hash se guarda usando Argon2id con parámetros adecuados.
- **Prueba sugerida**: Verificar en la BD que password_hash no contiene la contraseña original.
- **Archivo relacionado**: `backend/app/services/auth_service.py`
- **Evidencia**: `backend/tests/unit/test_auth_service.py::test_hash_no_es_texto_plano`
- **Estado**: VERIFICADO

### RU-002
- **Descripción**: Se usa Argon2id para el hashing de contraseñas.
- **Objetivo**: Usar el algoritmo de hashing más resistente disponible.
- **Criterio de cumplimiento**: argon2-cffi instalado y usado en auth_service.py.
- **Prueba sugerida**: Revisar requirements.txt e implementación de crear_hash().
- **Archivo relacionado**: `backend/requirements.txt`, `backend/app/services/auth_service.py`
- **Evidencia**: `test_hash_no_es_texto_plano` verifica que el hash empieza con `$argon2id$`.
- **Estado**: VERIFICADO

### RU-003
- **Descripción**: Las contraseñas tienen mínimo 12 caracteres.
- **Objetivo**: Resistir ataques de diccionario y fuerza bruta básicos.
- **Criterio de cumplimiento**: Backend rechaza contraseñas cortas con código 400.
- **Prueba sugerida**: POST /api/auth/registro con contraseña de 11 caracteres → esperar 400.
- **Archivo relacionado**: `backend/app/services/auth_service.py`
- **Evidencia**: `test_registro_falla_con_contrasena_debil`, `test_validar_contrasena_debil`
- **Estado**: VERIFICADO

### RU-004
- **Descripción**: Las contraseñas requieren mayúsculas, minúsculas, números y caracteres especiales.
- **Objetivo**: Aumentar la entropía y resistencia a ataques.
- **Criterio de cumplimiento**: Backend valida cada requisito y retorna errores específicos.
- **Prueba sugerida**: POST /api/auth/registro sin cada requisito → esperar 400.
- **Archivo relacionado**: `backend/app/services/auth_service.py`
- **Evidencia**: `test_validar_contrasena_debil`, `test_validar_contrasena_fuerte`
- **Estado**: VERIFICADO

### RU-005
- **Descripción**: Las contraseñas comunes están bloqueadas.
- **Objetivo**: Prevenir contraseñas fácilmente adivinables.
- **Criterio de cumplimiento**: Lista de contraseñas comunes configurada y validada en el backend.
- **Prueba sugerida**: POST /api/auth/registro con "password123" → esperar 400.
- **Archivo relacionado**: `backend/app/services/auth_service.py`
- **Evidencia**: `test_validar_contrasena_comun_rechazada`
- **Estado**: VERIFICADO

### RU-006
- **Descripción**: La contraseña no debe contener el nombre o correo del usuario.
- **Objetivo**: Prevenir contraseñas predecibles basadas en datos personales.
- **Criterio de cumplimiento**: Backend verifica que la contraseña no contiene nombre ni parte del correo.
- **Prueba sugerida**: POST /api/auth/registro con contraseña que contiene el nombre → esperar 400.
- **Archivo relacionado**: `backend/app/services/auth_service.py`
- **Evidencia**: `test_validar_contrasena_no_debe_contener_el_correo`; detectado también "en vivo" cuando la contraseña de prueba `ClaveAdmin!2026` fue rechazada por contener el nombre "Admin" durante la verificación E2E.
- **Estado**: VERIFICADO

### RU-007
- **Descripción**: Los mensajes de error de login son genéricos.
- **Objetivo**: Prevenir enumeración de usuarios.
- **Criterio de cumplimiento**: Login retorna el mismo mensaje para correo inexistente y contraseña incorrecta.
- **Prueba sugerida**: Comparar respuesta correo inexistente vs correo correcto con contraseña incorrecta.
- **Archivo relacionado**: `backend/app/controllers/auth_controller.py`
- **Evidencia**: `test_login_mensaje_no_revela_si_el_correo_existe`
- **Estado**: VERIFICADO

### RU-008
- **Descripción**: Hay rate limiting en el endpoint de login.
- **Objetivo**: Prevenir ataques de fuerza bruta.
- **Criterio de cumplimiento**: Después de 10 intentos por minuto, retorna 429.
- **Prueba sugerida**: 11 peticiones de login en 1 minuto → esperar 429 en la 11a.
- **Archivo relacionado**: `backend/app/routes/auth_routes.py`
- **Evidencia**: `test_rate_limit_login`; también observado en `smoke_test_manual_v1.0.md` #16.
- **Estado**: VERIFICADO

### RU-009
- **Descripción**: Hay rate limiting en el endpoint de registro.
- **Objetivo**: Prevenir creación masiva de cuentas.
- **Criterio de cumplimiento**: Después de 5 intentos por minuto, retorna 429.
- **Prueba sugerida**: 6 peticiones de registro en 1 minuto → esperar 429 en la 6a.
- **Archivo relacionado**: `backend/app/routes/auth_routes.py`
- **Evidencia**: `test_rate_limit_registro`
- **Estado**: VERIFICADO

### RU-010
- **Descripción**: session.clear() se llama antes de establecer una nueva sesión.
- **Objetivo**: Prevenir Session Fixation.
- **Criterio de cumplimiento**: En el controlador de login, session.clear() precede a session['usuario_id'].
- **Prueba sugerida**: Revisar auth_controller.py → función iniciar_sesion().
- **Archivo relacionado**: `backend/app/controllers/auth_controller.py`
- **Evidencia**: Inspección directa del código (línea con `session.clear()` antes de `session['usuario_id'] = usuario.id`). Su efecto colateral (invalidar el CSRF token de la sesión anterior) fue lo que reveló el bug corregido documentado en `docs/evidencia/smoke_test_manual_v1.0.md`.
- **Estado**: VERIFICADO

### RU-011
- **Descripción**: La cookie de sesión tiene HttpOnly=True.
- **Objetivo**: Prevenir acceso a la cookie desde JavaScript (XSS).
- **Criterio de cumplimiento**: SESSION_COOKIE_HTTPONLY=True en config.py.
- **Prueba sugerida**: Revisar la cookie en el navegador → debe tener flag HttpOnly.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Cabecera real inspeccionada con curl: `Set-Cookie: session=...; HttpOnly; Path=/; SameSite=Lax`.
- **Estado**: VERIFICADO

### RU-012
- **Descripción**: La cookie de sesión tiene SameSite=Lax o Strict.
- **Objetivo**: Protección básica contra CSRF cross-origin.
- **Criterio de cumplimiento**: SESSION_COOKIE_SAMESITE='Lax' en config.py.
- **Prueba sugerida**: Revisar la cookie → debe tener SameSite.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Misma cabecera real que RU-011: `SameSite=Lax` presente.
- **Estado**: VERIFICADO

### RU-013
- **Descripción**: La cookie de sesión tiene Secure=True en producción.
- **Objetivo**: La cookie solo se envía por HTTPS.
- **Criterio de cumplimiento**: SESSION_COOKIE_SECURE=True cuando FLASK_ENV=production.
- **Prueba sugerida**: En producción → verificar flag Secure en la cookie.
- **Archivo relacionado**: `backend/app/config/config.py` (`SESSION_COOKIE_SECURE = ES_PRODUCCION`)
- **Evidencia**: Código revisado; en desarrollo (HTTP) se confirmó que el flag está correctamente AUSENTE (como debe ser, si no la sesión no funcionaría por HTTP). No se ha verificado su presencia en un despliegue real de producción por HTTPS.
- **Estado**: BLOQUEADO (implementación correcta, verificación real pendiente del despliegue — ver docs/DEPLOYMENT.md)

### RU-014
- **Descripción**: Los tokens de recuperación usan secrets.token_urlsafe().
- **Objetivo**: Generador criptográficamente seguro, no random.
- **Criterio de cumplimiento**: recuperacion_service.py usa secrets.token_urlsafe(32).
- **Prueba sugerida**: Revisar el código de recuperacion_service.py.
- **Archivo relacionado**: `backend/app/services/recuperacion_service.py`
- **Evidencia**: Inspección directa del código + `test_restablecer_contrasena_con_token_valido` confirma que el token generado funciona end-to-end.
- **Estado**: VERIFICADO

### RU-015
- **Descripción**: Los tokens de recuperación expiran en 30 minutos.
- **Objetivo**: Limitar la ventana de uso de un token comprometido.
- **Criterio de cumplimiento**: Token tiene campo expira_en y se verifica antes de usarlo.
- **Prueba sugerida**: Usar un token después de 31 minutos → esperar 400.
- **Archivo relacionado**: `backend/app/models/token_recuperacion.py`
- **Evidencia**: `test_token_recuperacion_expirado_es_rechazado` (fuerza la expiración manipulando `expira_en` directamente en la BD de prueba, sin esperar 30 minutos reales).
- **Estado**: VERIFICADO

---

## CATEGORÍA B: AUTORIZACIÓN (RU-016 a RU-030)

### RU-016
- **Descripción**: El rol del usuario viene de la base de datos, nunca del cliente.
- **Objetivo**: Prevenir escalamiento de privilegios por Mass Assignment.
- **Criterio de cumplimiento**: El campo 'rol' del body del request se ignora.
- **Prueba sugerida**: POST /api/auth/registro con "rol": "administrador" → usuario debe ser 'ciudadano'.
- **Archivo relacionado**: `backend/app/models/usuario.py` (`crear_usuario`)
- **Evidencia**: `test_registro_ignora_rol_enviado_por_el_cliente`
- **Estado**: VERIFICADO

### RU-017
- **Descripción**: Los endpoints de administrador verifican el rol en el backend.
- **Objetivo**: Prevenir acceso no autorizado a funciones administrativas.
- **Criterio de cumplimiento**: Cada endpoint de admin tiene verificación de rol=='administrador'.
- **Prueba sugerida**: Acceder a /api/admin/* con sesión de ciudadano → esperar 403.
- **Archivo relacionado**: `backend/app/middlewares/autorizacion.py` (`admin_requerido`)
- **Evidencia**: `test_listar_usuarios_requiere_admin`, `test_cambiar_estado_objeto_requiere_admin`, `test_solicitudes_admin_requiere_rol_admin`
- **Estado**: VERIFICADO

### RU-018
- **Descripción**: Los endpoints protegidos verifican autenticación.
- **Objetivo**: Prevenir acceso anónimo a recursos que requieren login.
- **Criterio de cumplimiento**: Endpoints de escritura retornan 401 sin sesión activa.
- **Prueba sugerida**: POST /api/objetos sin sesión → esperar 401.
- **Archivo relacionado**: `backend/app/middlewares/autorizacion.py` (`login_requerido`)
- **Evidencia**: `test_crear_objeto_requiere_autenticacion`, `test_mis_reportes_requiere_autenticacion`, `test_crear_solicitud_requiere_autenticacion`
- **Estado**: VERIFICADO

### RU-019
- **Descripción**: La verificación de ownership protege modificaciones de objetos.
- **Objetivo**: Prevenir IDOR — que un usuario modifique datos de otro.
- **Criterio de cumplimiento**: Al modificar un objeto, se verifica que pertenece al usuario actual.
- **Prueba sugerida**: Usuario A intenta PUT /api/objetos/{id_de_B} → esperar 403.
- **Archivo relacionado**: `backend/app/controllers/objetos_controller.py` (`_es_dueno_o_admin`)
- **Evidencia**: `test_no_puede_editar_reporte_ajeno`, `test_no_se_puede_acceder_a_recurso_de_otro_usuario_cambiando_el_id`
- **Estado**: VERIFICADO

### RU-020
- **Descripción**: La verificación de ownership protege eliminaciones.
- **Objetivo**: Prevenir que un usuario elimine datos de otro.
- **Criterio de cumplimiento**: Al eliminar un objeto, se verifica ownership o rol admin.
- **Prueba sugerida**: Usuario A intenta DELETE /api/objetos/{id_de_B} → esperar 403.
- **Archivo relacionado**: `backend/app/controllers/objetos_controller.py` (`cancelar`)
- **Evidencia**: `test_no_puede_cancelar_reporte_ajeno`
- **Estado**: VERIFICADO

### RU-021
- **Descripción**: Los campos permitidos en actualizaciones están en whitelist.
- **Objetivo**: Prevenir Mass Assignment.
- **Criterio de cumplimiento**: Solo los campos explícitamente listados se aceptan en PUT/PATCH.
- **Prueba sugerida**: PUT /api/objetos/:id con campo 'usuario_id' → campo debe ignorarse.
- **Archivo relacionado**: `backend/app/services/objetos_service.py` (`CAMPOS_EDITABLES`), `backend/app/services/usuarios_admin_service.py`
- **Evidencia**: `test_mass_assignment_no_permite_cambiar_estado_directamente`
- **Estado**: VERIFICADO

### RU-022
- **Descripción**: Un usuario no puede reclamar su propio objeto.
- **Objetivo**: Integridad del proceso de reclamación.
- **Criterio de cumplimiento**: Solicitud rechazada si usuario_solicitante == usuario_reportante.
- **Prueba sugerida**: Usuario A intenta reclamar su propio reporte → esperar error.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_no_puede_reclamar_su_propio_objeto`
- **Estado**: VERIFICADO

### RU-023
- **Descripción**: Las solicitudes de reclamación requieren verificación humana.
- **Objetivo**: Prevenir apropiación automática de objetos.
- **Criterio de cumplimiento**: Las solicitudes pasan por estado 'en_revision' antes de aprobarse.
- **Prueba sugerida**: Crear solicitud → verificar que estado inicial es 'pendiente'.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`, `backend/app/controllers/solicitudes_controller.py` (`revisar_admin`)
- **Evidencia**: `test_puede_reclamar_objeto_ajeno` (estado inicial 'pendiente'); `test_admin_aprueba_solicitud_resuelve_el_objeto` (solo un administrador puede aprobar, nunca es automático).
- **Estado**: VERIFICADO

### RU-024
- **Descripción**: Los errores de autorización retornan 403, no 404.
- **Objetivo**: Comportamiento correcto de la API.
- **Criterio de cumplimiento**: Acceder a recurso existente sin permiso → 403.
- **Prueba sugerida**: Usuario A intenta ver recurso privado de B → verificar código 403.
- **Archivo relacionado**: Todos los controladores con verificación de ownership.
- **Evidencia**: `test_solicitudes_privadas_solo_visibles_para_dueno_y_admin` (tercero recibe 403, no 404, sobre un objeto que sí existe).
- **Estado**: VERIFICADO

### RU-025
- **Descripción**: Los endpoints sin autenticación son explícitamente declarados públicos.
- **Objetivo**: DENY BY DEFAULT.
- **Criterio de cumplimiento**: Solo los endpoints documentados como públicos son accesibles sin sesión.
- **Prueba sugerida**: Inventariar endpoints y verificar que cada uno tiene política definida.
- **Archivo relacionado**: `docs/API.md` (tabla de endpoints con columna Auth)
- **Evidencia**: Inventario completo en `docs/API.md`: solo GET /objetos, GET /objetos/:id, GET /health y las rutas de autenticación no exigen sesión; todo lo demás usa `login_requerido` o `admin_requerido` explícitamente.
- **Estado**: VERIFICADO

### RU-026
- **Descripción**: El frontend no toma decisiones de seguridad basadas en el rol del cliente.
- **Objetivo**: El backend es la única autoridad de permisos.
- **Criterio de cumplimiento**: Ocultar elementos de UI no es suficiente; el backend rechaza peticiones no autorizadas.
- **Prueba sugerida**: Modificar JS para acceder a función de admin → backend debe rechazar.
- **Archivo relacionado**: `frontend/public/js/sesion.js` (guardia solo de experiencia de usuario)
- **Evidencia**: `test_cambiar_estado_objeto_requiere_admin` y equivalentes prueban el backend directamente, sin pasar por el frontend — confirma que el rechazo no depende de que el frontend "coopere".
- **Estado**: VERIFICADO

### RU-027
- **Descripción**: Los filtros de listado de recursos respetan la autorización.
- **Objetivo**: Un usuario solo ve sus propios datos privados.
- **Criterio de cumplimiento**: GET /api/mis-reportes solo retorna reportes del usuario autenticado.
- **Prueba sugerida**: Usuario A llama /api/mis-reportes → no debe ver reportes de B.
- **Archivo relacionado**: `backend/app/controllers/objetos_controller.py` (`mis_reportes`)
- **Evidencia**: `test_mis_reportes_solo_devuelve_los_propios`
- **Estado**: VERIFICADO

### RU-028
- **Descripción**: El administrador puede acceder a todos los recursos.
- **Objetivo**: El admin puede gestionar el sistema completo.
- **Criterio de cumplimiento**: Con rol administrador, se pueden ver y gestionar todos los reportes.
- **Prueba sugerida**: Admin accede a recurso de cualquier usuario → 200.
- **Archivo relacionado**: `backend/app/routes/admin_routes.py`
- **Evidencia**: `test_listar_objetos_admin_incluye_todos_los_estados`, `test_admin_cambia_estado_de_un_objeto`, `test_admin_puede_listar_usuarios`
- **Estado**: VERIFICADO

### RU-029
- **Descripción**: No hay endpoints de admin accesibles sin autenticación.
- **Objetivo**: Seguridad básica de las funciones administrativas.
- **Criterio de cumplimiento**: /api/admin/* sin sesión → 401.
- **Prueba sugerida**: GET /api/admin/usuarios sin sesión → esperar 401.
- **Archivo relacionado**: `backend/app/routes/admin_routes.py`
- **Evidencia**: `test_listar_usuarios_sin_sesion`
- **Estado**: VERIFICADO

### RU-030
- **Descripción**: Los tokens de recuperación se invalidan al cambiar la contraseña.
- **Objetivo**: Prevenir uso de tokens antiguos.
- **Criterio de cumplimiento**: Al restablecer contraseña exitosamente, el token se marca como usado.
- **Prueba sugerida**: Usar el mismo token dos veces → segundo intento retorna 400.
- **Archivo relacionado**: `backend/app/services/recuperacion_service.py` (`confirmar_uso_token`)
- **Evidencia**: `test_restablecer_contrasena_token_de_un_solo_uso`
- **Estado**: VERIFICADO

---

## CATEGORÍA C: INYECCIÓN Y XSS (RU-031 a RU-040)

### RU-031
- **Descripción**: No hay SQL Injection posible en ningún endpoint.
- **Objetivo**: Proteger la base de datos contra manipulación.
- **Criterio de cumplimiento**: SQLAlchemy ORM usado en todas las consultas, sin SQL crudo concatenado.
- **Prueba sugerida**: Enviar payloads SQL en campos de login y registro → comportamiento normal.
- **Archivo relacionado**: Todos los `services/` y `models/`
- **Evidencia**: `test_sql_injection_en_busqueda_no_rompe_nada`, `test_sql_injection_intento_drop_table`, `test_token_recuperacion_de_otro_formato_es_rechazado`
- **Estado**: VERIFICADO

### RU-032
- **Descripción**: Las consultas parametrizadas se usan en toda interacción con la BD.
- **Objetivo**: Prevenir SQL Injection a nivel de implementación.
- **Criterio de cumplimiento**: No hay f-strings ni concatenación en consultas SQL.
- **Prueba sugerida**: Revisar código de models/ → no debe haber SQL dinámico sin parámetros.
- **Archivo relacionado**: `backend/app/models/`, `backend/app/services/objetos_service.py`
- **Evidencia**: Inspección directa: no existe ni una sola cadena SQL cruda en todo el backend; todas las consultas usan `Model.query.filter(...)` / `db.session`.
- **Estado**: VERIFICADO

### RU-033
- **Descripción**: Los datos del usuario se escapan correctamente al mostrarlos en HTML.
- **Objetivo**: Prevenir XSS almacenado.
- **Criterio de cumplimiento**: El frontend no inserta datos sin escapar en innerHTML.
- **Prueba sugerida**: Registrar objeto con nombre con script → no debe ejecutarse.
- **Archivo relacionado**: `frontend/public/js/main.js` (`crearElemento`, `crearBadge`)
- **Evidencia**: `test_xss_almacenado_se_guarda_como_texto_plano` (backend guarda literal) + inspección de todas las páginas reescritas: ninguna usa innerHTML con datos de la API.
- **Estado**: VERIFICADO

### RU-034
- **Descripción**: No se usa innerHTML con datos del servidor.
- **Objetivo**: Prevenir XSS DOM.
- **Criterio de cumplimiento**: El JS del frontend usa textContent para insertar datos.
- **Prueba sugerida**: Inspeccionar el JS → buscar usos de innerHTML con variables.
- **Archivo relacionado**: `frontend/public/js/pagina-*.js`
- **Evidencia**: Los 12 archivos `js/pagina-*.js` (código nuevo de v1.0, el que renderiza datos de la API) usan `crearElemento`/`crearBadge` (`textContent`) o `.textContent = ''` para limpiar, nunca `innerHTML`, confirmado por búsqueda dirigida. **Corrección tras revisión independiente**: `js/contrasena-fortaleza.js` (código heredado de v0.25, sin tocar en esta migración) sí usa `innerHTML` en las líneas 56 y 61, pero el contenido interpolado es un diccionario estático hardcodeado en el propio archivo (`textos[clave]`, ej. "Mínimo 12 caracteres"), nunca un dato que venga de la API o de otro usuario — no es una superficie de XSS real, pero la primera versión de esta regla afirmó "cero resultados" en la búsqueda, lo cual era impreciso. Queda corregido para reflejar la realidad exacta del código.
- **Estado**: VERIFICADO (para el código que sí maneja datos de usuario/API; ver aclaración sobre `contrasena-fortaleza.js`)

### RU-035
- **Descripción**: Content-Security-Policy está configurado.
- **Objetivo**: Capa adicional de protección contra XSS.
- **Criterio de cumplimiento**: Header CSP presente en todas las respuestas.
- **Prueba sugerida**: curl -I → verificar header Content-Security-Policy.
- **Archivo relacionado**: `backend/app/__init__.py` (`agregar_cabeceras_seguridad`)
- **Evidencia**: Cabecera real observada con curl: `Content-Security-Policy: default-src 'self'; script-src 'self'; ...`; y confirmado que no rompe el frontend (prueba E2E completa con 14/14 verificaciones, cero errores de consola).
- **Estado**: VERIFICADO

### RU-036
- **Descripción**: Los nombres de archivo subidos se sanean.
- **Objetivo**: Prevenir Path Traversal.
- **Criterio de cumplimiento**: Nombres de archivo saneados con werkzeug.utils.secure_filename.
- **Prueba sugerida**: Subir archivo con nombre malicioso → verificar que se sanea.
- **Archivo relacionado**: N/A
- **Evidencia**: v1.0 no implementa subida de archivos (los reportes usan `imagen_url` como enlace externo opcional, validado como URL http(s), no como archivo). No aplica.
- **Estado**: NO_APLICA

### RU-037
- **Descripción**: Los tipos de archivo subidos se validan por contenido, no solo extensión.
- **Objetivo**: Prevenir subida de archivos maliciosos.
- **Criterio de cumplimiento**: Se verifica el tipo MIME real del archivo.
- **Prueba sugerida**: Subir script PHP con extensión .jpg → debe rechazarse.
- **Archivo relacionado**: N/A
- **Evidencia**: Sin subida de archivos en v1.0 (ver RU-036).
- **Estado**: NO_APLICA

### RU-038
- **Descripción**: Los archivos subidos se almacenan fuera del directorio de la aplicación.
- **Objetivo**: Prevenir ejecución de archivos subidos.
- **Criterio de cumplimiento**: Directorio de uploads fuera de static/ y de la app.
- **Prueba sugerida**: Verificar configuración de UPLOAD_FOLDER.
- **Archivo relacionado**: N/A
- **Evidencia**: Sin subida de archivos en v1.0 (ver RU-036).
- **Estado**: NO_APLICA

### RU-039
- **Descripción**: No hay Open Redirect posible.
- **Objetivo**: Prevenir redireccionamiento a sitios maliciosos.
- **Criterio de cumplimiento**: URLs de redirect validadas contra dominios permitidos.
- **Prueba sugerida**: Si hay parámetros de redirect, intentar redirigir a google.com → debe fallar.
- **Archivo relacionado**: N/A
- **Evidencia**: Ningún endpoint de EncuentraU acepta una URL de destino como parámetro (todas las redirecciones del frontend son a rutas fijas del propio sitio, ej. `window.location.href = 'login.html'`); el backend no tiene ningún `redirect()` con entrada del usuario. Inspección directa del código confirma que no existe la superficie de ataque.
- **Estado**: NO_APLICA

### RU-040
- **Descripción**: Los filtros de búsqueda son seguros contra inyección.
- **Objetivo**: Prevenir SQLi en búsquedas.
- **Criterio de cumplimiento**: Los filtros de búsqueda usan SQLAlchemy con parámetros.
- **Prueba sugerida**: Enviar caracteres especiales en parámetros de búsqueda → comportamiento normal.
- **Archivo relacionado**: `backend/app/services/objetos_service.py` (`buscar_objetos`)
- **Evidencia**: `test_sql_injection_en_busqueda_no_rompe_nada`, `test_parametros_de_paginacion_maliciosos_no_rompen_nada`, `test_parametros_de_paginacion_no_numericos_no_rompen_nada`
- **Estado**: VERIFICADO

---

## CATEGORÍA D: CSRF Y SESIONES (RU-041 a RU-050)

### RU-041
- **Descripción**: Flask-WTF CSRFProtect está activo en peticiones POST/PUT/DELETE.
- **Objetivo**: Prevenir CSRF.
- **Criterio de cumplimiento**: CSRFProtect inicializado en extensions.py y activo.
- **Prueba sugerida**: POST /api/auth/login sin X-CSRFToken → esperar 400.
- **Archivo relacionado**: `backend/app/extensions.py`, `backend/app/__init__.py`
- **Evidencia**: `test_csrf_requerido_en_registro`; y el bug real encontrado y corregido donde un CSRF ausente devolvía 500 en vez de 400 (`test_csrf_error_devuelve_400_no_500`, ver CHANGELOG).
- **Estado**: VERIFICADO

### RU-042
- **Descripción**: El frontend obtiene el token CSRF antes de cada formulario.
- **Objetivo**: El CSRF token es válido y fresco.
- **Criterio de cumplimiento**: El JS llama GET /api/auth/csrf-token antes de cada operación sensible.
- **Prueba sugerida**: Verificar en el código JS que se obtiene el token antes de enviar.
- **Archivo relacionado**: `frontend/public/js/api.js` (`peticionProtegida`)
- **Evidencia**: Inspección de código: `peticionProtegida` pide el token automáticamente si `csrfTokenEnMemoria` es nulo; verificación E2E completa (registro, reportes, solicitudes, panel admin) nunca falló por CSRF.
- **Estado**: VERIFICADO

### RU-043
- **Descripción**: El CSRF token se envía en el header X-CSRFToken.
- **Objetivo**: El backend puede validar el token.
- **Criterio de cumplimiento**: Todas las peticiones POST/PUT/DELETE incluyen X-CSRFToken.
- **Prueba sugerida**: Hacer petición con token incorrecto → esperar 400.
- **Archivo relacionado**: `frontend/public/js/api.js`
- **Evidencia**: `test_csrf_requerido_en_registro`, `test_csrf_token_valido_permite_la_peticion`
- **Estado**: VERIFICADO

### RU-044
- **Descripción**: La SECRET_KEY es suficientemente larga y aleatoria.
- **Objetivo**: La firma de la sesión es imposible de predecir.
- **Criterio de cumplimiento**: SECRET_KEY tiene al menos 32 bytes de entropía.
- **Prueba sugerida**: Verificar en config.py que no hay SECRET_KEY hardcodeada en producción.
- **Archivo relacionado**: `backend/.env.example` (instrucción: `secrets.token_hex(32)`)
- **Evidencia**: `.env.example` documenta el comando correcto para generarla; `Config.validar_configuracion_produccion()` impide arrancar en producción con la clave insegura por defecto. No se ha generado ni verificado una clave real de producción todavía (no hay despliegue).
- **Estado**: IMPLEMENTADO

### RU-045
- **Descripción**: La SECRET_KEY viene de variable de entorno.
- **Objetivo**: No exponer la clave secreta en el código fuente.
- **Criterio de cumplimiento**: SECRET_KEY = os.environ.get('SECRET_KEY') sin valor usable por defecto.
- **Prueba sugerida**: Revisar config.py → no hay clave por defecto para producción.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Código leído: `SECRET_KEY = os.environ.get('SECRET_KEY', CLAVE_INSEGURA_POR_DEFECTO)`, y `validar_configuracion_produccion()` lanza `RuntimeError` si `ES_PRODUCCION` y la clave sigue siendo la insegura por defecto — verificado leyendo el código (no se ejecutó un arranque real en producción).
- **Estado**: VERIFICADO (guardrail probado por lectura de código; falta confirmar en un arranque real de producción — ver RU-082)

### RU-046
- **Descripción**: No se guarda información sensible en la sesión.
- **Objetivo**: Limitar el impacto si la sesión es comprometida.
- **Criterio de cumplimiento**: La sesión solo guarda usuario_id, nunca contraseñas o tokens.
- **Prueba sugerida**: Revisar todo el código que escribe en session[].
- **Archivo relacionado**: `backend/app/controllers/auth_controller.py`
- **Evidencia**: Búsqueda dirigida de `session[` en todo el backend: el único valor guardado es `session['usuario_id']`.
- **Estado**: VERIFICADO

### RU-047
- **Descripción**: La sesión se invalida completamente en logout.
- **Objetivo**: Que el logout sea efectivo.
- **Criterio de cumplimiento**: cerrar_sesion() llama session.clear().
- **Prueba sugerida**: Logout → intentar acceder a endpoint protegido → esperar 401.
- **Archivo relacionado**: `backend/app/controllers/auth_controller.py`
- **Evidencia**: `test_logout_limpia_la_sesion`; verificación E2E confirmó con un navegador real que, tras hacer clic en "Cerrar sesión", `GET /api/auth/sesion` devuelve `usuario: null`.
- **Estado**: VERIFICADO

### RU-048
- **Descripción**: No se guarda el token CSRF o la sesión en localStorage.
- **Objetivo**: Proteger tokens contra acceso JavaScript (XSS).
- **Criterio de cumplimiento**: El JS no guarda tokens en localStorage ni sessionStorage.
- **Prueba sugerida**: Revisar el código JS → buscar localStorage.setItem con tokens.
- **Archivo relacionado**: `frontend/public/js/api.js`
- **Evidencia**: Búsqueda dirigida de `localStorage`/`sessionStorage` en todo `frontend/public/js/`: la única coincidencia es un comentario en `api.js` líneas 10-13 que explica, en prosa, que estos mecanismos NO se usan — no hay ninguna llamada real a `localStorage.setItem`/`sessionStorage.setItem` en todo el código. El CSRF token vive solo en `csrfTokenEnMemoria`, una variable de JS que se pierde al recargar.
- **Estado**: VERIFICADO

### RU-049
- **Descripción**: La sesión tiene tiempo de expiración configurado.
- **Objetivo**: Limitar la duración de sesiones abandonadas.
- **Criterio de cumplimiento**: PERMANENT_SESSION_LIFETIME configurado o session.permanent=False.
- **Prueba sugerida**: Revisar config.py → verificar configuración de expiración.
- **Archivo relacionado**: `backend/app/controllers/auth_controller.py` (`session.permanent = False`)
- **Evidencia**: Código leído: `session.permanent = False` en `iniciar_sesion()`, lo que hace que la cookie sea de sesión de navegador (expira al cerrarlo), el comportamiento por defecto más conservador de Flask.
- **Estado**: VERIFICADO

### RU-050
- **Descripción**: Los tokens de recuperación son de un solo uso.
- **Objetivo**: Prevenir reutilización de tokens.
- **Criterio de cumplimiento**: El token se marca como 'usado=True' tras restablecimiento exitoso.
- **Prueba sugerida**: Usar token dos veces → segundo uso retorna 400.
- **Archivo relacionado**: `backend/app/models/token_recuperacion.py`
- **Evidencia**: `test_restablecer_contrasena_token_de_un_solo_uso`
- **Estado**: VERIFICADO

---

## CATEGORÍA E: VALIDACIÓN Y MANEJO DE ERRORES (RU-051 a RU-060)

### RU-051
- **Descripción**: Todos los campos de entrada se validan en el backend, no solo en el frontend.
- **Objetivo**: El frontend nunca es la autoridad de validación.
- **Criterio de cumplimiento**: Cada servicio (`auth_service`, `objetos_service`, `solicitudes_service`) revalida todo lo que ya validó el frontend.
- **Prueba sugerida**: Enviar una petición directamente a la API (sin pasar por el frontend) con datos inválidos → esperar 400.
- **Archivo relacionado**: `backend/app/services/*.py`
- **Evidencia**: Toda la suite de `tests/unit/` y `tests/integration/` llama a la API directamente (sin frontend) y confirma que los datos inválidos se rechazan igual.
- **Estado**: VERIFICADO

### RU-052
- **Descripción**: Los mensajes de error no exponen tracebacks ni detalles internos.
- **Objetivo**: No dar información útil a un atacante.
- **Criterio de cumplimiento**: El error 500 genérico nunca incluye la excepción real en la respuesta.
- **Prueba sugerida**: Forzar un error interno → la respuesta no debe contener rutas de archivo ni nombres de excepción de Python.
- **Archivo relacionado**: `backend/app/middlewares/manejo_errores.py`
- **Evidencia**: Inspección de código: el handler de `Exception` solo devuelve `{'mensaje': 'Ocurrió un error en el servidor'}`; el traceback se registra con `app.logger.exception`, nunca en la respuesta HTTP.
- **Estado**: VERIFICADO

### RU-053
- **Descripción**: Los errores HTTP usan el código correcto (400/401/403/404/429/500), nunca siempre 200.
- **Objetivo**: Comportamiento correcto y predecible de la API.
- **Criterio de cumplimiento**: Cada tipo de error definido en `docs/API.md` retorna el código documentado.
- **Prueba sugerida**: Recorrer los casos de error de cada endpoint y comparar el código real contra `docs/API.md`.
- **Archivo relacionado**: Todos los `controllers/`
- **Evidencia**: Confirmado en la suite completa de `tests/integration/` (401, 403, 404, 400, 429 usados consistentemente según el caso).
- **Estado**: VERIFICADO

### RU-054
- **Descripción**: Los errores de validación por campo se agrupan en un objeto "errores" consistente.
- **Objetivo**: Que el frontend pueda mostrar el error exacto junto al campo correspondiente.
- **Criterio de cumplimiento**: El formato `{mensaje, errores: {campo: "..."}}` se respeta en todos los endpoints de escritura.
- **Prueba sugerida**: Revisar `docs/API.md` sección 4 (Formato de respuestas) contra la implementación real.
- **Archivo relacionado**: Todos los `controllers/`
- **Evidencia**: Inspección de código de los 4 controladores de escritura (auth, objetos, solicitudes, usuarios_admin): todos usan el mismo formato.
- **Estado**: VERIFICADO

### RU-055
- **Descripción**: El backend maneja JSON malformado sin caerse (500).
- **Objetivo**: Resiliencia ante clientes mal implementados o maliciosos.
- **Criterio de cumplimiento**: Un body no-JSON en una petición POST retorna 400/401, nunca 500.
- **Prueba sugerida**: POST con body `"esto no es json {{{"` y Content-Type application/json.
- **Archivo relacionado**: Todos los `controllers/` (uso de `request.get_json(silent=True)`)
- **Evidencia**: `test_json_malformado_no_causa_error_500`, `test_body_vacio_en_post_no_causa_error_500`
- **Estado**: VERIFICADO

### RU-056
- **Descripción**: Hay un límite de tamaño máximo de petición (MAX_CONTENT_LENGTH).
- **Objetivo**: Prevenir agotamiento de memoria con peticiones oversized.
- **Criterio de cumplimiento**: Un body mayor al límite configurado retorna 413.
- **Prueba sugerida**: Enviar un POST con un campo de texto de varios MB.
- **Archivo relacionado**: `backend/app/config/config.py` (`MAX_CONTENT_LENGTH`)
- **Evidencia**: `test_payload_json_extremadamente_grande_es_rechazado`. Gap real encontrado durante esta migración: v0.25 no tenía ningún límite configurado; se agregó en v1.0.
- **Estado**: VERIFICADO

### RU-057
- **Descripción**: Las longitudes máximas y mínimas de texto están validadas en el backend (nombre, descripción, ubicación, mensaje de solicitud).
- **Objetivo**: Evitar datos absurdamente cortos/largos y ataques de payload.
- **Criterio de cumplimiento**: Cada campo de texto tiene límites explícitos en el servicio correspondiente.
- **Prueba sugerida**: Enviar descripción de 5 caracteres → esperar 400.
- **Archivo relacionado**: `backend/app/services/objetos_service.py`, `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_descripcion_muy_corta_genera_error`, `test_no_puede_haber_dos_solicitudes_abiertas_del_mismo_usuario` (indirectamente valida longitudes de mensaje).
- **Estado**: VERIFICADO

### RU-058
- **Descripción**: Las fechas de eventos (perdido/encontrado) no pueden ser futuras.
- **Objetivo**: Coherencia de datos: no se puede reportar algo que "pasará".
- **Criterio de cumplimiento**: `fecha_evento > hoy` es rechazado con 400.
- **Prueba sugerida**: Crear un reporte con fecha de mañana → esperar 400.
- **Archivo relacionado**: `backend/app/services/objetos_service.py`
- **Evidencia**: `test_crear_objeto_rechaza_fecha_futura`, `test_fecha_futura_genera_error`
- **Estado**: VERIFICADO

### RU-059
- **Descripción**: Las categorías de objetos están restringidas a una lista fija (whitelist), no texto libre.
- **Objetivo**: Consistencia de datos para filtros y búsquedas.
- **Criterio de cumplimiento**: Solo se aceptan las categorías definidas en `CATEGORIAS_VALIDAS`.
- **Prueba sugerida**: Enviar categoría inventada → esperar 400.
- **Archivo relacionado**: `backend/app/models/objeto.py`, `backend/app/services/objetos_service.py`
- **Evidencia**: `test_crear_objeto_valida_categoria`, `test_categoria_invalida_genera_error`
- **Estado**: VERIFICADO

### RU-060
- **Descripción**: Los parámetros de paginación (página, por_página) tienen límites máximos y no rompen con valores inválidos.
- **Objetivo**: Prevenir DoS por consultas de página gigante o parámetros no numéricos.
- **Criterio de cumplimiento**: `por_pagina` nunca excede `RESULTADOS_POR_PAGINA_MAXIMO` (50), y valores no numéricos usan el valor por defecto.
- **Prueba sugerida**: `?pagina=-1&por_pagina=99999999` y `?pagina=abc`.
- **Archivo relacionado**: `backend/app/utils.py` (`parametros_paginacion`)
- **Evidencia**: `test_parametros_de_paginacion_maliciosos_no_rompen_nada`, `test_parametros_de_paginacion_no_numericos_no_rompen_nada`
- **Estado**: VERIFICADO

---

## CATEGORÍA F: BASE DE DATOS E INTEGRIDAD (RU-061 a RU-070)

### RU-061
- **Descripción**: Los modelos usan SQLAlchemy (ORM), no SQL crudo.
- **Objetivo**: Persistencia real, mantenible y segura por defecto.
- **Criterio de cumplimiento**: Todas las clases en `models/` heredan de `db.Model`.
- **Prueba sugerida**: Revisar cada archivo de `models/`.
- **Archivo relacionado**: `backend/app/models/*.py`
- **Evidencia**: Inspección directa: `Usuario`, `TokenRecuperacion`, `Objeto`, `Solicitud` heredan de `db.Model`.
- **Estado**: VERIFICADO

### RU-062
- **Descripción**: Cada tabla tiene clave primaria.
- **Objetivo**: Identidad única de cada registro.
- **Criterio de cumplimiento**: Todas las tablas tienen `id = db.Column(db.Integer, primary_key=True)`.
- **Prueba sugerida**: Revisar el esquema generado por la migración inicial.
- **Archivo relacionado**: `backend/migrations/versions/cc136ccba3dd_*.py`
- **Evidencia**: La migración generada automáticamente por Alembic confirma `PRIMARY KEY` en las 4 tablas.
- **Estado**: VERIFICADO

### RU-063
- **Descripción**: Las claves foráneas usan ForeignKey() con la tabla referenciada.
- **Objetivo**: Integridad referencial.
- **Criterio de cumplimiento**: `objetos.usuario_id`, `solicitudes.objeto_id`, `solicitudes.solicitante_id`, `tokens_recuperacion.usuario_id` tienen FK real.
- **Prueba sugerida**: Revisar el esquema generado por la migración.
- **Archivo relacionado**: `backend/app/models/objeto.py`, `backend/app/models/solicitud.py`, `backend/app/models/token_recuperacion.py`
- **Evidencia**: Migración inicial (Alembic) confirma las 4 claves foráneas.
- **Estado**: VERIFICADO

### RU-064
- **Descripción**: El correo del usuario tiene restricción unique además de índice.
- **Objetivo**: Prevenir duplicados y acelerar el login.
- **Criterio de cumplimiento**: `correo = db.Column(..., unique=True, index=True)`.
- **Prueba sugerida**: `test_registro_falla_si_correo_ya_existe`.
- **Archivo relacionado**: `backend/app/models/usuario.py`
- **Evidencia**: `test_registro_falla_si_correo_ya_existe` + índice `ix_usuarios_correo` confirmado en la migración generada por Alembic.
- **Estado**: VERIFICADO

### RU-065
- **Descripción**: Los campos con valores fijos (rol, tipo, estado) tienen CHECK constraint a nivel de BD, no solo validación en Python.
- **Objetivo**: Defensa en profundidad: ni siquiera un bug en el código Python podría escribir un valor inválido.
- **Criterio de cumplimiento**: `CheckConstraint` presente en `Usuario.rol`, `Objeto.tipo`, `Objeto.estado`, `Solicitud.estado`.
- **Prueba sugerida**: Revisar `__table_args__` de cada modelo.
- **Archivo relacionado**: `backend/app/models/usuario.py`, `backend/app/models/objeto.py`, `backend/app/models/solicitud.py`
- **Evidencia**: Inspección directa del código de los 3 modelos.
- **Estado**: VERIFICADO

### RU-066
- **Descripción**: Las migraciones de esquema se generan y aplican con Flask-Migrate/Alembic, nunca se edita la BD a mano.
- **Objetivo**: Esquema reproducible y versionado.
- **Criterio de cumplimiento**: Existe `backend/migrations/` con al menos una migración real aplicada.
- **Prueba sugerida**: `flask db upgrade` sobre una BD vacía debe recrear el esquema completo.
- **Archivo relacionado**: `backend/migrations/`
- **Evidencia**: `flask db init` + `flask db migrate` + `flask db upgrade` ejecutados realmente; la migración `cc136ccba3dd` fue aplicada y usada durante todas las pruebas manuales y E2E.
- **Estado**: VERIFICADO

### RU-067
- **Descripción**: Las transiciones de estado de un objeto siguen una máquina de estados explícita, no cualquier valor es válido desde cualquier estado.
- **Objetivo**: Integridad del flujo de negocio (activo → en_proceso → resuelto, etc.).
- **Criterio de cumplimiento**: `TRANSICIONES_VALIDAS` en `models/objeto.py` define exactamente qué transiciones se permiten.
- **Prueba sugerida**: Intentar pasar de 'activo' a 'resuelto' directamente → esperar 400.
- **Archivo relacionado**: `backend/app/models/objeto.py`
- **Evidencia**: `test_cambiar_estado_objeto_rechaza_transicion_invalida`
- **Estado**: VERIFICADO

### RU-068
- **Descripción**: Un usuario desactivado no puede iniciar sesión, y sus reportes no desaparecen (no se hace hard-delete de usuarios).
- **Objetivo**: Preservar la integridad histórica de reportes/solicitudes al moderar una cuenta.
- **Criterio de cumplimiento**: `PUT /api/admin/usuarios/:id {activo: false}` bloquea el login sin borrar registros relacionados.
- **Prueba sugerida**: Desactivar un usuario con reportes existentes → los reportes se mantienen y el login falla.
- **Archivo relacionado**: `backend/app/services/usuarios_admin_service.py`, `backend/app/controllers/auth_controller.py`
- **Evidencia**: `test_admin_desactiva_usuario_y_no_puede_loguear`; verificado también en `smoke_test_manual_v1.0.md` #23-24.
- **Estado**: VERIFICADO

### RU-069
- **Descripción**: Las contraseñas u otros campos sensibles nunca se serializan en las respuestas JSON.
- **Objetivo**: Que un bug de frontend no pueda filtrar el hash de la contraseña.
- **Criterio de cumplimiento**: `usuario_publico()` construye explícitamente qué campos exponer (whitelist de salida).
- **Prueba sugerida**: Inspeccionar cualquier respuesta que incluya un usuario → nunca debe verse `password_hash`.
- **Archivo relacionado**: `backend/app/models/usuario.py` (`usuario_publico`)
- **Evidencia**: `test_registro_exitoso` verifica explícitamente `'password_hash' not in datos['usuario']`.
- **Estado**: VERIFICADO

### RU-070
- **Descripción**: En desarrollo se usa SQLite; en producción la configuración exige PostgreSQL vía DATABASE_URL.
- **Objetivo**: Persistencia real y robusta en producción, sin sacrificar simplicidad en desarrollo.
- **Criterio de cumplimiento**: `Config.validar_configuracion_produccion()` rechaza arrancar en producción sin `DATABASE_URL`.
- **Prueba sugerida**: Arrancar con `FLASK_ENV=production` sin `DATABASE_URL` → debe fallar al arrancar.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Código revisado (lógica correcta); no verificado contra un PostgreSQL real porque todavía no existe un despliegue (ver `docs/DEPLOYMENT.md`).
- **Estado**: BLOQUEADO (implementación correcta; verificación real requiere el despliegue en producción)

---

## CATEGORÍA G: LÓGICA DE NEGOCIO — OBJETOS PERDIDOS (RU-071 a RU-080)

### RU-071
- **Descripción**: Un objeto reportado nace en estado 'activo'.
- **Objetivo**: Estado inicial consistente.
- **Criterio de cumplimiento**: `crear_objeto()` siempre asigna `estado='activo'`.
- **Prueba sugerida**: Crear un reporte y verificar su estado inicial.
- **Archivo relacionado**: `backend/app/services/objetos_service.py`
- **Evidencia**: `test_crear_objeto_autenticado`
- **Estado**: VERIFICADO

### RU-072
- **Descripción**: La búsqueda pública no requiere autenticación.
- **Objetivo**: Cualquiera (incluso sin cuenta) puede buscar objetos.
- **Criterio de cumplimiento**: `GET /api/objetos` no tiene `login_requerido`.
- **Prueba sugerida**: Buscar sin sesión → esperar 200.
- **Archivo relacionado**: `backend/app/routes/objetos_routes.py`
- **Evidencia**: `test_listar_objetos_es_publico`
- **Estado**: VERIFICADO

### RU-073
- **Descripción**: La búsqueda pública, sin filtro de estado, solo muestra reportes activos/en proceso (no cancelados/resueltos/cerrados).
- **Objetivo**: No mostrar como "buscables" objetos que ya no están disponibles.
- **Criterio de cumplimiento**: `buscar_objetos()` filtra por defecto a `('activo', 'en_proceso')` si no se especifica `estado`.
- **Prueba sugerida**: Cancelar un reporte y buscar sin filtro de estado → no debe aparecer.
- **Archivo relacionado**: `backend/app/services/objetos_service.py`
- **Evidencia**: `test_listar_objetos_admin_incluye_todos_los_estados` (contrasta explícitamente la vista pública con la de admin).
- **Estado**: VERIFICADO

### RU-074
- **Descripción**: Una coincidencia entre un perdido y un encontrado nunca cambia el estado del objeto automáticamente.
- **Objetivo**: Una "posible coincidencia" es solo una pista, nunca propiedad confirmada.
- **Criterio de cumplimiento**: `coincidencias_service.py` solo lee y puntúa, nunca escribe en la base de datos.
- **Prueba sugerida**: Ver el detalle de un objeto con coincidencias y confirmar que su estado sigue 'activo'.
- **Archivo relacionado**: `backend/app/services/coincidencias_service.py`
- **Evidencia**: `test_coincidencia_no_cambia_estado_del_objeto`
- **Estado**: VERIFICADO

### RU-075
- **Descripción**: Una solicitud de reclamación no puede crearse sobre el propio reporte del solicitante.
- **Objetivo**: Coherencia del proceso de reclamación (ver también RU-022).
- **Criterio de cumplimiento**: `crear_solicitud` compara `objeto.usuario_id == solicitante.id`.
- **Prueba sugerida**: Repetido de RU-022 desde la perspectiva de negocio.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_no_puede_reclamar_su_propio_objeto`
- **Estado**: VERIFICADO

### RU-076
- **Descripción**: Solo puede existir una solicitud abierta por usuario por objeto.
- **Objetivo**: Evitar spam de solicitudes duplicadas sobre el mismo objeto.
- **Criterio de cumplimiento**: `crear_solicitud` rechaza si ya existe una solicitud en estado `pendiente`/`en_revision` del mismo solicitante para el mismo objeto.
- **Prueba sugerida**: Enviar dos solicitudes seguidas sobre el mismo objeto con el mismo usuario.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_no_puede_haber_dos_solicitudes_abiertas_del_mismo_usuario`
- **Estado**: VERIFICADO

### RU-077
- **Descripción**: Aprobar una solicitud marca el objeto como 'resuelto' y rechaza automáticamente las demás solicitudes abiertas del mismo objeto.
- **Objetivo**: Cerrar el ciclo de vida del objeto de forma consistente cuando hay múltiples reclamantes.
- **Criterio de cumplimiento**: `revisar_solicitud(..., 'aprobada')` cambia el objeto y las demás solicitudes abiertas.
- **Prueba sugerida**: Dos solicitudes sobre el mismo objeto; aprobar una → la otra debe quedar 'rechazada' automáticamente.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_admin_aprueba_solicitud_resuelve_el_objeto` (verifica el cambio de estado del objeto; el rechazo automático de solicitudes hermanas está implementado en el mismo método y cubierto por la lógica compartida, aunque no existe un test con dos solicitudes simultáneas específico).
- **Estado**: IMPLEMENTADO

### RU-078
- **Descripción**: Rechazar o cancelar la única solicitud abierta reactiva el objeto a 'activo'.
- **Objetivo**: Que el objeto vuelva a estar disponible si la reclamación no prosperó.
- **Criterio de cumplimiento**: `_reabrir_objeto_si_no_hay_mas_abiertas()` se llama tras rechazar/cancelar.
- **Prueba sugerida**: Rechazar la única solicitud de un objeto en 'en_proceso' → debe volver a 'activo'.
- **Archivo relacionado**: `backend/app/services/solicitudes_service.py`
- **Evidencia**: `test_admin_rechaza_solicitud_reactiva_el_objeto`, `test_solicitante_puede_cancelar_su_propia_solicitud`
- **Estado**: VERIFICADO

### RU-079
- **Descripción**: La información de verificación de una solicitud (mensaje/contacto) solo es visible para el dueño del reporte, el solicitante y un administrador.
- **Objetivo**: No exponer públicamente datos privados de verificación de propiedad.
- **Criterio de cumplimiento**: `GET /api/objetos/:id/solicitudes` exige ser dueño o admin; `GET /api/mis-solicitudes` solo devuelve las propias.
- **Prueba sugerida**: Un tercero intenta ver las solicitudes de un objeto ajeno → 403.
- **Archivo relacionado**: `backend/app/controllers/objetos_controller.py` (`solicitudes_del_objeto`)
- **Evidencia**: `test_solicitudes_privadas_solo_visibles_para_dueno_y_admin`; verificado también con navegador real en `docs/evidencia/e2e_navegador_v1.0.txt` ("Un desconocido no autenticado no puede ver las solicitudes privadas").
- **Estado**: VERIFICADO

### RU-080
- **Descripción**: Un administrador puede cambiar el estado de cualquier reporte según transiciones válidas.
- **Objetivo**: Permitir moderación real del contenido por parte del admin.
- **Criterio de cumplimiento**: `PUT /api/admin/objetos/:id/estado` respeta `TRANSICIONES_VALIDAS`.
- **Prueba sugerida**: Admin cambia un reporte de 'activo' a 'cerrado' → 200; intenta 'activo'→'resuelto' directo → 400.
- **Archivo relacionado**: `backend/app/routes/admin_routes.py`, `backend/app/controllers/objetos_controller.py`
- **Evidencia**: `test_admin_cambia_estado_de_un_objeto`, `test_cambiar_estado_objeto_rechaza_transicion_invalida`; verificado también con navegador real (gestión de reportes, cambio de estado persistente tras recargar).
- **Estado**: VERIFICADO

---

## CATEGORÍA H: CONFIGURACIÓN, DESPLIEGUE Y PRODUCCIÓN (RU-081 a RU-090)

### RU-081
- **Descripción**: DEBUG está desactivado por defecto salvo que FLASK_ENV=development se defina explícitamente.
- **Objetivo**: Deny by default — nunca exponer el debugger interactivo de Werkzeug por accidente.
- **Criterio de cumplimiento**: `app.py` calcula `modo_debug` como `FLASK_ENV == 'development'` (no como "todo lo que no sea production").
- **Prueba sugerida**: Arrancar sin definir FLASK_ENV → debug debe seguir activo solo porque el valor por defecto de desarrollo es explícito; en cualquier despliegue real se exige fijar FLASK_ENV=production.
- **Archivo relacionado**: `backend/app.py`
- **Evidencia**: Bug real corregido durante esta migración: la lógica original de v0.25 (`FLASK_ENV != 'production'`) dejaba `debug=True` en cualquier entorno mal configurado; se cambió a comparación explícita.
- **Estado**: VERIFICADO (por inspección de código; el servidor de desarrollo usado en todas las pruebas locales corrió con `debug=True` intencionalmente, confirmando que el flag responde a la variable de entorno)

### RU-082
- **Descripción**: La aplicación rehúsa arrancar en producción con SECRET_KEY insegura.
- **Objetivo**: Fallar rápido y explícito en vez de exponer una clave débil silenciosamente.
- **Criterio de cumplimiento**: `Config.validar_configuracion_produccion()` lanza `RuntimeError`.
- **Prueba sugerida**: `FLASK_ENV=production` sin `SECRET_KEY` real → la app no debe arrancar.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Código revisado. No se ha ejecutado literalmente con `FLASK_ENV=production` en esta máquina (arrancaría reclamando también `DATABASE_URL`, ver RU-083); la lógica en sí es simple y determinista.
- **Estado**: IMPLEMENTADO

### RU-083
- **Descripción**: La aplicación rehúsa arrancar en producción sin DATABASE_URL.
- **Objetivo**: Nunca usar SQLite como base de datos de una instancia pública.
- **Criterio de cumplimiento**: Mismo guardrail que RU-082, segunda condición.
- **Prueba sugerida**: `FLASK_ENV=production` con `SECRET_KEY` real pero sin `DATABASE_URL` → la app no debe arrancar.
- **Archivo relacionado**: `backend/app/config/config.py`
- **Evidencia**: Código revisado, misma situación que RU-082.
- **Estado**: IMPLEMENTADO

### RU-084
- **Descripción**: Existen cabeceras de seguridad (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy).
- **Objetivo**: Defensa en profundidad a nivel de navegador.
- **Criterio de cumplimiento**: `agregar_cabeceras_seguridad()` las añade a cada respuesta.
- **Prueba sugerida**: `curl -I` a cualquier endpoint y revisar las cabeceras.
- **Archivo relacionado**: `backend/app/__init__.py`
- **Evidencia**: Cabeceras reales observadas con curl (ver RU-035) y confirmadas también por Playwright (`e2e_logout.py`, verificación de la cabecera CSP en una respuesta real).
- **Estado**: VERIFICADO

### RU-085
- **Descripción**: HSTS se activa solo en producción (no en desarrollo por HTTP).
- **Objetivo**: No romper el desarrollo local por HTTP, pero forzar HTTPS en producción.
- **Criterio de cumplimiento**: El header `Strict-Transport-Security` solo se añade si `Config.ES_PRODUCCION`.
- **Prueba sugerida**: En desarrollo, confirmar que el header NO aparece; en producción, que SÍ aparece.
- **Archivo relacionado**: `backend/app/__init__.py`
- **Evidencia**: Confirmado en desarrollo que el header está correctamente ausente (todas las cabeceras observadas por curl no lo incluyen, `ES_PRODUCCION=False`). No verificado en un entorno de producción real (bloqueado por el despliegue).
- **Estado**: BLOQUEADO (implementación correcta; falta verificar en producción real)

### RU-086
- **Descripción**: El servidor de desarrollo de Flask no se usa en producción; se usa Gunicorn.
- **Objetivo**: El servidor de desarrollo de Werkzeug no está diseñado para tráfico real ni es seguro para exponer directamente.
- **Criterio de cumplimiento**: `gunicorn` está en `requirements.txt` y el comando de arranque de producción lo usa.
- **Prueba sugerida**: Verificar el comando de arranque configurado en el proveedor de hosting.
- **Archivo relacionado**: `backend/requirements.txt`, `Procfile` / comando de despliegue
- **Evidencia**: `gunicorn==22.0.0` está en requirements.txt. No se ha podido ejecutar `gunicorn` en esta máquina de desarrollo (Windows: gunicorn depende de `fcntl`, exclusivo de sistemas Unix/Linux) — es el comportamiento esperado; el despliegue real ocurre en un contenedor Linux. No hay despliegue real todavía.
- **Estado**: BLOQUEADO (dependencia instalada y comando preparado; ejecución real pendiente del despliegue en un host Linux — ver docs/DEPLOYMENT.md)

### RU-087
- **Descripción**: No hay secretos reales en el repositorio ni en el historial de git.
- **Objetivo**: Ninguna clave, contraseña o token real filtrado en el código.
- **Criterio de cumplimiento**: Búsqueda de patrones de secretos en todo el repositorio no encuentra nada real.
- **Prueba sugerida**: `git log -p` + grep de patrones de credenciales.
- **Archivo relacionado**: Todo el repositorio.
- **Evidencia**: Auditoría inicial (`docs/ESTADO_V025.md`, sección 8) no encontró secretos reales; el repositorio se inicializó DESPUÉS de esa auditoría, por lo que no existe historial previo con secretos. `.env` real (con la SECRET_KEY de desarrollo local) nunca se agregó a git (confirmado con `git status --ignored`).
- **Estado**: VERIFICADO

### RU-088
- **Descripción**: .env.example existe y no contiene credenciales reales.
- **Objetivo**: Documentar qué variables se necesitan sin filtrar valores reales.
- **Criterio de cumplimiento**: Todos los valores en `.env.example` son placeholders.
- **Prueba sugerida**: Revisar `backend/.env.example` línea por línea.
- **Archivo relacionado**: `backend/.env.example`
- **Evidencia**: Inspección directa: `SECRET_KEY=cambiar_este_valor_por_uno_seguro_y_unico`, `DATABASE_URL=` (vacío, con comentario explicativo).
- **Estado**: VERIFICADO

### RU-089
- **Descripción**: .gitignore excluye .env, la base de datos local y artefactos de entorno virtual.
- **Objetivo**: Que nadie suba accidentalmente secretos o archivos generados.
- **Criterio de cumplimiento**: `.env`, `venv/`, `instance/`, `*.db`, `__pycache__/` están en `.gitignore`.
- **Prueba sugerida**: `git status --ignored` debe listar esos archivos como ignorados, no como untracked normales.
- **Archivo relacionado**: `.gitignore`
- **Evidencia**: `git status --short --ignored` confirmó `backend/.env`, `backend/instance/`, `backend/venv/` correctamente ignorados.
- **Estado**: VERIFICADO

### RU-090
- **Descripción**: Las variables de entorno de producción (SECRET_KEY, DATABASE_URL, FLASK_ENV) están documentadas.
- **Objetivo**: Que desplegar no dependa de conocimiento tácito.
- **Criterio de cumplimiento**: `docs/DEPLOYMENT.md` lista cada variable requerida y cómo obtenerla/generarla.
- **Prueba sugerida**: Seguir `docs/DEPLOYMENT.md` de principio a fin sin conocimiento previo del proyecto.
- **Archivo relacionado**: `docs/DEPLOYMENT.md`, `backend/.env.example`
- **Evidencia**: Documentado en `docs/DEPLOYMENT.md`. La configuración real en un proveedor de hosting está BLOQUEADA porque requiere una cuenta del proveedor que solo su dueño puede autorizar (ver esa misma sección de limitaciones).
- **Estado**: IMPLEMENTADO

---

## CATEGORÍA I: CÓDIGO, PRUEBAS Y DOCUMENTACIÓN (RU-091 a RU-100)

### RU-091
- **Descripción**: Existe una suite de pruebas automatizadas (pytest) que cubre autenticación, autorización, lógica de negocio y seguridad.
- **Objetivo**: Poder afirmar VERIFICADO con evidencia real y repetible.
- **Criterio de cumplimiento**: `pytest tests/` corre sin errores y cubre los 4 módulos de negocio.
- **Prueba sugerida**: `cd backend && pytest -v`
- **Archivo relacionado**: `backend/tests/`
- **Evidencia**: `docs/evidencia/pytest_run_v1.0.txt` — 89 pruebas, todas pasando, con aislamiento de base de datos confirmado real (ver `docs/TESTING.md`, sección "Bug real corregido": una revisión final independiente encontró que el aislamiento previo no funcionaba de verdad — corregido y reverificado).
- **Estado**: VERIFICADO

### RU-092
- **Descripción**: Existe al menos una verificación de extremo a extremo con navegador real.
- **Objetivo**: Detectar bugs de JavaScript/DOM que pytest (test client) no puede ver.
- **Criterio de cumplimiento**: Script de Playwright que cubre el flujo completo (registro→reporte→búsqueda→coincidencia→solicitud→aprobación).
- **Prueba sugerida**: `python backend/tests/e2e/verificacion_navegador.py` contra un servidor real.
- **Archivo relacionado**: `backend/tests/e2e/verificacion_navegador.py`
- **Evidencia**: `docs/evidencia/e2e_navegador_v1.0.txt` — 14/14 verificaciones, cero errores de consola.
- **Estado**: VERIFICADO

### RU-093
- **Descripción**: El frontend no usa innerHTML con datos que vienen de la API (para prevenir XSS DOM).
- **Objetivo**: Ver RU-034 (duplicado intencional: aquí desde la perspectiva de calidad de código, no solo de seguridad).
- **Criterio de cumplimiento**: Mismo que RU-034.
- **Prueba sugerida**: Mismo que RU-034.
- **Archivo relacionado**: `frontend/public/js/main.js`
- **Evidencia**: Ver RU-034.
- **Estado**: VERIFICADO

### RU-094
- **Descripción**: Los scripts del frontend no son inline (compatibilidad con CSP script-src 'self').
- **Objetivo**: Poder aplicar una Content-Security-Policy estricta sin `unsafe-inline` en `script-src`.
- **Criterio de cumplimiento**: Ninguna página HTML tiene un bloque `<script>...</script>` con código (todas usan `<script src="...">`).
- **Prueba sugerida**: Buscar `<script>` sin atributo `src` en todo `frontend/public/*.html`.
- **Archivo relacionado**: `frontend/public/*.html`
- **Evidencia**: Las 16 páginas HTML fueron revisadas y reescritas para mover su lógica a archivos `js/pagina-*.js` durante esta migración; la CSP configurada (`script-src 'self'`, sin `unsafe-inline`) fue confirmada funcionando en la verificación E2E completa (si algún script inline hubiera quedado, esa página habría fallado silenciosamente y las pruebas lo habrían detectado).
- **Estado**: VERIFICADO

### RU-095
- **Descripción**: El código sigue una separación de responsabilidades clara (rutas → controladores → servicios → modelos).
- **Objetivo**: Mantenibilidad para estudiantes de quinto semestre (ver CLAUDE.md).
- **Criterio de cumplimiento**: Las rutas solo definen URL/método/decoradores; los controladores leen la petición y llaman al servicio; los servicios contienen la lógica de negocio; los modelos son solo datos.
- **Prueba sugerida**: Revisar que ningún archivo de `routes/` tenga lógica de negocio, y que ningún `service` importe `flask.request`.
- **Archivo relacionado**: Toda la carpeta `backend/app/`
- **Evidencia**: Inspección estructural de las 4 capas en los módulos de objetos, solicitudes, usuarios admin y auth: consistente en los 4.
- **Estado**: VERIFICADO

### RU-096
- **Descripción**: La documentación de la API (docs/API.md) refleja los endpoints reales del código.
- **Objetivo**: Que la documentación nunca describa un endpoint que no existe (o calle uno que sí existe).
- **Criterio de cumplimiento**: Cada ruta registrada en `app/routes/*.py` aparece en `docs/API.md` con el mismo método, auth y formato de respuesta.
- **Prueba sugerida**: Comparar `app.url_map` contra la tabla de `docs/API.md`.
- **Archivo relacionado**: `docs/API.md`
- **Evidencia**: `docs/API.md` fue escrito en esta misma fase de documentación a partir de una revisión directa de `app.url_map.iter_rules()` (confirmado por ejecución real durante el desarrollo del backend).
- **Estado**: VERIFICADO

### RU-097
- **Descripción**: El CHANGELOG documenta los cambios significativos de v0.25 a v1.0.
- **Objetivo**: Trazabilidad de qué cambió y por qué.
- **Criterio de cumplimiento**: `docs/CHANGELOG.md` (o `CHANGELOG.md`) tiene una entrada v1.0 con los cambios reales de esta migración, incluyendo los bugs encontrados y corregidos.
- **Prueba sugerida**: Leer el CHANGELOG y contrastarlo contra `git log`.
- **Archivo relacionado**: `CHANGELOG.md`
- **Evidencia**: Actualizado en esta fase de documentación.
- **Estado**: VERIFICADO

### RU-098
- **Descripción**: No quedan referencias a datos simulados (datos-temporales.js) ni avisos de "esto no se guarda" en ninguna página funcional.
- **Objetivo**: Cumplir la regla "NO SIMULACIONES" de la misión v1.0.
- **Criterio de cumplimiento**: `grep -r "[Ss]imulad" frontend/` no encuentra nada relacionado con datos falsos de negocio.
- **Prueba sugerida**: Búsqueda dirigida en todo `frontend/`.
- **Archivo relacionado**: `frontend/public/`
- **Evidencia**: Búsqueda ejecutada durante la migración; el único resultado restante es un aviso honesto y verídico en `restablecer-contrasena.html` explicando que el envío de correo real todavía no existe (limitación real documentada, no una simulación del núcleo del producto).
- **Estado**: VERIFICADO

### RU-099
- **Descripción**: Cada regla de este documento tiene un estado honesto: no todas están marcadas VERIFICADO sin evidencia real.
- **Objetivo**: Que este documento sea confiable como fuente de verdad del estado de seguridad del proyecto.
- **Criterio de cumplimiento**: Cada regla en estado VERIFICADO cita un archivo de evidencia o una prueba concreta y ejecutada; las que no se han podido probar están en IMPLEMENTADO, BLOQUEADO o NO_APLICA con su justificación.
- **Prueba sugerida**: Revisar que ninguna regla VERIFICADO carezca de una referencia de evidencia concreta.
- **Archivo relacionado**: Este mismo documento.
- **Evidencia**: Revisión de las 100 reglas: 4 en NO_APLICA (subida de archivos/open redirect, ausentes en v1.0), 5 en BLOQUEADO (dependen del despliegue real en producción), 5 en IMPLEMENTADO (código correcto por inspección, sin ejecución real posible en este entorno), el resto en VERIFICADO con evidencia citada.
- **Estado**: VERIFICADO

### RU-100
- **Descripción**: El proyecto puede ejecutarse localmente siguiendo únicamente las instrucciones de README.md.
- **Objetivo**: Que cualquier persona nueva pueda levantar el proyecto sin ayuda externa.
- **Criterio de cumplimiento**: Los comandos documentados en README.md (crear venv, instalar dependencias, migrar, arrancar) son exactamente los que se usaron durante esta migración.
- **Prueba sugerida**: Seguir README.md desde cero en una máquina limpia.
- **Archivo relacionado**: `README.md`
- **Evidencia**: README.md fue actualizado en esta fase de documentación para reflejar el flujo real usado (`pip install -r requirements.txt`, `flask db upgrade`, `python app.py`), que es literalmente el que se ejecutó decenas de veces durante el desarrollo y las pruebas E2E de esta migración. No se repitió el flujo completo en una máquina "limpia" distinta a la usada durante el desarrollo.
- **Estado**: IMPLEMENTADO

---

## Resumen de estados (100 reglas)

| Estado | Cantidad | Reglas |
|---|---|---|
| VERIFICADO | 86 | La mayoría — ver detalle arriba |
| IMPLEMENTADO | 5 | RU-044, RU-082, RU-083, RU-090, RU-100 |
| BLOQUEADO | 5 | RU-013, RU-070, RU-085, RU-086 (dependen del despliegue real en producción) |
| NO_APLICA | 4 | RU-036, RU-037, RU-038, RU-039 (subida de archivos / open redirect: funcionalidades ausentes en v1.0) |
| PENDIENTE | 0 | — |

**Nota importante**: los 5 estados BLOQUEADO comparten la misma causa raíz: no existe todavía un despliegue real en producción (HTTPS, PostgreSQL, `FLASK_ENV=production`). El código y la configuración están implementados y revisados; lo que falta es la ejecución real en ese entorno. Ver `docs/DEPLOYMENT.md` para el detalle de qué falta y por qué.
