# EncuentraU

Plataforma de la comunidad San Mateo para reportar y recuperar objetos perdidos, con entrega verificada en la oficina de objetos perdidos.

**Versión actual: v2.0**: Flask + PostgreSQL (triggers, procedimientos almacenados, auditoría), tres roles (estudiante, encargado, administrador), reclamación con verificación a ciegas y código de retiro, verificación del correo institucional y frontend con el estilo del sitio de la universidad. **Desplegada en https://encuentrau.onrender.com** (Render + Supabase + Brevo; ver `docs/DEPLOYMENT.md`).

Documentación en `docs/`: `VERSION_2.0.md` (informe), `ARQUITECTURA.md`, `DATABASE.md`, `API.md`, `AUTHENTICATION.md`, `AUTHORIZATION.md`, `BACKEND.md`, `FRONTEND.md`, `TESTING.md`, `DEPLOYMENT.md`, `MATRIZ_SEGURIDAD.md`, `DIAGRAMAS.md`, `REGLAS_100.md`. En la raíz: `SECURITY.md` y `CHANGELOG.md`.

## Requisitos

- Python 3.11 (`winget install --id Python.Python.3.11 --source winget`)
- PostgreSQL 15 o superior (probado con 18.6)

## Cómo ejecutar en desarrollo (Windows, PowerShell)

### 1. Entorno de Python (una sola vez)

```powershell
cd C:\dev\EncuentraU\backend
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env
```

En `backend\.env`:
- Pon un `SECRET_KEY` propio. Para generarlo: `.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"`.
- Inventa dos contraseñas: una para el usuario dueño (`CLAVE_DUENO`) y otra para el de la aplicación (`CLAVE_APP`). Ponlas en las cuatro URLs de base de datos.

### 2. Base de datos (una sola vez)

Crea los usuarios `encuentrau` (dueño) y `encuentrau_app` (permisos mínimos) y las bases `encuentrau_dev` y `encuentrau_test`. Pide la contraseña de `postgres`:

```powershell
cd C:\dev\EncuentraU
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -v clave=CLAVE_DUENO -v clave_app=CLAVE_APP -f database\scripts\crear_bd_local.sql
```

Luego crea las tablas, triggers y procedimientos:

```powershell
cd C:\dev\EncuentraU\backend
.\venv\Scripts\flask.exe db upgrade
```

### 3. Arrancar

```powershell
.\venv\Scripts\python.exe app.py
```

Abre **http://127.0.0.1:5000**. En desarrollo los correos (verificación, recuperación, avisos) **se imprimen en esta terminal**: copia de ahí el enlace de verificación.

## Crear el primer administrador

1. Regístrate en http://127.0.0.1:5000/registro.html con tu correo `@sanmateo.edu.co` y abre el enlace de verificación que aparece en la terminal del servidor.
2. En otra terminal:
   ```powershell
   cd C:\dev\EncuentraU\backend
   .\venv\Scripts\flask.exe crear-admin tu-correo@sanmateo.edu.co
   ```
3. Inicia sesión: entrarás al panel del administrador. Desde **Usuarios** puedes nombrar encargados de la oficina.

No existe forma de volverse administrador desde la web: es intencional.

## Ver la base de datos

pgAdmin 4 (viene con PostgreSQL): servidor `localhost`, base `encuentrau_dev`, usuario `encuentrau`. Detalles y consultas útiles en `docs/DATABASE.md` §13.

## Pruebas

```powershell
cd C:\dev\EncuentraU\backend
.\venv\Scripts\python.exe -m pytest -q                         # suite completa (usa encuentrau_test y la BORRA)
.\venv\Scripts\python.exe tests\e2e\verificacion_navegador.py  # navegador real (Edge); levanta el servidor solo
```

Respaldo y restauración: `database/scripts/respaldo.py` y `restaurar.py` (ver `docs/DATABASE.md` §11).

## Problemas comunes

- **`UnicodeDecodeError ... byte 0xf3` al conectar**: PostgreSQL rechazó el usuario o la contraseña, pero envió el error en español y psycopg2 no lo pudo leer. Revisa que corriste `crear_bd_local.sql` con las mismas claves que hay en `.env`.
- **`DATABASE_URL no está definida o no es PostgreSQL`**: falta `backend\.env` o sus URLs.
- **No llega el correo de verificación**: en desarrollo no se envía, se imprime en la terminal del servidor. También puedes usar `.\venv\Scripts\flask.exe verificar-correo tu-correo@sanmateo.edu.co`.
