# DEPLOYMENT.md — Despliegue de EncuentraU v2.0

## Estado real: DESPLEGADO — PARCIAL (2026-10-19)

URL pública: **https://encuentrau.onrender.com**

| Pieza | Estado | Evidencia |
|---|---|---|
| Supabase (PostgreSQL 17, región us-west-2) | VERIFICADO | `flask db upgrade` → `0001_esquema_v2`; 15 tablas, RLS en todas salvo `alembic_version`; `anon`/`authenticated` sin privilegios sobre las tablas. |
| Usuario `encuentrau_app` en Supabase | VERIFICADO | Conecta por el pooler (`encuentrau_app.<id-proyecto>`); `DELETE FROM auditoria` y `CREATE TABLE` → *permission denied*. |
| Servicio web en Render (free, Oregon) | VERIFICADO | Creado por la API de Render; despliega automáticamente la rama `main`; `GET /health` → 200. |
| HTTPS, HSTS, CSP, X-Frame-Options, nosniff, Referrer-Policy | VERIFICADO | Cabeceras de `GET /`; `http://` → 301 a `https://`. |
| Cookie de sesión `Secure; HttpOnly; SameSite=Lax` | VERIFICADO | `GET /api/auth/csrf-token`. |
| Brevo (correos) | VERIFICADO | El correo de verificación de registro llegó a un buzón `@sanmateo.edu.co` y la cuenta quedó verificada. |
| Primer administrador | VERIFICADO | `flask crear-admin` ejecutado desde el PC contra Supabase. |
| CI de pruebas en GitHub Actions | VERIFICADO | Suite completa sobre PostgreSQL en `main`: https://github.com/sebastquintero1312/EncuentraU/actions/runs/39299522079 |
| Secretos de respaldo en GitHub | PENDIENTE | |

- La v1.0 se llegó a desplegar en Render con su PostgreSQL gratuito. Esa base venció (Render borra las bases gratuitas a los 30 días).
- Los secretos de producción están en `backend/.env.produccion` (en `.gitignore`), solo en el PC del responsable.

## Pasos (referencia para repetir el despliegue)

### 1. Supabase
1. Crear el proyecto.
2. En el *SQL Editor*, crear el usuario de la aplicación con permisos mínimos con `database/scripts/crear_usuario_app_supabase.sql` (reemplazando la contraseña de ejemplo).
3. Copiar dos URLs del **pooler en modo Session** (puerto 5432, funciona por IPv4; la conexión directa de Supabase gratuito es solo IPv6): una con el usuario `postgres.<id-proyecto>` (dueño, para migraciones) y otra con `encuentrau_app.<id-proyecto>` (para la aplicación). Agregar `?sslmode=require`.
4. Ejecutar la migración desde el PC con `DATABASE_URL_MIGRACIONES` apuntando a Supabase: `flask db upgrade`. `06_permisos.sql` detecta Supabase (roles `anon`/`authenticated`) y les quita todo acceso.
5. Supabase gratuito **pausa el proyecto tras 7 días sin actividad**; se reactiva desde su panel.

### 2. Brevo (correos)
Crear la cuenta, verificar un correo remitente y generar una API key. Variables: `CORREO_PROVEEDOR=brevo`, `BREVO_API_KEY`, `CORREO_REMITENTE`. Riesgo: los correos de un remitente genérico pueden llegar a spam en `@sanmateo.edu.co`; lo ideal es pedir a la universidad un remitente institucional.

### 3. Render
- "New > Blueprint" con este repositorio. `render.yaml` ya fija `FLASK_ENV=production`, `SECRET_KEY` (generada por Render), `NUM_PROXIES=1`, `CORREO_PROVEEDOR=brevo` y `DOMINIO_CORREO_INSTITUCIONAL`. Render pide a mano (`sync: false`): `DATABASE_URL` (pooler, usuario `encuentrau_app`), `URL_PUBLICA=https://<servicio>.onrender.com`, `BREVO_API_KEY` y `CORREO_REMITENTE`.
- La migración no corre al arrancar (el usuario de la app no puede crear tablas): se ejecuta aparte, desde el PC, con la URL del dueño.
- Gunicorn corre con 1 proceso y 4 hilos: el límite de peticiones guarda los contadores en memoria por proceso, así los límites son exactos.
- Render gratuito **no tiene Shell**: el primer administrador se crea desde el PC con `DATABASE_URL_MIGRACIONES` apuntando a Supabase (`flask crear-admin correo`) o con un `UPDATE usuarios SET rol = 'administrador' …` en el SQL Editor de Supabase.
- Render gratuito bloquea los puertos SMTP (por eso Brevo se usa por API HTTPS) y "duerme" el servicio tras 15 minutos sin visitas.

### 4. GitHub
- Secretos para el respaldo diario (`.github/workflows/respaldo-bd.yml`): `SUPABASE_DB_URL` (pooler, dueño) y `BACKUP_PASSPHRASE`.
- `.github/workflows/pruebas.yml` correrá pytest en cada push sin configuración adicional.

### 5. Verificación en producción (después de desplegar)
Repetir `tests/e2e/verificacion_navegador.py` contra la URL pública (requiere adaptarlo para leer los enlaces de verificación de un buzón real o verificar con `flask verificar-correo`), comprobar las cabeceras HTTPS/HSTS y la cookie `Secure`, y probar una restauración de respaldo.

## Variables de entorno de producción

Ver la tabla de `docs/BACKEND.md` ("Variables de entorno").
