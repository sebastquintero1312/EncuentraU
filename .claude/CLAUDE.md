# CLAUDE.md — Instrucciones principales de EncuentraU

## Proyecto

**EncuentraU** — Plataforma universitaria para gestión de objetos perdidos y encontrados.

## Versión actual

**v2.0**

Estado: Flask + PostgreSQL (triggers, procedimientos, auditoría, permisos mínimos, RLS), tres roles (estudiante, encargado, administrador), reclamación con verificación a ciegas y código de retiro, verificación de correo institucional, frontend rediseñado con el estilo de sanmateo.edu.co. Verificado localmente (ver `docs/VERSION_2.0.md`). NO desplegado.

## Siguiente objetivo

Despliegue: Supabase (PostgreSQL) + Render (web) + Brevo (correos). Ver `docs/DEPLOYMENT.md`.

---

## Regla de continuidad

**No comenzar desde cero.** La versión actual existe y tiene trabajo real. Cada transformación debe partir del análisis de lo que ya hay, conservar lo que funciona bien, y mejorar o reemplazar solo lo que sea necesario.

Antes de cualquier cambio, leer:
- `docs/VERSION_2.0.md`
- `docs/ARQUITECTURA.md`
- La Skill correspondiente a la tarea

---

## Principios de desarrollo

1. **Código claro**: legible por un estudiante de quinto semestre. Sin sobre-ingeniería.
2. **Código mantenible**: separación de responsabilidades, nombres descriptivos, sin magia innecesaria.
3. **Seguridad**: tratada como requisito funcional, no como añadido posterior.
4. **Pruebas**: ninguna funcionalidad se declara terminada sin evidencia de que funciona.
5. **Documentación**: la documentación describe lo que el código hace realmente, no lo que se planea hacer.
6. **Simplicidad académica**: arquitectura comprensible, no perfecta en abstracto.

---

## Regla de seguridad

La seguridad es una prioridad, no una opción.

- Toda entrada del cliente es potencialmente maliciosa hasta que se valide.
- DENY BY DEFAULT: lo que no está explícitamente permitido está prohibido.
- LEAST PRIVILEGE: cada componente accede solo a lo que necesita.
- DEFENSE IN DEPTH: múltiples capas de protección.
- El frontend NUNCA es la autoridad de permisos ni de validación definitiva.

Ver: `.claude/skills/seguridad/SKILL.md` y `docs/REGLAS_100.md`

---

## Regla de verificación

**No afirmar que algo funciona sin comprobarlo.**

- Si una función fue escrita pero no ejecutada: estado IMPLEMENTADO, no VERIFICADO.
- Si una prueba fue diseñada pero no ejecutada: no marcarla como exitosa.
- Si no se tiene certeza de algo: indicar la incertidumbre explícitamente.
- Preferir "no sé / no verifiqué" sobre una afirmación falsa.

---

## Regla de documentación

La documentación debe coincidir con el código real.

- No documentar funcionalidades que no existen.
- No marcar como IMPLEMENTADO lo que solo está planificado.
- Si el código cambia, la documentación cambia también.
- Nunca generar documentación de relleno o ficticia.

---

## Regla de cambios

No realizar cambios grandes sin analizar primero sus consecuencias.

- Antes de modificar: identificar qué depende de eso.
- Cambios grandes = múltiples revisiones en partes pequeñas.
- Documentar qué cambió y por qué en `docs/CHANGELOG.md`.
- Si hay duda sobre el impacto: parar y consultar.

---

## Regla de desarrollo

Antes de modificar cualquier código:

1. **Entenderlo**: leer el código actual completo, no parcialmente.
2. **Identificar dependencias**: ¿qué lo usa? ¿de qué depende?
3. **Identificar riesgos**: ¿qué puede romperse? ¿hay datos en juego?
4. **Modificar**: hacer el cambio mínimo necesario.
5. **Probar**: ejecutar pruebas reales, no afirmar que funciona.
6. **Documentar**: actualizar `CHANGELOG.md` y la documentación relevante.

---

## Regla de finalización

Una funcionalidad **no está terminada** porque el código haya sido escrito.

Está terminada cuando:
- [ ] Funciona: se puede demostrar que opera correctamente.
- [ ] Probada: existe evidencia real de ejecución (no solo código de prueba).
- [ ] Revisada: el código fue revisado para detectar problemas.
- [ ] Documentada: la documentación refleja el estado actual.

---

## Sistema de estados

| Estado | Significado |
|--------|-------------|
| PENDIENTE | No comenzado. |
| EN_DESARROLLO | En progreso activo. |
| IMPLEMENTADO | Código escrito, NO verificado en ejecución. |
| VERIFICADO | Funciona con evidencia real de ejecución. |
| PARCIAL | Incompleto o con limitaciones conocidas. |
| BLOQUEADO | No puede avanzar por dependencias no resueltas. |
| NO_APLICA | No aplica a este proyecto/fase. |

**CRÍTICO**: IMPLEMENTADO ≠ VERIFICADO. Nunca usar VERIFICADO sin evidencia.

---

## Skills disponibles

| Skill | Cuándo usarla |
|-------|--------------|
| auditoria-proyecto | Al analizar el proyecto antes de modificarlo |
| arquitectura | Al revisar o modificar la estructura del sistema |
| backend-python | Al trabajar con Flask/Python |
| frontend | Al trabajar con HTML/CSS/JS |
| base-datos | Al trabajar con modelos o base de datos |
| autenticacion | Al trabajar con login, registro, sesiones |
| autorizacion | Al trabajar con roles y permisos |
| seguridad | En cualquier decisión de seguridad |
| objetos-perdidos | Al trabajar con la lógica de negocio principal |
| api | Al diseñar o modificar endpoints |
| pruebas | Al escribir o ejecutar pruebas |
| seguridad-ofensiva-defensiva | Al hacer pruebas de seguridad controladas |
| documentacion | Al crear o actualizar documentación |
| despliegue | Al preparar el proyecto para producción |

---

## Agentes disponibles

| Agente | Responsabilidad |
|--------|----------------|
| auditor | Análisis sin modificación |
| arquitectura | Revisión de estructura del sistema |
| backend | Backend Python/Flask |
| frontend | Interfaz de usuario |
| seguridad | Auditoría de seguridad |
| base-datos | Modelos y base de datos |
| testing | Pruebas y evidencia |
| revisor-final | Revisión independiente antes de declarar v1.0 |

---

## Tecnología actual (v2.0)

- Frontend: HTML + CSS + JavaScript vanilla (estilo de sanmateo.edu.co; fuentes e íconos locales; CSP estricta)
- Backend: Python 3.11 + Flask
- Base de datos: PostgreSQL en todos los entornos (SQLAlchemy + Alembic; esquema en `backend/migrations/sql/`)
- Autenticación: Flask session + Argon2id + verificación de correo institucional
- Roles: estudiante, encargado, administrador (separación de funciones)
- Seguridad activa: Flask-Limiter, Flask-WTF (CSRF), Flask-CORS, ProxyFix configurable, usuario de BD con permisos mínimos, RLS, auditoría por triggers

---

*Última actualización: v2.0 (2026-10-16)*
