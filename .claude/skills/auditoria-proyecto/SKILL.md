---
name: auditoria-proyecto
description: Analiza proyectos existentes antes de modificarlos. Genera un reporte honesto del estado real del sistema.
---

# SKILL: Auditoría de Proyecto

## 1. Propósito

Analizar exhaustivamente el proyecto EncuentraU en su estado actual (v0.25) antes de realizar cualquier modificación. Esta Skill garantiza que los cambios futuros partan de un conocimiento real y verificado del sistema, no de suposiciones.

## 2. Cuándo utilizarla

- Antes de comenzar cualquier fase de desarrollo nueva.
- Antes de migrar tecnologías (ej: de memoria a base de datos).
- Cuando hay dudas sobre qué está funcionando realmente.
- Al incorporarse un nuevo agente al proyecto.
- Al inicio de la transición v0.25 → v1.0.

## 3. Qué debe revisar

### Estructura del proyecto
- [ ] Carpetas y archivos existentes
- [ ] Organización de carpetas (frontend/backend/database/docs)
- [ ] Archivos de configuración (.env.example, .gitignore)
- [ ] Documentación existente

### Backend
- [ ] Punto de entrada (app.py)
- [ ] Fábrica de la aplicación (__init__.py)
- [ ] Configuración (config.py)
- [ ] Extensiones registradas (extensions.py)
- [ ] Rutas definidas (routes/)
- [ ] Controladores (controllers/)
- [ ] Servicios / lógica de negocio (services/)
- [ ] Modelos de datos (models/)
- [ ] Middlewares (middlewares/)

### Frontend
- [ ] Páginas HTML existentes
- [ ] Hojas de estilo (CSS)
- [ ] Scripts JavaScript
- [ ] Datos simulados / mocks
- [ ] Consumo de API real vs simulado

### Base de datos
- [ ] ¿Existe conexión a base de datos real?
- [ ] ¿Qué datos viven en memoria?
- [ ] ¿Existen scripts SQL?
- [ ] ¿Hay modelos ORM definidos?

### APIs
- [ ] Endpoints definidos y sus métodos HTTP
- [ ] Endpoints que funcionan vs endpoints que solo están declarados
- [ ] Formato de respuestas
- [ ] Autenticación requerida por endpoint

### Autenticación
- [ ] Mecanismo de registro
- [ ] Mecanismo de login
- [ ] Mecanismo de logout
- [ ] Gestión de sesiones
- [ ] Recuperación de contraseña
- [ ] Hashing de contraseñas (algoritmo usado)

### Autorización
- [ ] Roles definidos
- [ ] Verificación de roles en rutas
- [ ] Protección contra acceso no autorizado

### Pruebas
- [ ] ¿Existen tests escritos?
- [ ] ¿Existen tests ejecutados con evidencia?
- [ ] ¿Hay framework de pruebas configurado?

### Configuración y dependencias
- [ ] requirements.txt (backend)
- [ ] package.json (frontend, si aplica)
- [ ] Variables de entorno documentadas
- [ ] Dependencias con versiones fijas

### Código problemático
- [ ] Código duplicado
- [ ] Código muerto (nunca ejecutado)
- [ ] Mocks que deben reemplazarse
- [ ] TODOs / FIXMEs pendientes
- [ ] Funcionalidades incompletas
- [ ] Datos hardcodeados que deberían estar en configuración

### Riesgos
- [ ] Secretos en el código
- [ ] DEBUG=True en producción potencial
- [ ] Validaciones faltantes
- [ ] Datos en memoria (se pierden al reiniciar)

## 4. Reglas obligatorias

1. NO modificar ningún archivo durante la auditoría.
2. NO asumir que el código funciona: verificar cuándo sea posible.
3. NO inventar información: solo reportar lo observado.
4. Distinguir entre IMPLEMENTADO y VERIFICADO.
5. Reportar limitaciones honestamente.
6. Si algo no está claro, indicar la incertidumbre.

## 5. Procedimiento

### Paso 1: Inspección de estructura
```
Listar todos los archivos y carpetas del proyecto.
Registrar tamaños aproximados.
Identificar archivos inusuales o faltantes.
```

### Paso 2: Lectura del código backend
```
Leer app.py → __init__.py → config.py → extensions.py
Leer cada ruta en routes/
Leer cada controlador en controllers/
Leer cada servicio en services/
Leer cada modelo en models/
```

### Paso 3: Lectura del código frontend
```
Listar todas las páginas HTML.
Revisar JS: ¿hace peticiones reales a la API o usa datos simulados?
Identificar qué partes del frontend están conectadas al backend.
```

### Paso 4: Análisis de dependencias
```
Revisar requirements.txt.
Verificar si las dependencias tienen versiones fijas.
Identificar dependencias que faltan para v1.0.
```

### Paso 5: Clasificación de funcionalidades
```
Para cada funcionalidad identificada, asignar estado:
PENDIENTE / EN_DESARROLLO / IMPLEMENTADO / VERIFICADO / PARCIAL / BLOQUEADO / NO_APLICA
```

### Paso 6: Identificación de riesgos
```
Listar problemas de seguridad detectados.
Listar limitaciones conocidas.
Listar deuda técnica.
```

## 6. Checklist de finalización de auditoría

- [ ] Estructura completa documentada
- [ ] Cada archivo backend revisado
- [ ] Cada página frontend revisada
- [ ] Estado de cada funcionalidad asignado
- [ ] Riesgos listados
- [ ] `docs/ESTADO_V025.md` generado
- [ ] Ningún archivo fue modificado durante la auditoría

## 7. Criterios de finalización

La auditoría está completa cuando:
- Se puede responder con certeza qué funciona y qué no.
- `docs/ESTADO_V025.md` existe y refleja lo observado realmente.
- Se ha identificado qué es necesario para v1.0 y qué ya existe.

## 8. Errores que debe evitar

- Afirmar que algo funciona sin haberlo verificado.
- Modificar archivos durante la auditoría.
- Omitir limitaciones o problemas para "no preocupar".
- Confundir código escrito con funcionalidad probada.
- Generar `ESTADO_V025.md` con información ficticia o de relleno.

## 9. Documentación que debe actualizar

- Crear: `docs/ESTADO_V025.md` (resultado principal de la auditoría)
- No modificar otros documentos durante esta fase.
