-- Crea los usuarios y las bases de datos LOCALES de EncuentraU.
--
-- Se ejecuta UNA sola vez, con el superusuario "postgres", desde la raíz del proyecto:
--
--   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -v clave=CLAVE_DUENO -v clave_app=CLAVE_APP -f database\scripts\crear_bd_local.sql
--
-- psql pedirá la contraseña de "postgres" (la que definiste al instalar PostgreSQL).
-- CLAVE_DUENO y CLAVE_APP deben coincidir con las que aparecen en backend/.env.
-- Este archivo NO contiene ninguna contraseña: las recibe como variables de psql.
--
-- Dos usuarios, por el principio de mínimo privilegio (least privilege):
--
--   encuentrau      Dueño de las bases de datos. Lo usan SOLO las migraciones
--                   (crear tablas, triggers, procedimientos) y los respaldos.
--   encuentrau_app  Usuario con el que se conecta la aplicación web. Solo puede
--                   leer, insertar y actualizar (los permisos exactos los asigna
--                   la migración). No puede borrar filas, ni modificar la tabla
--                   de auditoría, ni desactivar triggers, ni crear tablas.
--
-- Ninguno de los dos es superusuario.
-- Es seguro ejecutarlo más de una vez: lo que ya existe no se vuelve a crear
-- (las contraseñas sí se actualizan).

\set ON_ERROR_STOP on

-- 1. Usuario dueño (migraciones y respaldos)
SELECT format('CREATE ROLE encuentrau LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'clave')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'encuentrau')
\gexec

SELECT format('ALTER ROLE encuentrau PASSWORD %L', :'clave')
\gexec

-- 2. Usuario de la aplicación (permisos mínimos)
SELECT format('CREATE ROLE encuentrau_app LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT', :'clave_app')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'encuentrau_app')
\gexec

SELECT format('ALTER ROLE encuentrau_app PASSWORD %L', :'clave_app')
\gexec

-- 3. Base de datos de desarrollo (la que usa "python app.py")
SELECT 'CREATE DATABASE encuentrau_dev OWNER encuentrau ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'encuentrau_dev')
\gexec

-- 4. Base de datos de pruebas (la que usa pytest; se limpia en cada prueba)
SELECT 'CREATE DATABASE encuentrau_test OWNER encuentrau ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'encuentrau_test')
\gexec

\echo 'Listo: usuarios encuentrau / encuentrau_app y bases encuentrau_dev / encuentrau_test creados.'
