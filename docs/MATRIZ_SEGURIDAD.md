# MATRIZ_SEGURIDAD.md — Revisión OWASP Top 10 (2021) de EncuentraU v2.0

**Metodología**: para cada riesgo se documenta si aplica, la medida, dónde está, cómo se probó y el resultado. Evidencia: `docs/evidencia/pytest_v2.0.txt`, `e2e_navegador_v2.0.txt`, `respaldo_restauracion_v2.0.txt`. Detalle regla por regla: `docs/REGLAS_100.md`.

**Advertencia honesta**: esta matriz documenta controles implementados y probados, no una garantía de "100% seguro". Ningún sistema lo es.

## A01 — Broken Access Control
- **Medida**: tres roles con permisos separados y decoradores por rol que releen el rol de la BD en cada petición; ownership en reportes, reclamaciones y notificaciones; whitelists; la BD vuelve a exigir el rol en procedimientos y triggers; usuario de BD de la app con permisos por columna y sin `DELETE`; RLS.
- **Prueba**: `test_roles.py` (matriz completa ruta por ruta), `test_idor_*`, `test_mass_assignment_*`, `test_la_aplicacion_no_tiene_permiso` (12 operaciones prohibidas → 42501), `test_la_base_de_datos_tambien_exige_el_rol_encargado`; E2E: un estudiante y una encargada que abren pantallas ajenas vuelven a su panel.
- **Estado**: VERIFICADO.

## A02 — Cryptographic Failures
- **Medida**: Argon2id; tokens con `secrets` y guardados solo como SHA-256; código de retiro guardado como HMAC-SHA256 con la `SECRET_KEY`; la auditoría nunca copia hashes; respaldos en la nube cifrados con AES-256; cookie `HttpOnly`+`SameSite=Lax`+`Secure` en producción; HSTS en producción.
- **Prueba**: `test_hash_no_es_texto_plano`, `test_en_la_base_solo_se_guarda_el_hash_del_token`, `test_el_codigo_no_se_guarda_en_claro`, `test_hash_de_codigo_depende_de_la_secret_key`, `test_auditoria_no_expone_hashes`, `test_cookie_de_sesion_httponly_y_samesite`.
- **Limitación**: HTTPS, `Secure` y HSTS reales no verificados (no hay despliegue). Cifrado del respaldo en GitHub Actions no ejecutado.
- **Estado**: VERIFICADO localmente; producción PENDIENTE.

## A03 — Injection
- **Medida**: ORM y SQL siempre parametrizado (también en los `CALL`); comodines de `ILIKE` escapados; filtros numéricos convertidos a entero; salida en el navegador solo con `textContent`; CSV protegido contra inyección de fórmulas; correos en texto plano.
- **Prueba**: `test_sql_injection_*` (búsqueda, filtros numéricos, auditoría), `test_xss_almacenado_se_guarda_como_texto_plano`, `test_celda_csv_evita_inyeccion_de_formulas`; E2E: un objeto llamado `<img src=x onerror=alert(1)>` se muestra literal y no ejecuta nada.
- **Estado**: VERIFICADO.

## A04 — Insecure Design
- **Medida**: rediseño del proceso de reclamación contra fraudes: verificación a ciegas, publicación solo de lo que está en la oficina, evidencia de reporte previo, código de un solo uso con intentos limitados y vencimiento, entrega presencial con carné y prueba, límites y cuentas en revisión, separación de funciones encargado/administrador, máquina de estados en la BD (ver `docs/AUTHORIZATION.md` §4).
- **Prueba**: `test_reclamaciones.py` (32 pruebas), `test_concurrencia.py`; E2E del flujo completo.
- **Limitación**: si un impostor conoce bien el objeto puede describirlo; la barrera final es la prueba presencial.
- **Estado**: VERIFICADO.

## A05 — Security Misconfiguration
- **Medida**: `validar_configuracion()` rechaza arrancar sin PostgreSQL y, en producción, con `SECRET_KEY` insegura, sin Brevo o sin `https`; debug solo con `FLASK_ENV=development` explícito (bug heredado corregido); CSP estricta sin `unsafe-inline`; `Cache-Control: no-store` en la API; `MAX_CONTENT_LENGTH`; errores sin detalles internos; ProxyFix solo si `NUM_PROXIES` > 0.
- **Prueba**: `tests/unit/test_config.py`, `test_cabeceras_de_seguridad`, `test_errores_no_exponen_detalles_internos`, `test_payload_json_extremadamente_grande_es_rechazado`; E2E sin violaciones de CSP (la CSP incluso bloqueó el `eval` de Playwright).
- **Estado**: VERIFICADO localmente; arranque real en producción PENDIENTE.

## A06 — Vulnerable and Outdated Components
- **Medida**: dependencias con versión exacta; fuentes e íconos servidos localmente (sin CDN); Font Awesome verificado contra el hash SRI publicado por cdnjs.
- **Limitación**: no hay escaneo automático de vulnerabilidades (`pip-audit`).
- **Estado**: PARCIAL.

## A07 — Identification and Authentication Failures
- **Medida**: solo correos institucionales y **verificados**; política de contraseñas; respuestas anti-enumeración en registro, reenvío y recuperación (incluido el tiempo de respuesta); tokens de un solo uso con propósito y vencimiento; regeneración de sesión al iniciar sesión; límites de peticiones.
- **Prueba**: `test_auth.py`, `test_login_regenera_la_sesion`, `test_rate_limit_*`.
- **Estado**: VERIFICADO.

## A08 — Software and Data Integrity Failures
- **Medida**: migración versionada y transaccional; restricciones CHECK/FK/UNIQUE y triggers en la BD; actas de entrega inmodificables; concurrencia pesimista (`FOR UPDATE`) y optimista (`version`); respaldos con restauración probada; CI que corre las pruebas en cada push.
- **Prueba**: migración `upgrade → downgrade → upgrade` en cada ejecución de pytest, `test_esquema_bd.py`, `test_concurrencia.py`, `respaldo_restauracion_v2.0.txt`.
- **Limitación**: el flujo de CI no se ha ejecutado en GitHub todavía.
- **Estado**: VERIFICADO localmente.

## A09 — Security Logging and Monitoring Failures
- **Medida**: auditoría completa por triggers (quién, cuándo, IP, antes/después), inmutable incluso para el dueño, consultable por el administrador; cuentas con varios rechazos se marcan y se avisa al administrador; desempeño por encargado para detectar complicidad; errores 500 en el log del servidor.
- **Prueba**: `test_auditoria_*`, `test_la_auditoria_registra_quien_hizo_cada_paso`, `test_tres_rechazos_ponen_la_cuenta_en_revision`.
- **Limitación**: sin alertas automáticas ni monitoreo centralizado.
- **Estado**: VERIFICADO (auditoría); monitoreo NO_APLICA por alcance.

## A10 — Server-Side Request Forgery
- **Medida**: el servidor no descarga URLs indicadas por usuarios (el campo `imagen_url` de v1.0 se eliminó). Las únicas peticiones salientes van a una URL fija (API de Brevo).
- **Estado**: NO_APLICA.

## Resumen

| Riesgo | Estado |
|---|---|
| A01 Control de acceso | Verificado |
| A02 Criptografía | Verificado localmente; HTTPS de producción pendiente |
| A03 Inyección | Verificado |
| A04 Diseño inseguro | Verificado |
| A05 Configuración | Verificado localmente; producción pendiente |
| A06 Componentes | Parcial (sin escaneo automático) |
| A07 Autenticación | Verificado |
| A08 Integridad | Verificado localmente |
| A09 Registro y monitoreo | Auditoría verificada; monitoreo fuera de alcance |
| A10 SSRF | No aplica |
