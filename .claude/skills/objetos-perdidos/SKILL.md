---
name: objetos-perdidos
description: Guía para implementar la lógica de negocio principal de EncuentraU: reportes de objetos perdidos y encontrados, búsqueda, coincidencias y reclamaciones.
---

# SKILL: Objetos Perdidos

## 1. Propósito

Guiar la implementación de la lógica de negocio central de EncuentraU. Esta Skill define cómo deben funcionar los reportes, la búsqueda, las coincidencias y el proceso de reclamación de objetos.

## 2. Cuándo utilizarla

- Al implementar el módulo de reportes de objetos.
- Al diseñar el sistema de búsqueda y filtros.
- Al implementar el proceso de coincidencias.
- Al diseñar el flujo de reclamaciones.
- Al definir estados de objetos y transiciones permitidas.

## 3. Definiciones del dominio

### Objeto perdido
Un usuario reporta haber perdido un objeto. Proporciona descripción, categoría, ubicación y fecha aproximada.

### Objeto encontrado
Un usuario reporta haber encontrado un objeto. Proporciona descripción, categoría, ubicación y fecha.

### Reporte
Es el registro en el sistema de un objeto perdido o encontrado. Tiene un estado y pertenece a un usuario.

### Coincidencia (POSIBLE COINCIDENCIA)
El sistema identifica que un objeto perdido y un objeto encontrado podrían ser el mismo. Una coincidencia NO significa automáticamente propiedad. Es solo una pista.

### Solicitud de reclamación
Un usuario cree que un objeto encontrado es suyo y inicia el proceso de verificación. Debe pasar por verificación antes de ser aprobada.

### Verificación de propiedad
Proceso de confirmar que un objeto pertenece a quien lo reclama. Puede requerir descripción de características únicas no públicas.

## 4. Estados de los objetos

| Estado | Descripción | Quién puede establecerlo |
|--------|-------------|--------------------------|
| activo | Reporte activo buscando dueño/objeto | Sistema al crear |
| en_proceso | Hay una solicitud pendiente de verificación | Sistema automático |
| resuelto | El objeto fue devuelto a su dueño | Admin o sistema |
| cerrado | Cerrado sin resolución (tiempo expirado, etc.) | Admin |
| cancelado | Cancelado por el usuario que lo reportó | Usuario o Admin |

### Transiciones permitidas

```
activo → en_proceso (cuando hay solicitud)
activo → cancelado (el usuario cancela)
en_proceso → resuelto (verificación exitosa)
en_proceso → activo (solicitud rechazada)
activo/en_proceso → cerrado (admin cierra)
```

## 5. Estados de las solicitudes

| Estado | Descripción |
|--------|-------------|
| pendiente | Enviada, esperando revisión |
| en_revision | Admin revisando |
| aprobada | Verificación exitosa |
| rechazada | No se pudo verificar propiedad |
| cancelada | Cancelada por el solicitante |

## 6. Reglas del negocio

### Reportes
1. Solo usuarios autenticados pueden crear reportes.
2. Un usuario puede ver sus propios reportes.
3. Todos los usuarios pueden ver los reportes activos de otros (información pública).
4. Solo el dueño del reporte o un admin puede modificarlo.
5. Solo el dueño del reporte o un admin puede cancelarlo.

### Búsqueda
1. La búsqueda es pública (no requiere autenticación).
2. Se puede filtrar por: tipo, categoría, ubicación, fecha, estado.
3. La búsqueda de texto es sobre nombre y descripción.

### Coincidencias
1. Una POSIBLE COINCIDENCIA es solo una sugerencia del sistema.
2. La coincidencia NO transfiere propiedad automáticamente.
3. El usuario debe iniciar una solicitud de reclamación.
4. La solicitud pasa por verificación.

### Solicitudes de reclamación
1. Solo un usuario autenticado puede crear una solicitud.
2. Un usuario no puede reclamar su propio reporte.
3. Solo puede haber una solicitud activa por objeto por usuario.
4. El solicitante debe describir características únicas del objeto.
5. El admin revisa y aprueba o rechaza.
6. Una aprobación cambia el estado del objeto a 'resuelto'.

## 7. Qué debe revisar

### Autenticación y autorización
- [ ] ¿Los endpoints de creación requieren login?
- [ ] ¿Los endpoints de modificación verifican ownership?
- [ ] ¿Los endpoints de admin verifican rol?

### Seguridad de datos
- [ ] ¿No se expone información del reportante en búsquedas públicas? (solo nombre, no correo)
- [ ] ¿Las imágenes se validan si hay upload?
- [ ] ¿Los filtros de búsqueda son seguros contra injection?

### Lógica de negocio
- [ ] ¿Las transiciones de estado son válidas?
- [ ] ¿Un usuario no puede reclamar su propio objeto?
- [ ] ¿Una coincidencia no transfiere propiedad automáticamente?
- [ ] ¿Una solicitud aprobada cambia el estado del objeto?

### Paginación
- [ ] ¿Los resultados de búsqueda están paginados?
- [ ] ¿Hay límite al número de resultados por página?

## 8. Endpoints necesarios (v1.0)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | /api/objetos | Listar/buscar objetos | No |
| POST | /api/objetos | Crear reporte | Si |
| GET | /api/objetos/:id | Ver detalle | No |
| PUT | /api/objetos/:id | Actualizar reporte | Si (owner/admin) |
| DELETE | /api/objetos/:id | Cancelar reporte | Si (owner/admin) |
| GET | /api/mis-reportes | Mis reportes | Si |
| POST | /api/solicitudes | Crear solicitud | Si |
| GET | /api/mis-solicitudes | Mis solicitudes | Si |
| GET | /api/admin/solicitudes | Ver todas | Si (admin) |
| PUT | /api/admin/solicitudes/:id | Aprobar/rechazar | Si (admin) |

## 9. Checklist de implementación

- [ ] Modelo de Objeto/Reporte creado con todos los campos
- [ ] Modelo de Solicitud creado con todos los campos
- [ ] Estados definidos como Enum
- [ ] Transiciones de estado validadas en el servicio
- [ ] Endpoints de reportes implementados y protegidos
- [ ] Búsqueda con filtros implementada y paginada
- [ ] Sistema de solicitudes implementado
- [ ] Verificación de ownership en modificaciones
- [ ] Un usuario no puede reclamar su propio objeto
- [ ] Tests escritos y ejecutados

## 10. Criterios de finalización

El módulo de objetos perdidos está completo cuando:
- Se pueden crear, ver, buscar y gestionar reportes.
- El proceso de reclamación completo funciona.
- Las transiciones de estado son correctas.
- Los permisos están correctamente verificados.
- Los tests pasan.

## 11. Errores que debe evitar

- Aprobar automáticamente solicitudes sin verificación.
- Permitir que una coincidencia transfiera propiedad sin proceso.
- Exponer el correo del reportante en búsquedas públicas.
- Permitir que un usuario reclame su propio objeto.
- Omitir la verificación de ownership al modificar reportes.

## 12. Documentación que debe actualizar

- `docs/API.md` — al implementar endpoints de objetos.
- `docs/BACKEND.md` — al implementar la lógica de negocio.
