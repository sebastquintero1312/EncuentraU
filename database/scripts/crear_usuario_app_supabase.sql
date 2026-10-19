-- Crea el usuario de la aplicación (encuentrau_app) en SUPABASE.
--
-- Se ejecuta UNA vez en el "SQL Editor" del proyecto de Supabase, ANTES de
-- la migración (flask db upgrade), reemplazando CAMBIAR_CLAVE_APP por una
-- contraseña larga y aleatoria, por ejemplo:
--   python -c "import secrets; print(secrets.token_urlsafe(32))"
-- No guardar este archivo con la contraseña escrita.
--
-- En Supabase el dueño de las tablas es el usuario "postgres" del proyecto
-- (equivale a "encuentrau" en local): las migraciones se ejecutan con él.
-- encuentrau_app solo recibe permisos mínimos, que asigna 06_permisos.sql.
--
-- Para conectarse por el pooler de Supabase, el usuario se escribe como
-- "encuentrau_app.<id-del-proyecto>".

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'encuentrau_app') THEN
        CREATE ROLE encuentrau_app LOGIN PASSWORD 'CAMBIAR_CLAVE_APP'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    ELSE
        ALTER ROLE encuentrau_app PASSWORD 'CAMBIAR_CLAVE_APP';
    END IF;
END $$;
