---
name: base-datos
description: Guía para el diseño, implementación y mantenimiento de la base de datos de EncuentraU usando SQLAlchemy.
---

# SKILL: Base de Datos

## 1. Propósito

Guiar el diseño e implementación de la base de datos de EncuentraU, incluyendo modelos SQLAlchemy, relaciones, migraciones y transacciones. Garantizar la integridad de los datos y la seguridad en las consultas.

## 2. Cuándo utilizarla

- Al diseñar o modificar modelos de datos.
- Al migrar de almacenamiento en memoria a SQLAlchemy.
- Al agregar relaciones entre tablas.
- Al diseñar consultas o filtros.
- Al implementar migraciones de esquema.

## 3. ESTADO ACTUAL (v0.25)

**NO hay base de datos real.** Los datos viven en memoria (listas Python).
- `models/usuario.py` — lista en memoria
- `models/token_recuperacion.py` — lista en memoria
- Se pierden al reiniciar el servidor.
- **NO modificar este estado durante la Fase 0.**

## 4. Qué debe cubrir (para v1.0)

### SQLAlchemy
- [ ] Extensión `SQLAlchemy` inicializada en `extensions.py`
- [ ] `db.Model` como clase base de todos los modelos
- [ ] Sesión gestionada correctamente

### Modelos
- [ ] `__tablename__` definido explícitamente
- [ ] Campos con tipos correctos (`String`, `Integer`, `DateTime`, `Boolean`, `Enum`)
- [ ] Longitudes máximas en `String`
- [ ] `nullable=False` en campos obligatorios
- [ ] `unique=True` donde corresponde (correo de usuario)
- [ ] `default` y `server_default` donde aplica
- [ ] `created_at` / `updated_at` con `datetime.utcnow`

### Relaciones
- [ ] Claves foráneas con `ForeignKey()`
- [ ] `relationship()` definido para acceso conveniente
- [ ] `cascade` configurado según el comportamiento deseado
- [ ] `back_populates` o `backref` para relaciones bidireccionales

### Claves e índices
- [ ] Clave primaria en cada tabla
- [ ] Índices en campos de búsqueda frecuente (correo, token)
- [ ] Índice único en correo de usuario

### Restricciones
- [ ] Restricciones CHECK donde aplica (ej: rol en ('ciudadano', 'administrador'))
- [ ] Restricciones de integridad referencial

### Migraciones
- [ ] Usar Flask-Migrate (Alembic) para cambios de esquema
- [ ] Nunca modificar directamente la BD en producción sin migración
- [ ] Mantener historial de migraciones

### Integridad y transacciones
- [ ] Operaciones múltiples agrupadas en una transacción
- [ ] Rollback en caso de error
- [ ] No dejar sesiones abiertas

## 5. Modelos necesarios en v1.0

### Usuario
```
id, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido,
correo (único), password_hash, rol, activo, created_at
```

### TokenRecuperacion
```
id, token (único, indexado), usuario_id (FK), expira_en, usado, created_at
```

### Objeto (reporte)
```
id, tipo (perdido/encontrado), nombre, categoria, descripcion,
ubicacion, fecha_evento, imagen_url, estado, usuario_id (FK), created_at, updated_at
```

### Solicitud
```
id, objeto_id (FK), solicitante_id (FK), mensaje, estado, created_at
```

## 6. Reglas obligatorias

1. Nunca poner consultas SQL directas fuera de los modelos.
2. Siempre usar parámetros de SQLAlchemy (previene SQL Injection automáticamente).
3. Nunca modificar el esquema en producción sin migración.
4. Siempre hacer rollback si una transacción falla.
5. No dejar sesiones de SQLAlchemy sin cerrar.
6. No modificar la base de datos actual durante la Fase 0.

## 7. Procedimiento de migración (memoria → SQLAlchemy)

```
1. Diseñar los modelos SQLAlchemy completos.
2. Revisar con el agente de arquitectura.
3. Crear la migración inicial con Flask-Migrate.
4. Adaptar los servicios para usar db.session en lugar de listas.
5. Verificar que el comportamiento es idéntico.
6. Escribir tests de integración.
7. Actualizar docs/DATABASE.md.
```

## 8. Checklist de un modelo correcto

- [ ] Hereda de `db.Model`
- [ ] `__tablename__` definido
- [ ] Clave primaria definida
- [ ] Campos obligatorios con `nullable=False`
- [ ] `created_at` con `default=datetime.utcnow`
- [ ] Relaciones definidas con `relationship()`
- [ ] Índices en campos de búsqueda

## 9. Criterios de finalización

La base de datos está correctamente implementada cuando:
- Los modelos reflejan el esquema real de la BD.
- Las migraciones permiten reproducir el esquema desde cero.
- Los tests de integración pasan con la BD real.
- No hay datos en memoria que deberían estar en BD.

## 10. Errores que debe evitar

- Modificar la base de datos en producción sin migración.
- Guardar contraseñas en la base de datos en texto plano.
- Usar `id` autoincremental predecible para tokens de seguridad.
- Olvidar `rollback()` cuando hay errores.
- Dejar campos sensibles sin restricciones (ej: rol sin Enum).

## 11. Documentación que debe actualizar

- `docs/DATABASE.md` — al modificar modelos o esquema.
- `docs/CHANGELOG.md` — al hacer cambios de esquema.
