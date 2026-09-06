# DATABASE.md — Base de datos de EncuentraU v1.0

## Motor

- **Desarrollo**: SQLite, archivo `backend/instance/encuentrau_dev.db` (creado automáticamente, ignorado por git).
- **Producción**: PostgreSQL, vía la variable de entorno `DATABASE_URL`. Si `DATABASE_URL` no está definida, `Config` usa SQLite; en producción (`FLASK_ENV=production`), la app rehúsa arrancar sin `DATABASE_URL` real (ver `backend/app/config/config.py`).
- **ORM**: SQLAlchemy 2.x vía Flask-SQLAlchemy. **Migraciones**: Flask-Migrate (Alembic), carpeta `backend/migrations/`.

## Esquema (4 tablas)

### `usuarios`
| Campo | Tipo | Notas |
|---|---|---|
| id | Integer | PK |
| primer_nombre | String(80) | obligatorio |
| segundo_nombre | String(80) | opcional, default `''` |
| primer_apellido | String(80) | obligatorio |
| segundo_apellido | String(80) | opcional, default `''` |
| correo | String(255) | **único**, indexado |
| password_hash | String(255) | Argon2id |
| rol | String(20) | `ciudadano` \| `administrador`, CHECK constraint |
| activo | Boolean | default `True`; `False` = cuenta desactivada por un admin |
| created_at | DateTime | default `utcnow` |

### `tokens_recuperacion`
| Campo | Tipo | Notas |
|---|---|---|
| id | Integer | PK |
| token | String(255) | único, indexado, generado con `secrets.token_urlsafe(32)` |
| usuario_id | Integer | FK → `usuarios.id` |
| expira_en | DateTime | `created_at + 30 minutos` |
| usado | Boolean | default `False`, se marca `True` tras un restablecimiento exitoso |
| created_at | DateTime | default `utcnow` |

### `objetos` (reportes de perdido/encontrado)
| Campo | Tipo | Notas |
|---|---|---|
| id | Integer | PK |
| tipo | String(20) | `perdido` \| `encontrado`, CHECK |
| nombre | String(120) | 3–120 caracteres |
| categoria | String(50) | whitelist fija (ver API.md), CHECK a nivel de aplicación (no de BD, para no tener que migrar el esquema si se agrega una categoría) |
| descripcion | String(300) | 10–300 caracteres |
| ubicacion | String(150) | 3–150 caracteres |
| fecha_evento | Date | no puede ser futura |
| imagen_url | String(500) | opcional, URL http(s) |
| estado | String(20) | `activo`\|`en_proceso`\|`resuelto`\|`cerrado`\|`cancelado`, CHECK, indexado |
| usuario_id | Integer | FK → `usuarios.id` (reportante) |
| created_at / updated_at | DateTime | `updated_at` con `onupdate=utcnow` |

### `solicitudes` (reclamaciones)
| Campo | Tipo | Notas |
|---|---|---|
| id | Integer | PK |
| objeto_id | Integer | FK → `objetos.id`, indexado |
| solicitante_id | Integer | FK → `usuarios.id`, indexado |
| contacto | String(150) | dato de contacto del solicitante |
| mensaje | String(400) | **privado**: información de verificación, solo visible para el dueño del objeto, el propio solicitante y un admin |
| estado | String(20) | `pendiente`\|`en_revision`\|`aprobada`\|`rechazada`\|`cancelada`, CHECK |
| respuesta_admin | String(300) | opcional, comentario del admin al resolver |
| created_at / updated_at | DateTime | |

## Relaciones

```
Usuario 1 ──< Objeto (usuario_id)         "mis reportes"
Usuario 1 ──< Solicitud (solicitante_id)  "mis solicitudes"
Objeto   1 ──< Solicitud (objeto_id)      "solicitudes recibidas"
Usuario 1 ──< TokenRecuperacion (usuario_id)
```

Todas definidas con `db.relationship(..., backref=db.backref(..., lazy='dynamic'))` para poder encadenar filtros (ej. `objeto.solicitudes.order_by(...)`).

## Integridad

- Claves foráneas reales (`ForeignKey`) en las 4 relaciones.
- `CheckConstraint` a nivel de base de datos para `rol`, `tipo`, `estado` de objeto y `estado` de solicitud — ni un bug en Python podría escribir un valor fuera de la lista permitida.
- Las transiciones de estado de un `Objeto` están además validadas en código (`TRANSICIONES_VALIDAS` en `models/objeto.py`), porque un CHECK constraint no puede expresar "de qué estado a qué estado", solo qué valores son válidos en general.
- No hay borrado físico (`hard delete`) de usuarios: se desactivan (`activo=False`) para no romper la integridad referencial con sus reportes y solicitudes existentes.
- Los reportes se **cancelan** (`estado=cancelado`), no se borran, para conservar el historial.

## Migraciones

```bash
cd backend
flask db init        # ya ejecutado una vez (carpeta migrations/ ya existe)
flask db migrate -m "descripción del cambio"
flask db upgrade      # aplica la migración pendiente
```

Migración inicial aplicada: `cc136ccba3dd_esquema_inicial_v1_0_usuarios_tokens_.py` (crea las 4 tablas, sus índices y sus CHECK constraints). Generada y aplicada realmente durante el desarrollo (no solo escrita a mano) — ver `docs/evidencia/`.

**Nunca** modificar el esquema de producción a mano; siempre generar una migración nueva con `flask db migrate` y revisarla antes de `flask db upgrade`.
