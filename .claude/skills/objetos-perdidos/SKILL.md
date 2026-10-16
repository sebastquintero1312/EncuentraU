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

## 4. Estados (v2.0, como DATOS en `estados_objeto` / `transiciones_objeto`)

**Objeto encontrado**: `pendiente_entrega` (reportado, falta llevarlo a la oficina) → `en_oficina` (el encargado lo recibió; recién aquí se publica) → `reservado` (reclamación pre-aprobada) → `entregado`. También `cancelado` (antes de llevarlo) y `cerrado` (por la oficina). `reservado → en_oficina` si la reserva vence, se rechaza o se cancela.

**Objeto perdido**: `buscando` → `recuperado` (al entregarle un objeto con ese reporte vinculado) · `cancelado` · `cerrado`.

Un trigger de PostgreSQL rechaza cualquier transición que no esté en `transiciones_objeto`.

## 5. Estados de las reclamaciones

`pendiente` → `preaprobada` → `entregada`. Cierres: `rechazada` (cuenta para poner la cuenta en revisión), `cancelada`, `vencida`, `descartada` (el objeto se entregó a otra persona o se cerró).

## 6. Reglas del negocio (v2.0)

1. Solo estudiantes con correo verificado reportan y reclaman; el encargado y el administrador no.
2. La búsqueda requiere sesión de estudiante y muestra solo objetos encontrados que están en la oficina, con datos públicos (nunca la descripción privada, ni se filtra por ella).
3. Los reportes de pérdida no son públicos: los ven su dueño y la oficina.
4. Reclamación a ciegas: el estudiante describe el objeto sin ver los detalles; el encargado compara.
5. Una reclamación abierta por objeto y persona; máximo `max_solicitudes_abiertas`; con `max_rechazos` rechazos la cuenta queda en revisión.
6. Pre-aprobar no es entregar: código de un solo uso (HMAC), `max_intentos_codigo` intentos, `horas_vigencia_retiro` horas, entrega presencial con carné y prueba (`sp_registrar_entrega`).
7. Una coincidencia nunca transfiere propiedad ni cambia estados.

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

## 8. Endpoints

Ver `docs/API.md` (verificado contra el código por `test_documentacion_api.py`).

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
