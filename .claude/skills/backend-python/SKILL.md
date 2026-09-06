---
name: backend-python
description: Guía para desarrollar y revisar el backend Python + Flask + SQLAlchemy de EncuentraU v1.0.
---

# SKILL: Backend Python

## 1. Propósito

Guiar el desarrollo, revisión y mejora del backend de EncuentraU usando Python, Flask y SQLAlchemy. Esta Skill aplica tanto a la comprensión del backend actual (v0.25) como al desarrollo del backend objetivo (v1.0).

## 2. Cuándo utilizarla

- Al agregar o modificar rutas, controladores o servicios.
- Al migrar el almacenamiento de memoria a SQLAlchemy.
- Al revisar validaciones o manejo de errores.
- Al depurar problemas en el backend.
- Al revisar la configuración de Flask.

## 3. Tecnologías objetivo

- **Python 3.10+**
- **Flask 3.x** — framework web
- **SQLAlchemy 2.x** — ORM para base de datos
- **Flask-Limiter** — rate limiting
- **Flask-WTF** — protección CSRF
- **Flask-CORS** — control de CORS
- **python-dotenv** — variables de entorno

## 4. Qué debe revisar

### Rutas
- [ ] ¿Están agrupadas en Blueprints?
- [ ] ¿Definen solo URL y método HTTP?
- [ ] ¿Tienen rate limiting donde corresponde?
- [ ] ¿Están protegidas con CSRF donde deben estarlo?
- [ ] ¿Requieren autenticación cuando lo necesitan?

### Controladores
- [ ] ¿Solo coordinan: leen request, llaman servicio, devuelven response?
- [ ] ¿Manejan errores de forma segura (sin exponer stack traces)?
- [ ] ¿Validan todos los campos de entrada?
- [ ] ¿Los mensajes de error no revelan información sensible?

### Servicios
- [ ] ¿Contienen la lógica de negocio completa?
- [ ] ¿Son independientes de Flask (no usan request/jsonify)?
- [ ] ¿Las transacciones de BD hacen commit/rollback correctamente?
- [ ] ¿Manejan casos borde?

### Modelos (SQLAlchemy)
- [ ] ¿Heredan de db.Model?
- [ ] ¿Tienen __tablename__ definido?
- [ ] ¿Los campos tienen tipos correctos?
- [ ] ¿Las relaciones están definidas con relationship()?
- [ ] ¿Las claves foráneas tienen restricciones correctas?
- [ ] ¿Los campos obligatorios tienen nullable=False?

### Validación
- [ ] ¿Se valida en el backend (no solo en frontend)?
- [ ] ¿Los campos obligatorios se verifican?
- [ ] ¿Los tipos de datos se verifican?
- [ ] ¿Las longitudes máximas se verifican?
- [ ] ¿Los formatos (correo, etc.) se verifican con regex?

### Errores
- [ ] ¿Los errores 400/401/403/404/500 están manejados?
- [ ] ¿Los errores no exponen información interna?
- [ ] ¿Se registra suficiente información para depurar (sin datos sensibles)?

### Configuración
- [ ] ¿SECRET_KEY viene de variable de entorno?
- [ ] ¿DEBUG=False en producción?
- [ ] ¿La URL de BD viene de variable de entorno?
- [ ] ¿FLASK_ENV distingue dev/producción?

### Transacciones
- [ ] ¿Se usa db.session correctamente?
- [ ] ¿Los errores hacen rollback?
- [ ] ¿Las operaciones múltiples están en una sola transacción?

## 5. Reglas obligatorias

1. Nunca poner lógica de negocio en rutas o controladores.
2. Nunca exponer stack traces en respuestas de producción.
3. Nunca guardar contraseñas en texto plano.
4. Siempre validar en el backend, independientemente del frontend.
5. Nunca poner secrets en el código fuente.
6. Usar consultas parametrizadas (SQLAlchemy previene SQL Injection).
7. Los mensajes de error no revelan si un usuario existe o no.

## 6. Procedimiento de adición de funcionalidad

```
1. Definir la ruta en routes/ (URL, método, límites)
2. Crear el controlador en controllers/ (leer, validar, llamar, responder)
3. Crear el servicio en services/ (lógica de negocio)
4. Crear/actualizar el modelo en models/ (datos)
5. Escribir tests en tests/
6. Ejecutar los tests
7. Actualizar docs/API.md y docs/BACKEND.md
```

## 7. Checklist de un endpoint correcto

- [ ] Ruta definida en Blueprint con método HTTP correcto
- [ ] Rate limiting aplicado si es operación sensible
- [ ] CSRF requerido si modifica datos
- [ ] Autenticación verificada si requiere login
- [ ] Autorización verificada si requiere rol específico
- [ ] Todos los campos de entrada validados
- [ ] Errores retornan códigos HTTP correctos (400/401/403/404/500)
- [ ] Errores no exponen información interna
- [ ] Test escrito y ejecutado con evidencia

## 8. Criterios de finalización

Un endpoint está completo cuando:
- Pasa todos los tests (unit + integration).
- Maneja correctamente los casos de error.
- No expone información sensible.
- Está documentado en docs/API.md.

## 9. Errores que debe evitar

- Migrar al backend de SQLAlchemy sin antes hacer la auditoría completa.
- Cambiar el esquema de datos sin migraciones.
- Olvidar cerrar sesiones de SQLAlchemy.
- Dejar DEBUG=True en producción.
- Confirmar que algo funciona sin ejecutarlo.
- Usar `random` en lugar de `secrets` para tokens.

## 10. Documentación que debe actualizar

- `docs/BACKEND.md` — al agregar o modificar funcionalidades.
- `docs/API.md` — al agregar o modificar endpoints.
- `docs/CHANGELOG.md` — al hacer cambios significativos.
- `docs/DATABASE.md` — al modificar modelos.
