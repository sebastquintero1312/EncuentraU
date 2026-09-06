---
name: documentacion
description: Guía para crear y mantener la documentación de EncuentraU. La documentación debe describir siempre el estado real del código.
---

# SKILL: Documentación

## 1. Propósito

Garantizar que toda la documentación de EncuentraU sea honesta, precisa y útil. La documentación describe lo que el sistema HACE HOY, no lo que se planea hacer. Documenta limitaciones conocidas con la misma honestidad que los logros.

## 2. Cuándo utilizarla

- Al crear documentación nueva.
- Al actualizar documentación existente después de un cambio.
- Al revisar que la documentación coincide con el código.
- Antes de declarar una fase completa.

## 3. Qué debe garantizar

### README
- [ ] ¿Describe claramente qué es el proyecto?
- [ ] ¿Tiene instrucciones de instalación correctas y probadas?
- [ ] ¿Lista las dependencias necesarias?
- [ ] ¿Indica cómo ejecutar el proyecto?
- [ ] ¿Indica el estado actual (v0.25, limitaciones)?

### SECURITY
- [ ] ¿Lista las medidas de seguridad implementadas?
- [ ] ¿Lista las limitaciones conocidas honestamente?
- [ ] ¿Indica qué NO está implementado todavía?

### ARCHITECTURE
- [ ] ¿Coincide con la estructura real de carpetas?
- [ ] ¿Describe las tecnologías correctas?
- [ ] ¿Explica la separación de responsabilidades?

### CHANGELOG
- [ ] ¿Registra todos los cambios significativos?
- [ ] ¿Tiene fecha y versión?
- [ ] ¿Distingue entre funcionalidades completas y parciales?

### API
- [ ] ¿Lista todos los endpoints implementados?
- [ ] ¿Tiene ejemplos de request y response?
- [ ] ¿Indica qué requiere autenticación?
- [ ] ¿Indica los códigos de respuesta?

### TESTING
- [ ] ¿Indica cómo ejecutar las pruebas?
- [ ] ¿Lista qué está probado y con qué cobertura?
- [ ] ¿Indica qué pruebas fueron ejecutadas con evidencia?

### DATABASE
- [ ] ¿Describe el esquema de la base de datos?
- [ ] ¿Describe las relaciones entre tablas?
- [ ] ¿Indica el estado actual (en memoria vs BD real)?

## 4. Reglas obligatorias

1. Nunca documentar una funcionalidad que no existe.
2. Nunca omitir limitaciones conocidas.
3. Si hay incertidumbre sobre si algo funciona: indicarlo.
4. La documentación se actualiza en el mismo commit que el código.
5. Usar el sistema de estados: PENDIENTE / IMPLEMENTADO / VERIFICADO.
6. Si la documentación contradice el código, el código tiene razón.

## 5. Formato de documentos

### Encabezado estándar
```markdown
# Título del documento

**Proyecto**: EncuentraU
**Versión**: v0.25
**Última actualización**: [fecha]
**Estado**: [estado del documento]
```

### Sección de limitaciones
Todos los documentos de estado deben tener una sección "Limitaciones conocidas" o "Lo que NO está implementado todavía" si aplica.

### Sistema de estados en documentación
```markdown
- [x] Funcionalidad A — VERIFICADO (prueba ejecutada el DD/MM/AAAA)
- [~] Funcionalidad B — IMPLEMENTADO (código escrito, no probado en este entorno)
- [ ] Funcionalidad C — PENDIENTE
```

## 6. Documentos del proyecto

| Documento | Propósito | Quién lo actualiza |
|-----------|-----------|-------------------|
| README.md | Introducción y guía de inicio | Cualquier agente |
| SECURITY.md | Medidas de seguridad | Agente de seguridad |
| ARCHITECTURE.md | Estructura del sistema | Agente de arquitectura |
| CHANGELOG.md | Historial de cambios | Cualquier agente |
| docs/API.md | Endpoints de la API | Agente de backend |
| docs/TESTING.md | Estrategia y resultados de pruebas | Agente de testing |
| docs/DATABASE.md | Esquema de base de datos | Agente de base de datos |
| docs/ESTADO_V025.md | Auditoría de v0.25 | Agente auditor |
| docs/VERSION_1.0.md | Definición de v1.0 | Revisión conjunta |
| docs/REGLAS_100.md | 100 reglas de seguridad | Agente de seguridad |
| docs/MATRIZ_SEGURIDAD.md | Estado de seguridad | Agente de seguridad |

## 7. Checklist de documentación completa

- [ ] README.md actualizado y correcto
- [ ] SECURITY.md refleja el estado real de seguridad
- [ ] ARCHITECTURE.md coincide con la estructura actual
- [ ] CHANGELOG.md tiene los cambios de esta fase
- [ ] docs/API.md lista todos los endpoints implementados
- [ ] docs/TESTING.md indica qué se probó
- [ ] docs/ESTADO_V025.md refleja la auditoría real
- [ ] Ningún documento tiene información ficticia o de relleno

## 8. Criterios de finalización

La documentación está completa cuando:
- Todos los documentos listados existen.
- Ningún documento contradice el código real.
- Las limitaciones conocidas están documentadas.
- El estado de cada funcionalidad es correcto.

## 9. Errores que debe evitar

- Generar documentación de "relleno" sin contenido real.
- Copiar información planificada como si fuera implementada.
- Omitir limitaciones para que el proyecto "se vea mejor".
- Documentar endpoints que no existen.
- Dejar documentación desactualizada después de cambios.

## 10. Documentación que debe actualizar

Esta Skill aplica a TODA la documentación del proyecto.
Siempre actualizar CHANGELOG.md con cualquier cambio de documentación significativo.
