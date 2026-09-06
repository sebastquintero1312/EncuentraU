# DEPLOYMENT.md — Despliegue de EncuentraU v1.0

## Estado real: PREPARADO, NO DESPLEGADO

Todo lo que se puede hacer sin una cuenta externa está hecho y verificado. El despliegue real en Internet está **bloqueado** porque requiere crear una cuenta en un proveedor de hosting y conectarla a un repositorio de GitHub — ambas acciones solo las puede autorizar el propietario del proyecto (no existen credenciales que un asistente automatizado pueda generar por sí mismo de forma legítima). Esto se documenta explícitamente en vez de inventar una URL o simular un despliegue que no ocurrió (regla contra falsos resultados, `CLAUDE.md`).

## Por qué Render

Se compararon tres proveedores con plan gratuito (búsqueda hecha en septiembre de 2026, no se asumieron condiciones antiguas):

| Proveedor | Web service gratis | PostgreSQL gratis | Tarjeta requerida | Veredicto |
|---|---|---|---|---|
| **Render** | Sí (se "duerme" tras 15 min de inactividad, HTTPS automático) | Sí, 1 GB, **se borra a los 30 días sin aviso** | No | **Elegido**: único con web + BD gratis reales y sin tarjeta |
| Railway | Solo con crédito inicial ($5), no es gratis permanente tras 30 días | Incluido en el mismo crédito | No para el trial, sí después | Descartado: no tiene plan gratuito permanente |
| PythonAnywhere | Sí, pero 100 segundos de CPU/día, sin acceso saliente libre | No confirmado en el plan gratuito (históricamente solo MySQL) | No | Descartado: sin PostgreSQL gratuito confirmado |

**Limitación real y aceptada**: la base de datos PostgreSQL gratuita de Render se borra automáticamente a los 30 días. Para un proyecto universitario esto es aceptable (se puede recrear y volver a migrar), pero debe quedar explícito: **no es apta para datos que deban persistir indefinidamente sin mantenimiento**. Si el proyecto continúa más allá de esa ventana, hay que recrear la base de datos o pasar a un plan pago.

## Qué está listo (preparado y verificado localmente)

- [x] `backend/requirements.txt` incluye `gunicorn` (servidor WSGI de producción) y `psycopg2-binary` (driver de PostgreSQL).
- [x] `Config.validar_configuracion_produccion()` impide arrancar en producción sin `SECRET_KEY` real y sin `DATABASE_URL` (ver `backend/app/config/config.py`).
- [x] `Procfile` en la raíz: `web: cd backend && flask db upgrade && gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app` — corre las migraciones automáticamente antes de arrancar.
- [x] `render.yaml` (blueprint de Render): define el servicio web y la base de datos PostgreSQL, con `SECRET_KEY` autogenerada por Render (nunca hardcodeada) y `DATABASE_URL` inyectada automáticamente desde la base de datos declarada.
- [x] CORS configurado para no incluir orígenes de `localhost` en producción (`ES_PRODUCCION`).
- [x] Cabeceras de seguridad, incluyendo HSTS activado solo en producción.
- [x] `.gitignore` confirmado: ningún secreto real se subiría al repositorio.
- [x] Migraciones de Alembic generadas y probadas localmente contra SQLite (el mismo comando `flask db upgrade` funciona igual contra PostgreSQL).

## Qué falta — y por qué requiere al propietario

| Paso | Por qué no lo puede hacer un asistente automatizado |
|---|---|
| 1. Crear un repositorio en GitHub y subir este código (`git remote add origin ... && git push`) | Requiere una cuenta de GitHub del propietario del proyecto (no existen credenciales legítimas para crear una en su nombre) |
| 2. Crear una cuenta en Render.com | Requiere verificación de correo electrónico real del propietario |
| 3. Conectar la cuenta de Render con el repositorio de GitHub (autorización OAuth) | Requiere que el propietario apruebe el acceso desde su propia sesión de GitHub |
| 4. En Render, "New Blueprint" apuntando a este repo (usa `render.yaml` automáticamente) | Acción manual en el dashboard de Render, solo el dueño de la cuenta puede hacerla |
| 5. Confirmar que la migración corrió y el primer administrador se creó (`flask crear-admin ...` desde la consola/shell que ofrece Render) | Requiere acceso a la consola de esa instancia, disponible solo tras el paso 4 |

## Pasos exactos para completar el despliegue (cuando el propietario los autorice)

```bash
# 1. Desde la raíz del proyecto (ya es un repositorio git local)
git remote add origin https://github.com/<usuario>/encuentrau.git
git push -u origin main

# 2. En https://render.com: crear cuenta (gratis, sin tarjeta)
# 3. "New +" → "Blueprint" → conectar el repositorio de GitHub
#    Render detecta render.yaml automáticamente y propone crear:
#    - Un servicio web "encuentrau" (plan free)
#    - Una base de datos "encuentrau-db" (PostgreSQL, plan free)
# 4. Revisar y confirmar ("Apply") — Render construye y despliega automáticamente
# 5. Cuando el despliegue termine, abrir la "Shell" del servicio en el dashboard de Render y ejecutar:
cd backend && flask crear-admin tu-correo@sanmateo.edu.co
```

La URL pública tendrá la forma `https://encuentrau-XXXX.onrender.com` (Render asigna el subdominio exacto al crear el servicio; no se puede predecir de antemano — por eso no aparece un valor inventado aquí).

## Prueba crítica de persistencia (a ejecutar una vez desplegado)

Una vez exista la URL pública, repetir contra ella (no contra localhost) la prueba documentada en `docs/evidencia/e2e_navegador_v1.0.txt`, y además:

1. Crear un usuario desde la web pública.
2. Cerrar sesión, volver a iniciar sesión.
3. Crear un reporte.
4. Recargar la página, cerrar sesión, volver a iniciar sesión.
5. Confirmar que el reporte sigue existiendo.

Esto demuestra que frontend + backend + PostgreSQL están realmente conectados en producción, no solo en desarrollo. **Esta prueba no se ha podido ejecutar todavía** porque no existe la URL pública — queda como el primer paso a documentar en cuanto el despliegue se complete.

## Variables de entorno de producción (ya definidas en `render.yaml`)

| Variable | Origen | Notas |
|---|---|---|
| `SECRET_KEY` | Autogenerada por Render (`generateValue: true`) | Nunca escrita a mano ni en el repositorio |
| `DATABASE_URL` | Inyectada automáticamente desde la base de datos `encuentrau-db` | Formato `postgresql://...`; `Config` convierte el prefijo antiguo `postgres://` si Render lo usara |
| `FLASK_ENV` | `production` (fijo en `render.yaml`) | Activa todos los guardrails de producción |
| `FLASK_APP` | `app.py` (fijo en `render.yaml`) | Necesario para `flask db upgrade` en el `startCommand` |

## Alternativas consideradas y descartadas

Ver la tabla comparativa arriba. Si en el futuro Render cambia sus condiciones (la propia guía de esta misión advierte no asumir que un proveedor mantiene las mismas condiciones), volver a evaluar con la misma metodología (buscar condiciones actuales, comparar plan gratuito real vs. trial con tarjeta) antes de migrar.
