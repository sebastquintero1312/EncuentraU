-- Usuario de SOLO LECTURA para conectar herramientas externas de análisis
-- (Excel, Power BI, Looker Studio, Metabase...) a EncuentraU.
--
-- Integración con otras aplicaciones sin riesgo: este usuario solo puede
-- leer las VISTAS de estadísticas, que no contienen datos personales. No
-- ve las tablas (correos, contraseñas, descripciones privadas, auditoría).
--
-- Se ejecuta como dueño de la base de datos (o como "postgres" en Supabase):
--   psql "<url del dueño>" -v clave_lector=UNA_CLAVE_LARGA -f database/scripts/crear_rol_lector.sql
--
-- Para crear el rol se necesita el permiso CREATEROLE (en local, hacerlo
-- con el superusuario "postgres"; en Supabase, desde el editor SQL).

\set ON_ERROR_STOP on

SELECT format('CREATE ROLE encuentrau_lector LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'clave_lector')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'encuentrau_lector')
\gexec

GRANT USAGE ON SCHEMA public TO encuentrau_lector;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM encuentrau_lector;
GRANT SELECT ON v_objetos_disponibles, v_estadisticas_generales, v_estadisticas_mensuales TO encuentrau_lector;

\echo 'Listo: encuentrau_lector solo puede leer las vistas de estadísticas.'
