# VERSION_2.0.md — Informe de EncuentraU v2.0

**Fecha**: 2026-10-16 · Informe anterior: `docs/VERSION_1.0.md` (se conserva como historia).

## 1. Qué se pidió

1. Base de datos nueva, normalizada, con ACID y concurrencia, índices, respaldos, procedimientos, triggers, auditoría de todos los cambios e integración con aplicaciones y nube (temas vistos en clase).
2. Tres roles con permisos distintos: estudiante, encargado de la oficina y un tercero (se eligió **administrador**, sin funciones operativas).
3. Una solución al problema "veo un objeto y digo que es mío".
4. Verificación del correo institucional y seguimiento por correo.
5. Rediseño completo del frontend con el estilo del sitio de la universidad.
6. Sin despliegue todavía (fase siguiente).

## 2. Qué se entregó

| Pedido | Dónde | Estado |
|---|---|---|
| Normalización 3FN | `docs/DATABASE.md` §3, `docs/DIAGRAMAS.md` §1 | VERIFICADO |
| ACID y concurrencia | procedimientos con `FOR UPDATE`, columna `version`, índices únicos parciales; `test_concurrencia.py` | VERIFICADO |
| Índices | 8 tipos documentados; `test_indices_especiales_existen`, plan con `EXPLAIN` | VERIFICADO |
| Respaldos | `respaldo.py` / `restaurar.py` (probados) y respaldo diario cifrado en GitHub Actions | Local VERIFICADO · nube IMPLEMENTADO |
| Procedimientos y triggers | `03_procedimientos.sql`, `02_funciones_triggers.sql` | VERIFICADO |
| Auditoría de todos los cambios | trigger en 8 tablas, inmutable, panel del administrador | VERIFICADO |
| Integración con apps y nube | API REST documentada, CSV, usuario lector, Brevo, Supabase, GitHub Actions | CSV VERIFICADO · resto IMPLEMENTADO |
| Tres roles | `docs/AUTHORIZATION.md` §2; `test_roles.py` | VERIFICADO |
| Reclamaciones seguras | `docs/AUTHORIZATION.md` §4; `test_reclamaciones.py`, E2E | VERIFICADO |
| Correo institucional verificado + avisos | `docs/AUTHENTICATION.md`; `test_auth.py`, `test_notificaciones.py` | VERIFICADO (envío real por Brevo IMPLEMENTADO) |
| Rediseño del frontend | 25 páginas; `docs/FRONTEND.md`; capturas en `docs/evidencia/capturas_v2/` | VERIFICADO |

## 3. Evidencia

- `docs/evidencia/pytest_v2.0.txt`: suite completa sobre PostgreSQL, la app conectada con el usuario de permisos mínimos.
- `docs/evidencia/e2e_navegador_v2.0.txt`: flujo completo con los tres roles en Microsoft Edge, sin errores de JavaScript ni de CSP.
- `docs/evidencia/respaldo_restauracion_v2.0.txt`: respaldo y restauración con conteos idénticos.
- `docs/evidencia/capturas_v2/`: 17 capturas de pantalla.

Todo se ejecutó en un servidor **PostgreSQL 18.6 temporal** creado con los binarios instalados en el equipo y con los mismos scripts del proyecto (`crear_bd_local.sql`, `flask db upgrade`), porque el servidor PostgreSQL del propietario requiere su contraseña de superusuario. Hay que repetir la ejecución allí (ver README).

## 4. Bugs encontrados y corregidos

1. Debug activado por defecto cuando `FLASK_ENV` no está definida (heredado de v1.0; la regla RU-081 lo daba por verificado solo por lectura del comentario).
2. Nombre de función repetido en `solicitudes_service.py` (lo detectó pytest).

## 5. Limitaciones conocidas

1. **Despliegue**: en línea en https://encuentrau.onrender.com desde el 2026-10-19; faltan los secretos del respaldo diario (ver `docs/DEPLOYMENT.md`).
2. Brevo, el respaldo en la nube, la CI y el endurecimiento de Supabase están escritos pero no ejecutados.
3. Los correos de un remitente genérico pueden llegar a spam en `@sanmateo.edu.co`.
4. Límite de peticiones en memoria.
5. Un impostor que conozca bien el objeto puede describirlo; la barrera final es la prueba presencial.
6. Sin segundo factor, sin escaneo automático de dependencias, sin monitoreo centralizado.
7. El logo y los colores son de la universidad: el pie aclara que es un proyecto académico, pero conviene pedir autorización antes de publicarlo.

## 6. Reglas

`docs/REGLAS_100.md`: 91 VERIFICADO, 1 PARCIAL, 2 IMPLEMENTADO, 3 BLOQUEADO (requieren producción), 3 NO_APLICA, más 20 controles nuevos de v2.0.

## 7. Siguiente paso

Desplegar: Supabase (base de datos) + Render (web) + Brevo (correos) + secretos de GitHub, siguiendo `docs/DEPLOYMENT.md`, y repetir las verificaciones contra la URL pública.
