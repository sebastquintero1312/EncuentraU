# DEPLOYMENT.md — Despliegue de EncuentraU v2.0

## Estado real: PENDIENTE

- La v1.0 se llegó a desplegar en Render con su PostgreSQL gratuito. **Esa base de datos venció**: Render borra las bases gratuitas 30 días después de crearlas (14 días de gracia).
- La v2.0 **no se ha desplegado**. Los archivos `render.yaml` y `Procfile` todavía son los de v1.0 y **no sirven para v2.0 sin cambios**: la v2.0 se niega a arrancar en producción sin Brevo, sin `URL_PUBLICA` con https y sin una base PostgreSQL migrada.
- Decisión tomada: seguir en **Render (servicio web gratuito)** y usar **Supabase (PostgreSQL gratuito)** como base de datos.

## Lo que hay que hacer (próxima fase)

### 1. Supabase
1. Crear el proyecto.
2. En el *SQL Editor*, crear el usuario de la aplicación con permisos mínimos (como en `database/scripts/crear_bd_local.sql`, pero solo la parte de `encuentrau_app`).
3. Copiar dos URLs del **pooler en modo Session** (puerto 5432, funciona por IPv4; la conexión directa de Supabase gratuito es solo IPv6): una con el usuario `postgres` (dueño, para migraciones) y otra con `encuentrau_app` (para la aplicación). Agregar `?sslmode=require`.
4. Ejecutar la migración desde el PC con `DATABASE_URL_MIGRACIONES` apuntando a Supabase: `flask db upgrade`. `06_permisos.sql` detecta Supabase (roles `anon`/`authenticated`) y les quita todo acceso.
5. Supabase gratuito **pausa el proyecto tras 7 días sin actividad**; se reactiva desde su panel.

### 2. Brevo (correos)
Crear la cuenta, verificar un correo remitente y generar una API key. Variables: `CORREO_PROVEEDOR=brevo`, `BREVO_API_KEY`, `CORREO_REMITENTE`. Riesgo: los correos de un remitente genérico pueden llegar a spam en `@sanmateo.edu.co`; lo ideal es pedir a la universidad un remitente institucional.

### 3. Render
- Quitar el bloque `databases` de `render.yaml` y definir las variables a mano: `DATABASE_URL` (app), `FLASK_ENV=production`, `SECRET_KEY` (generada por Render), `URL_PUBLICA=https://<servicio>.onrender.com`, `NUM_PROXIES=1`, las de Brevo, `DOMINIO_CORREO_INSTITUCIONAL`.
- La migración ya no debería correr en cada arranque con el usuario de la app (no tiene permiso para crear tablas): se ejecuta aparte, con la URL del dueño.
- Revisar el número de procesos de Gunicorn: el límite de peticiones guarda los contadores en memoria por proceso; con 1 proceso y varios hilos los límites son exactos.
- Render gratuito **no tiene Shell**: el primer administrador se crea desde el PC con `DATABASE_URL_MIGRACIONES` apuntando a Supabase (`flask crear-admin correo`) o con un `UPDATE usuarios SET rol = 'administrador' …` en el SQL Editor de Supabase.
- Render gratuito bloquea los puertos SMTP (por eso Brevo se usa por API HTTPS) y "duerme" el servicio tras 15 minutos sin visitas.

### 4. GitHub
- Secretos para el respaldo diario (`.github/workflows/respaldo-bd.yml`): `SUPABASE_DB_URL` (pooler, dueño) y `BACKUP_PASSPHRASE`.
- `.github/workflows/pruebas.yml` correrá pytest en cada push sin configuración adicional.

### 5. Verificación en producción (después de desplegar)
Repetir `tests/e2e/verificacion_navegador.py` contra la URL pública (requiere adaptarlo para leer los enlaces de verificación de un buzón real o verificar con `flask verificar-correo`), comprobar las cabeceras HTTPS/HSTS y la cookie `Secure`, y probar una restauración de respaldo.

## Variables de entorno de producción

Ver la tabla de `docs/BACKEND.md` ("Variables de entorno").
