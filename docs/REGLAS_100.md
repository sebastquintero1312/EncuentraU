# REGLAS_100.md — 100 Reglas de Seguridad y Desarrollo para EncuentraU

**Versión evaluada**: v2.0 · **Última actualización**: 2026-10-16
**Nota**: IMPLEMENTADO ≠ VERIFICADO. Una regla es VERIFICADO solo con evidencia real de ejecución (prueba automatizada ejecutada, verificación con navegador o inspección de una respuesta real). Las pruebas citadas están en `backend/tests/` y su ejecución en `docs/evidencia/pytest_v2.0.txt`; "E2E" se refiere a `docs/evidencia/e2e_navegador_v2.0.txt`.

**Estados**: PENDIENTE · EN_DESARROLLO · IMPLEMENTADO · VERIFICADO · PARCIAL · BLOQUEADO · NO_APLICA

> Cambios respecto a la evaluación de v1.0: se reemplazaron todas las evidencias (las pruebas de v1.0 se reescribieron para PostgreSQL), y se actualizó el texto de las reglas que cambiaron con el nuevo modelo de roles y de reclamación (RU-028, RU-039, RU-059, RU-070 a RU-080). Al final se agregan los controles nuevos de v2.0.

## A. Autenticación (RU-001 a RU-015)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-001 | Las contraseñas nunca se almacenan en texto plano | VERIFICADO | `test_hash_no_es_texto_plano` |
| RU-002 | Se usa Argon2id | VERIFICADO | `test_hash_no_es_texto_plano` (prefijo `$argon2id$`) |
| RU-003 | Mínimo 12 caracteres | VERIFICADO | `test_validar_contrasena_debil`, `test_recuperacion_con_contrasena_debil_no_gasta_el_token` |
| RU-004 | Mayúscula, minúscula, número y carácter especial | VERIFICADO | `test_validar_contrasena_fuerte`, `test_validar_contrasena_debil` |
| RU-005 | Contraseñas comunes bloqueadas | VERIFICADO | `test_validar_contrasena_comun_rechazada` |
| RU-006 | La contraseña no contiene el nombre ni el correo | VERIFICADO | `test_validar_contrasena_no_debe_contener_el_correo` |
| RU-007 | Mensajes de login genéricos | VERIFICADO | `test_login_con_credenciales_incorrectas_es_generico`, `test_mensaje_de_verificacion_solo_con_contrasena_correcta` |
| RU-008 | Límite de peticiones en login | VERIFICADO | `test_rate_limit_login` |
| RU-009 | Límite de peticiones en registro | VERIFICADO | `test_rate_limit_registro` |
| RU-010 | `session.clear()` antes de crear la sesión | VERIFICADO | `test_login_regenera_la_sesion` |
| RU-011 | Cookie de sesión `HttpOnly` | VERIFICADO | `test_cookie_de_sesion_httponly_y_samesite` |
| RU-012 | Cookie de sesión `SameSite=Lax` | VERIFICADO | `test_cookie_de_sesion_httponly_y_samesite` |
| RU-013 | Cookie `Secure` en producción | BLOQUEADO | Configuración comprobada (`test_produccion_cookie_segura_y_hsts`); falta un despliegue HTTPS real |
| RU-014 | Tokens con `secrets.token_urlsafe()` | VERIFICADO | `test_token_es_largo_y_distinto_cada_vez` |
| RU-015 | Tokens de recuperación vencen en 30 minutos | VERIFICADO | `test_token_de_verificacion_vencido_no_sirve` (mismo mecanismo de vencimiento); `MINUTOS_EXPIRACION_TOKEN = 30` |

## B. Autorización (RU-016 a RU-030)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-016 | El rol viene de la BD, nunca del cliente | VERIFICADO | `test_registro_ignora_el_rol_que_manda_el_cliente`, `test_el_rol_se_relee_de_la_base_en_cada_peticion` |
| RU-017 | Endpoints de administrador verifican el rol en el backend | VERIFICADO | `test_rutas_de_admin_prohibidas_para_estudiante_y_encargado` |
| RU-018 | Endpoints protegidos verifican autenticación | VERIFICADO | `test_sin_sesion_todo_responde_401` |
| RU-019 | Ownership protege modificaciones | VERIFICADO | `test_editar_reporte_ajeno_esta_prohibido` |
| RU-020 | Ownership protege cancelaciones (no hay borrado físico) | VERIFICADO | `test_idor_reporte_de_perdida_ajeno`, `test_no_se_cancela_la_reclamacion_de_otro` |
| RU-021 | Campos actualizables en whitelist | VERIFICADO | `test_editar_ignora_campos_no_permitidos`, `test_whitelist_al_actualizar_usuario`, `test_mass_assignment_*` |
| RU-022 | Nadie reclama lo que él mismo reportó | VERIFICADO | `test_no_se_puede_reclamar_lo_que_uno_mismo_encontro` |
| RU-023 | Las reclamaciones requieren verificación humana | VERIFICADO | `test_flujo_completo_hasta_la_entrega` (pre-aprobación del encargado + entrega presencial) |
| RU-024 | Errores de autorización → 403 | VERIFICADO | `test_rutas_de_*_prohibidas_*`, `test_idor_*` |
| RU-025 | Endpoints públicos declarados explícitamente | VERIFICADO | `docs/API.md` (columna Acceso) + `test_cada_endpoint_real_esta_documentado` |
| RU-026 | El frontend no decide la seguridad | VERIFICADO | `test_rutas_de_*` (el backend rechaza sin importar la interfaz); `js/layout.js` solo redirige |
| RU-027 | Los listados respetan la autorización | VERIFICADO | `test_mis_reportes_solo_muestra_los_propios`, `test_objeto_encontrado_no_aparece_en_busqueda_hasta_llegar_a_la_oficina` |
| RU-028 | El administrador consulta todo, pero no opera objetos (separación de funciones) | VERIFICADO | `test_admin_si_puede_consultar_objetos`, `test_admin_no_puede_operar_objetos` |
| RU-029 | Ningún endpoint de admin accesible sin autenticación | VERIFICADO | `test_sin_sesion_todo_responde_401` |
| RU-030 | Los tokens se invalidan al usarse o al emitir uno nuevo | VERIFICADO | `test_recuperacion_completa_y_token_de_un_solo_uso`, `test_pedir_recuperacion_dos_veces_invalida_el_primer_enlace` |

## C. Inyección y XSS (RU-031 a RU-040)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-031 | No hay SQL injection posible | VERIFICADO | `test_sql_injection_*` (4 pruebas) |
| RU-032 | Consultas parametrizadas en toda interacción con la BD | VERIFICADO | ORM + `:parametros` en `models/procedimientos.py` y `models/reportes.py`; `test_sql_injection_intento_drop_table` |
| RU-033 | Los datos se escapan al mostrarlos | VERIFICADO | E2E: "Un nombre con HTML se muestra como texto" |
| RU-034 | No se usa `innerHTML` con datos del servidor | VERIFICADO | Búsqueda en `frontend/public/js`: ningún `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` ni `eval` (solo un comentario) |
| RU-035 | Content-Security-Policy configurada | VERIFICADO | `test_cabeceras_de_seguridad`; E2E sin violaciones de CSP |
| RU-036 | Nombres de archivos subidos saneados | NO_APLICA | No hay subida de archivos (decisión: fotos revelarían detalles privados) |
| RU-037 | Tipo de archivo validado por contenido | NO_APLICA | Ídem |
| RU-038 | Archivos fuera del directorio de la app | NO_APLICA | Ídem |
| RU-039 | No hay open redirect | VERIFICADO | E2E: "El parámetro siguiente no redirige a sitios externos"; `test_los_enlaces_de_las_notificaciones_son_internos` + CHECK en `notificaciones.enlace` |
| RU-040 | Filtros de búsqueda seguros | VERIFICADO | `test_sql_injection_en_filtros_numericos`, `test_patron_busqueda_escapa_comodines` |

## D. CSRF y sesión (RU-041 a RU-050)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-041 | CSRFProtect activo en POST/PUT | VERIFICADO | `test_csrf_requerido_en_registro`, `test_csrf_tambien_protege_las_acciones_del_encargado` |
| RU-042 | El frontend obtiene el token CSRF | VERIFICADO | E2E (todos los formularios funcionan con CSRF activo) |
| RU-043 | El token viaja en `X-CSRFToken` | VERIFICADO | `test_csrf_token_valido_permite_la_peticion` |
| RU-044 | `SECRET_KEY` larga y aleatoria | IMPLEMENTADO | Local: `secrets.token_hex(32)`; producción la generará Render |
| RU-045 | `SECRET_KEY` desde variable de entorno | VERIFICADO | `test_produccion_rechaza_secret_key_insegura` |
| RU-046 | Nada sensible en la sesión | VERIFICADO | `test_la_sesion_solo_guarda_el_id_del_usuario` |
| RU-047 | Logout invalida la sesión | VERIFICADO | `test_sesion_y_logout` |
| RU-048 | Ni token CSRF ni sesión en localStorage | VERIFICADO | `js/api.js` (variable en memoria); búsqueda sin `localStorage`/`sessionStorage` en `frontend/public/js` |
| RU-049 | La sesión expira | VERIFICADO | `test_cookie_de_sesion_httponly_y_samesite` (cookie de sesión del navegador, sin `Expires`) |
| RU-050 | Tokens de un solo uso | VERIFICADO | `test_token_de_verificacion_es_de_un_solo_uso`, `test_recuperacion_completa_y_token_de_un_solo_uso` |

## E. Validación y errores (RU-051 a RU-060)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-051 | Todo se valida en el backend | VERIFICADO | `test_validaciones_de_reporte`, `test_validaciones_de_la_reclamacion`, `test_tipos_inesperados_en_los_campos` |
| RU-052 | Errores sin tracebacks | VERIFICADO | `test_errores_no_exponen_detalles_internos` |
| RU-053 | Códigos HTTP correctos | VERIFICADO | Toda la suite verifica códigos (401/403/404/409/413/429) |
| RU-054 | Errores por campo en `errores` | VERIFICADO | `test_validaciones_de_reporte` |
| RU-055 | JSON malformado sin error 500 | VERIFICADO | `test_json_malformado_no_causa_error_500`, `test_json_que_no_es_un_objeto_no_causa_error_500` |
| RU-056 | `MAX_CONTENT_LENGTH` | VERIFICADO | `test_payload_json_extremadamente_grande_es_rechazado` |
| RU-057 | Longitudes validadas en backend (y en la BD) | VERIFICADO | `test_validaciones_*`, `test_texto_demasiado_largo_no_causa_error_500`; CHECK de longitud en `01_tablas.sql` |
| RU-058 | Fechas de eventos no futuras | VERIFICADO | `test_validaciones_de_reporte`, `test_validar_fecha_pasada_rechaza_futuro`; CHECK `ck_objetos_fecha_no_futura` |
| RU-059 | Categorías y ubicaciones solo de un catálogo (no texto libre) | VERIFICADO | `test_validaciones_de_reporte`, `test_categoria_desactivada_no_se_puede_usar` (FK a `categorias`/`ubicaciones`) |
| RU-060 | Paginación con límites | VERIFICADO | `test_parametros_de_paginacion_maliciosos` |

## F. Base de datos (RU-061 a RU-070)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-061 | ORM en vez de SQL crudo (salvo procedimientos y vistas, parametrizados) | VERIFICADO | `models/`; SQL a mano solo en `procedimientos.py` y `reportes.py` |
| RU-062 | Toda tabla tiene clave primaria | VERIFICADO | `test_la_migracion_crea_tablas_vistas_y_procedimientos` + `01_tablas.sql` |
| RU-063 | Claves foráneas reales | VERIFICADO | `test_entrega_con_objeto_que_no_coincide_con_la_solicitud` (23503) |
| RU-064 | Correo único | VERIFICADO | `ux_usuarios_correo`; `test_registro_con_correo_existente_no_revela_que_existe` (no se crea un segundo usuario) |
| RU-065 | Valores fijos restringidos en la BD | VERIFICADO | `test_check_rechaza_correo_en_mayusculas`, `test_fk_compuesta_impide_un_estado_de_otro_tipo` |
| RU-066 | Esquema solo por migraciones | VERIFICADO | pytest aplica la migración real `upgrade → downgrade → upgrade` en cada ejecución |
| RU-067 | Máquina de estados explícita | VERIFICADO | `test_trigger_rechaza_transiciones_no_permitidas` (tabla `transiciones_objeto` + trigger) |
| RU-068 | Usuario desactivado no entra; no hay borrado físico | VERIFICADO | `test_cuenta_desactivada_no_puede_entrar`, `test_la_aplicacion_no_tiene_permiso` (`DELETE` prohibido) |
| RU-069 | Campos sensibles nunca en el JSON | VERIFICADO | `test_la_api_nunca_devuelve_hashes` |
| RU-070 | PostgreSQL en todos los entornos; la app no arranca sin él | VERIFICADO | `test_rechaza_arrancar_sin_postgresql`; suite completa sobre PostgreSQL 18.6 |

## G. Lógica de negocio (RU-071 a RU-080)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-071 | Un reporte nace en el estado inicial de su tipo | VERIFICADO | `test_crear_reporte_*_empieza_*`, `test_trigger_exige_el_estado_inicial_al_crear` |
| RU-072 | La búsqueda muestra solo datos públicos | VERIFICADO | `test_busqueda_no_muestra_la_descripcion_privada`, `test_busqueda_no_filtra_por_la_descripcion_privada` |
| RU-073 | Solo se publica lo que está en la oficina | VERIFICADO | `test_objeto_encontrado_no_aparece_en_busqueda_hasta_llegar_a_la_oficina` |
| RU-074 | Una coincidencia nunca cambia estados | VERIFICADO | `test_coincidencias_para_un_reporte_de_perdida` |
| RU-075 | No se reclama un reporte propio | VERIFICADO | `test_no_se_puede_reclamar_lo_que_uno_mismo_encontro` |
| RU-076 | Una reclamación abierta por persona y objeto | VERIFICADO | `test_una_sola_reclamacion_abierta_por_objeto` (índice único parcial) |
| RU-077 | La entrega descarta las demás reclamaciones | VERIFICADO | `test_entrega_descarta_las_demas_reclamaciones` |
| RU-078 | Rechazar o cancelar una pre-aprobada libera el objeto | VERIFICADO | `test_rechazar_una_preaprobada_libera_el_objeto`, `test_estudiante_cancela_su_reclamacion_preaprobada` |
| RU-079 | La información de verificación solo la ven el reclamante y la oficina | VERIFICADO | `test_el_reclamante_nunca_ve_la_descripcion_privada`, `test_el_encargado_compara_reclamacion_con_detalles_privados` |
| RU-080 | Solo el encargado cambia estados de custodia y solo por transiciones válidas | VERIFICADO | `test_admin_no_puede_operar_objetos`, `test_no_se_cierra_un_objeto_reservado`, `test_recibir_dos_veces_el_mismo_objeto_falla` |

## H. Configuración y despliegue (RU-081 a RU-090)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-081 | Debug apagado salvo `FLASK_ENV=development` explícito | VERIFICADO | `test_debug_solo_con_development_explicito` (bug heredado de v1.0 corregido) |
| RU-082 | No arranca en producción con `SECRET_KEY` insegura | VERIFICADO | `test_produccion_rechaza_secret_key_insegura` (lógica); falta un arranque real en producción |
| RU-083 | No arranca sin PostgreSQL | VERIFICADO | `test_rechaza_arrancar_sin_postgresql` |
| RU-084 | Cabeceras de seguridad | VERIFICADO | `test_cabeceras_de_seguridad` |
| RU-085 | HSTS solo en producción | BLOQUEADO | `test_sin_hsts_fuera_de_produccion` (ausencia en desarrollo); falta verificarlo en HTTPS real |
| RU-086 | Gunicorn en producción | BLOQUEADO | Requiere el despliegue (ver `docs/DEPLOYMENT.md`) |
| RU-087 | Sin secretos en el repositorio | VERIFICADO | `.env` ignorado; búsqueda de las contraseñas locales en archivos versionados: ninguna coincidencia |
| RU-088 | `.env.example` sin credenciales reales | VERIFICADO | `backend/.env.example` (marcadores `CLAVE_APP`, `CLAVE_DUENO`) |
| RU-089 | `.gitignore` excluye `.env`, respaldos y entornos virtuales | VERIFICADO | `.gitignore` (`.env`, `venv/`, `database/respaldos/`, `*.dump`) |
| RU-090 | Variables de producción documentadas | IMPLEMENTADO | `docs/BACKEND.md`, `docs/DEPLOYMENT.md`; se confirmará al desplegar |

## I. Pruebas y calidad (RU-091 a RU-100)

| ID | Regla | Estado | Evidencia |
|---|---|---|---|
| RU-091 | Suite automatizada de autenticación, autorización, negocio y seguridad | VERIFICADO | `docs/evidencia/pytest_v2.0.txt` |
| RU-092 | Verificación con navegador real | VERIFICADO | `docs/evidencia/e2e_navegador_v2.0.txt` |
| RU-093 | Sin `innerHTML` con datos de la API | VERIFICADO | Ver RU-034 |
| RU-094 | Sin scripts inline | VERIFICADO | Las 25 páginas solo usan `<script src>`; la CSP `script-src 'self'` lo exige y el E2E no registró violaciones |
| RU-095 | Separación rutas → controladores → servicios → modelos | VERIFICADO | `docs/ARQUITECTURA.md`, `docs/BACKEND.md` |
| RU-096 | `docs/API.md` refleja los endpoints reales | VERIFICADO | `test_cada_endpoint_real_esta_documentado`, `test_no_se_documentan_endpoints_que_no_existen` |
| RU-097 | El CHANGELOG documenta los cambios significativos | VERIFICADO | `CHANGELOG.md`, sección v2.0 |
| RU-098 | Sin datos simulados en páginas funcionales | VERIFICADO | E2E recorre todas las pantallas con datos reales |
| RU-099 | Estados honestos en este documento | VERIFICADO | Las reglas sin evidencia de ejecución están en IMPLEMENTADO, BLOQUEADO o NO_APLICA |
| RU-100 | El proyecto corre siguiendo solo el README | PARCIAL | Pasos ejecutados por el asistente en un PostgreSQL temporal (mismos scripts); falta que el propietario los repita en su servidor |

## Resumen

| Estado | Cantidad | Reglas |
|---|---|---|
| VERIFICADO | 91 | todas las demás |
| PARCIAL | 1 | RU-100 |
| IMPLEMENTADO | 2 | RU-044, RU-090 |
| BLOQUEADO | 3 | RU-013, RU-085, RU-086 (requieren el despliegue en producción) |
| NO_APLICA | 3 | RU-036, RU-037, RU-038 (no hay subida de archivos) |

## Controles nuevos de v2.0 (además de las 100 reglas)

| ID | Control | Estado | Evidencia |
|---|---|---|---|
| C2-01 | Registro solo con correo institucional | VERIFICADO | `test_registro_solo_con_correo_institucional`, `test_correo_institucional` |
| C2-02 | Verificación del correo antes de usar la cuenta | VERIFICADO | `test_no_puede_iniciar_sesion_sin_verificar_el_correo`, E2E |
| C2-03 | Registro sin enumeración de cuentas | VERIFICADO | `test_registro_con_correo_existente_no_revela_que_existe` |
| C2-04 | Tokens guardados solo como hash | VERIFICADO | `test_en_la_base_solo_se_guarda_el_hash_del_token` |
| C2-05 | Tres roles con funciones separadas | VERIFICADO | `test_roles.py` |
| C2-06 | Verificación a ciegas de las reclamaciones | VERIFICADO | `test_el_reclamante_nunca_ve_la_descripcion_privada`, E2E |
| C2-07 | Código de retiro de un solo uso (HMAC, intentos, vencimiento) | VERIFICADO | `test_codigo_incorrecto_suma_intentos_y_se_bloquea`, `test_reserva_vencida_libera_el_objeto` |
| C2-08 | Entrega presencial con carné y prueba | VERIFICADO | `test_entrega_exige_carne_y_prueba` |
| C2-09 | Límites de reclamaciones y cuentas en revisión (en la BD) | VERIFICADO | `test_el_limite_tambien_lo_exige_la_base_de_datos`, `test_tres_rechazos_ponen_la_cuenta_en_revision` |
| C2-10 | Auditoría completa e inmutable por triggers | VERIFICADO | `test_auditoria_*`, `test_la_auditoria_registra_quien_hizo_cada_paso` |
| C2-11 | Usuario de BD con permisos mínimos y por columna | VERIFICADO | `test_la_aplicacion_no_tiene_permiso` |
| C2-12 | Row Level Security | VERIFICADO | `test_rls_activo_en_todas_las_tablas` |
| C2-13 | Concurrencia pesimista y optimista | VERIFICADO | `test_concurrencia.py` |
| C2-14 | Respaldo y restauración | VERIFICADO | `docs/evidencia/respaldo_restauracion_v2.0.txt` |
| C2-15 | Respaldo diario cifrado en la nube | IMPLEMENTADO | `.github/workflows/respaldo-bd.yml` (sin ejecutar) |
| C2-16 | Integración continua | IMPLEMENTADO | `.github/workflows/pruebas.yml` (sin ejecutar) |
| C2-17 | Correos reales por Brevo | IMPLEMENTADO | `correo_service.py` (probado solo en modos consola y memoria) |
| C2-18 | Exportación CSV sin datos personales ni fórmulas | VERIFICADO | `test_exportar_csv_sin_datos_personales_y_seguro_para_excel` |
| C2-19 | Usuario lector para herramientas de análisis | IMPLEMENTADO | `database/scripts/crear_rol_lector.sql` (sin ejecutar) |
| C2-20 | Endurecimiento para Supabase (sin acceso de `anon`/`authenticated`) | IMPLEMENTADO | `06_permisos.sql` (sin ejecutar en Supabase) |
