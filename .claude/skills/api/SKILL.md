---
name: api
description: Guía para diseñar, implementar y documentar la API REST de EncuentraU.
---

# SKILL: API

## 1. Propósito

Guiar el diseño, implementación y documentación de la API REST de EncuentraU. Una API bien diseñada es predecible, segura y fácil de consumir desde el frontend.

## 2. Cuándo utilizarla

- Al agregar nuevos endpoints.
- Al revisar endpoints existentes.
- Al documentar la API en docs/API.md.
- Al diseñar respuestas de error.
- Al implementar paginación.

## 3. Principios de diseño REST

### Métodos HTTP correctos
| Método | Uso | Idempotente |
|--------|-----|-------------|
| GET | Leer recursos | Si |
| POST | Crear recursos | No |
| PUT | Reemplazar recurso | Si |
| PATCH | Modificar parcialmente | No |
| DELETE | Eliminar recurso | Si |

### Códigos HTTP correctos
| Código | Significado | Cuándo usarlo |
|--------|-------------|---------------|
| 200 | OK | Lectura exitosa, actualización exitosa |
| 201 | Created | Recurso creado exitosamente |
| 204 | No Content | Eliminación exitosa (sin body) |
| 400 | Bad Request | Error de validación, datos incorrectos |
| 401 | Unauthorized | No autenticado |
| 403 | Forbidden | Autenticado pero sin permiso |
| 404 | Not Found | Recurso no existe |
| 409 | Conflict | Conflicto (correo ya existe) |
| 429 | Too Many Requests | Rate limit alcanzado |
| 500 | Internal Server Error | Error del servidor |

### URLs de recursos
```
/api/auth/...          # Autenticación
/api/objetos           # Colección de objetos
/api/objetos/:id       # Objeto específico
/api/mis-reportes      # Reportes del usuario actual
/api/solicitudes       # Solicitudes
/api/admin/...         # Endpoints de administrador
```

## 4. Formato de respuestas

### Respuesta de éxito (lista)
```json
{
  "datos": [...],
  "total": 50,
  "pagina": 1,
  "por_pagina": 10
}
```

### Respuesta de éxito (recurso único)
```json
{
  "mensaje": "Operación exitosa",
  "objeto": {...}
}
```

### Respuesta de error
```json
{
  "mensaje": "Descripción del error",
  "errores": {
    "campo": "Error específico del campo"
  }
}
```

El campo "errores" es opcional y solo aparece cuando hay errores de validación por campo.

## 5. Qué debe revisar

### Diseño
- [ ] ¿Los métodos HTTP son correctos para cada operación?
- [ ] ¿Las URLs son consistentes y descriptivas?
- [ ] ¿Los códigos HTTP son correctos?
- [ ] ¿Las respuestas tienen formato consistente?

### Validación
- [ ] ¿Se validan todos los campos de entrada?
- [ ] ¿Se validan tipos, longitudes y formatos?
- [ ] ¿Los errores de validación retornan 400 con detalle?

### Autenticación y autorización
- [ ] ¿Los endpoints protegidos verifican sesión?
- [ ] ¿Los endpoints de admin verifican rol?
- [ ] ¿Los endpoints retornan 401/403 correctamente?

### Paginación
- [ ] ¿Las listas tienen paginación?
- [ ] ¿Hay límite máximo de resultados por página?
- [ ] ¿El cliente puede especificar página y tamaño?

### Errores
- [ ] ¿Los errores 400/401/403/404/500 están manejados?
- [ ] ¿Los errores no exponen detalles internos?
- [ ] ¿Los errores tienen mensajes útiles para el frontend?

### Rate Limiting
- [ ] ¿Los endpoints sensibles tienen rate limit?
- [ ] ¿Los límites son razonables?

## 6. Reglas obligatorias

1. Todos los endpoints que retornan datos sensibles requieren autenticación.
2. Los errores nunca exponen stack traces o detalles internos.
3. Las listas siempre están paginadas.
4. Los mensajes de error son en español (es un proyecto académico).
5. Las respuestas de error tienen formato consistente.
6. Los endpoints de escritura (POST/PUT/DELETE) tienen CSRF protegido.

## 7. Endpoints actuales en v0.25

| Método | Ruta | Descripción | Rate Limit | CSRF |
|--------|------|-------------|-----------|------|
| GET | /api/auth/csrf-token | Token CSRF | — | — |
| POST | /api/auth/registro | Registrar | 5/min | Si |
| POST | /api/auth/login | Login | 10/min | Si |
| POST | /api/auth/logout | Logout | — | Si |
| GET | /api/auth/sesion | Sesión actual | — | — |
| POST | /api/auth/recuperar | Recuperar contraseña | 5/min | Si |
| POST | /api/auth/restablecer | Restablecer contraseña | 5/min | Si |

## 8. Endpoints pendientes para v1.0

- GET/POST /api/objetos
- GET/PUT/DELETE /api/objetos/:id
- GET /api/mis-reportes
- POST /api/solicitudes
- GET /api/mis-solicitudes
- GET/PUT /api/admin/solicitudes
- GET /api/admin/usuarios
- PUT /api/admin/usuarios/:id

## 9. Checklist de un endpoint correcto

- [ ] URL correcta y consistente con el resto de la API
- [ ] Método HTTP apropiado
- [ ] Validación completa de entrada
- [ ] Autenticación verificada si requiere login
- [ ] Autorización verificada si requiere rol
- [ ] Código HTTP de respuesta correcto
- [ ] Formato de respuesta consistente
- [ ] Rate limiting si es sensible
- [ ] CSRF si modifica datos
- [ ] Documentado en docs/API.md

## 10. Criterios de finalización

Un endpoint está correcto cuando:
- Retorna los códigos HTTP apropiados.
- Valida todos los campos de entrada.
- Los errores no exponen información interna.
- Está documentado en docs/API.md.
- Tiene test de integración.

## 11. Errores que debe evitar

- Retornar siempre 200 aunque haya errores.
- No paginar listas que pueden crecer.
- Exponer detalles de la base de datos en errores 500.
- Mezclar PUT y PATCH sin consistencia.
- Dejar endpoints sin documentación en docs/API.md.

## 12. Documentación que debe actualizar

- `docs/API.md` — al agregar o modificar cualquier endpoint.
