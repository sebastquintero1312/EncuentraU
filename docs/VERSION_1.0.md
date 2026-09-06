# VERSION_1.0.md — Informe de cierre de EncuentraU v1.0

**Fecha**: 2026-09-06

## 1. Resumen del proyecto

EncuentraU es una plataforma universitaria para gestionar objetos perdidos y encontrados. v0.25 tenía un backend Flask real pero limitado a autenticación (datos en memoria); todo el núcleo funcional (reportar, buscar, coincidencias, reclamaciones, administración) era una simulación en el frontend, sin backend ni base de datos detrás. v1.0 construye ese núcleo completo, migra la persistencia a una base de datos real con SQLAlchemy, y conecta el frontend por completo, eliminando toda simulación.

## 2. Cambios v0.25 → v1.0

Ver `CHANGELOG.md` para el detalle completo. Resumen: base de datos real (SQLAlchemy + Flask-Migrate), 4 módulos de negocio nuevos (objetos, solicitudes, coincidencias, administración), autorización real (ownership, roles, whitelist), hashing migrado a Argon2id, cabeceras de seguridad, 3 bugs reales encontrados y corregidos mediante pruebas, 88 pruebas automatizadas + verificación E2E con navegador real, documentación completa, y preparación de despliegue (bloqueada por autorización externa).

## 3. Arquitectura final

Ver `docs/ARQUITECTURA.md`. Monolito de dos capas (frontend estático + backend Flask) servidas desde el mismo origen, con PostgreSQL en producción / SQLite en desarrollo.

## 4. Componentes

| Componente | Estado |
|---|---|
| Frontend | VERIFICADO — todas las páginas conectadas a la API real, sin datos simulados, probado con navegador real |
| Backend Flask | VERIFICADO — 4 módulos de negocio completos, 88 pruebas pasando |
| Base de datos (SQLAlchemy) | VERIFICADO en SQLite (desarrollo); BLOQUEADO en PostgreSQL real (requiere el despliegue) |
| Autenticación | VERIFICADO — Argon2id, rate limiting, tokens seguros, sesión, recuperación (sin correo real) |
| Autorización | VERIFICADO — roles, ownership, whitelist, un admin no puede automodificarse |
| Seguridad | VERIFICADO localmente (ver `docs/MATRIZ_SEGURIDAD.md`); HTTPS/producción real BLOQUEADO |
| Pruebas | VERIFICADO — 88 pytest + 14 verificaciones E2E + 24 verificaciones manuales, toda con evidencia en `docs/evidencia/` |
| Despliegue | PREPARADO, NO DESPLEGADO — bloqueado por autorización externa (ver `docs/DEPLOYMENT.md`) |
| Documentación | VERIFICADO — completa y coincide con el código real |
| REGLAS_100.md | COMPLETO — 100/100 reglas evaluadas con evidencia (86 VERIFICADO, 5 IMPLEMENTADO, 5 BLOQUEADO, 4 NO_APLICA, 0 PENDIENTE) |

## 5. Limitaciones conocidas

1. **No hay despliegue real en producción.** El código, la configuración y el blueprint de Render (`render.yaml`) están listos y no se ha detectado ningún bloqueador técnico; falta la autorización externa de una cuenta de GitHub y de Render, que solo el propietario del proyecto puede otorgar. Ver `docs/DEPLOYMENT.md` para los pasos exactos pendientes.
2. **No hay envío real de correos electrónicos** (recuperación de contraseña). El token se imprime en el log del servidor — funcional para pruebas, no para usuarios reales sin acceso al servidor.
3. **La base de datos PostgreSQL gratuita de Render se borra a los 30 días.** Documentado en `docs/DEPLOYMENT.md`; aceptable para un proyecto académico, no para producción real sostenida sin mantenimiento.
4. **`SESSION_COOKIE_SECURE`, HSTS y el arranque con Gunicorn en producción están implementados pero no verificados en un entorno HTTPS real**, porque ese entorno todavía no existe.
5. **Sin verificación de correo institucional ni segundo factor de autenticación** — fuera del alcance definido para v1.0.
6. **Sin escaneo automatizado de dependencias vulnerables** en CI — fuera del alcance de esta fase.

Ninguna de estas limitaciones se presenta como resuelta. Ver `docs/REGLAS_100.md` para el detalle regla por regla de qué está VERIFICADO, IMPLEMENTADO, BLOQUEADO o NO_APLICA.

## 6. Riesgos conocidos

- Un despliegue real revelará si el comportamiento bajo PostgreSQL es idéntico al de SQLite (se usó el mismo ORM y las mismas migraciones, por lo que el riesgo es bajo, pero no se ha verificado con ejecución real).
- El plan gratuito de Render "duerme" el servicio tras 15 minutos de inactividad; la primera petición tras la inactividad tardará varios segundos en responder (limitación aceptada del plan gratuito, no un bug).
- Sin monitoreo/alertas configurado, un error en producción solo se detectaría revisando logs manualmente.

## 7. Declaración de seguridad (realista, no absoluta)

EncuentraU v1.0 tiene controles de seguridad implementados y probados para los riesgos más relevantes de una aplicación web con autenticación, roles y datos de usuarios (ver `docs/MATRIZ_SEGURIDAD.md`, revisión OWASP Top 10 completa). Esto **no significa que sea invulnerable**: ningún sistema lo es. Las limitaciones conocidas están documentadas explícitamente arriba y en `docs/REGLAS_100.md`.

## 8. RU-001 a RU-100

Ver `docs/REGLAS_100.md`. Resumen: 86 VERIFICADO, 5 IMPLEMENTADO (guardrails de producción no ejercitados en un arranque real), 5 BLOQUEADO (dependen del despliegue real), 4 NO_APLICA (subida de archivos y open redirect: funcionalidades ausentes en v1.0), 0 PENDIENTE.

## 9. Definición de "terminado" — checklist de la misión

- [x] Frontend funcional
- [x] Backend Flask funcional
- [x] SQLAlchemy funcional
- [x] Base de datos real (SQLite en desarrollo)
- [ ] PostgreSQL en producción — BLOQUEADO (requiere despliegue)
- [x] Frontend conectado al backend
- [x] Backend conectado a la base de datos
- [x] Autenticación real
- [x] Autorización real
- [x] Usuarios
- [x] Roles
- [x] Objetos perdidos
- [x] Objetos encontrados
- [x] Búsqueda
- [x] Filtros
- [x] Coincidencias
- [x] Reclamaciones
- [x] Administración
- [x] Seguridad (controles implementados y probados localmente)
- [x] Tests
- [x] Migraciones
- [x] Variables de entorno
- [x] Sin secretos publicados
- [ ] HTTPS — BLOQUEADO (requiere despliegue)
- [ ] URL pública — BLOQUEADO (requiere despliegue)
- [ ] Aplicación accesible desde Internet — BLOQUEADO (requiere despliegue)
- [ ] Pruebas realizadas sobre la URL pública — BLOQUEADO (requiere que la URL exista)
- [x] Persistencia de datos comprobada (en desarrollo, SQLite; pendiente repetir en PostgreSQL de producción)
- [x] Documentación actualizada
- [x] RU-001 → RU-100 evaluadas

## 10. Prueba de realidad

¿Puedo abrir EncuentraU desde un navegador usando una URL pública? **NO todavía** — no existe una URL pública; el sistema corre y fue probado en `http://127.0.0.1:5000`.
¿La URL utiliza HTTPS? **N/A** — no hay URL pública todavía.
¿El frontend funciona? **SÍ**, verificado con navegador real.
¿El frontend se comunica con Flask? **SÍ**, verificado.
¿Flask se comunica con SQLAlchemy? **SÍ**, verificado (SQLite en desarrollo).
¿SQLAlchemy se comunica con PostgreSQL? **NO VERIFICADO** — el código está preparado (`psycopg2-binary`, conversión de `DATABASE_URL`), pero no se ha ejecutado contra un PostgreSQL real.
¿Los datos realmente se guardan? **SÍ**, verificado (SQLite real, sobrevive a reinicios del proceso, confirmado creando datos, cerrando sesión y volviendo a consultarlos).
¿Puedo cerrar la página y volver a entrar y encontrar mis datos? **SÍ**, verificado con navegador real.
¿El login funciona desde Internet? **NO VERIFICADO** — solo desde localhost.
¿Los reportes funcionan desde Internet? **NO VERIFICADO** — solo desde localhost.
¿La búsqueda funciona desde Internet? **NO VERIFICADO** — solo desde localhost.
¿Las reclamaciones funcionan desde Internet? **NO VERIFICADO** — solo desde localhost.
¿El administrador funciona desde Internet? **NO VERIFICADO** — solo desde localhost.
¿Las medidas de seguridad funcionan? **PROBADAS localmente** (ver `docs/MATRIZ_SEGURIDAD.md`); no probadas en un entorno de producción real por HTTPS.

## 11. Próximo paso único y explícito

El proyecto está a un solo paso humano de tener una URL pública real:
1. El propietario crea (o autoriza) un repositorio de GitHub y una cuenta de Render.
2. Sigue los pasos exactos de `docs/DEPLOYMENT.md` (5 pasos, ~10 minutos).
3. Se repite la prueba crítica de persistencia y la verificación E2E contra la URL pública resultante.
4. Se actualiza este documento y `README.md`/`docs/DEPLOYMENT.md` con la URL real.

Hasta que eso ocurra, v1.0 se declara **funcionalmente completa y verificada en un entorno local**, no **desplegada en producción**.
