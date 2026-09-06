---
name: arquitectura
description: Revisa y documenta la arquitectura del sistema EncuentraU. Prioriza comprensibilidad para estudiantes de quinto semestre.
---

# SKILL: Arquitectura

## 1. Propósito

Revisar, documentar y guiar las decisiones de arquitectura de EncuentraU. Asegurar que la estructura del sistema sea comprensible, mantenible y escalable sin caer en sobre-ingeniería.

## 2. Cuándo utilizarla

- Al revisar la estructura actual antes de modificarla.
- Al proponer cambios arquitectónicos.
- Al agregar nuevos módulos o capas.
- Al documentar la arquitectura en `docs/ARQUITECTURA.md`.
- Cuando hay dudas sobre dónde colocar nuevo código.

## 3. Qué debe revisar

### Separación frontend/backend
- [ ] ¿El frontend solo consume la API? (no accede directo a BD)
- [ ] ¿El backend no genera HTML? (separación limpia)
- [ ] ¿La comunicación es via HTTP/JSON?

### Capas del backend
- [ ] **routes/**: solo define URLs y métodos HTTP. No contiene lógica.
- [ ] **controllers/**: recibe petición, valida, llama a services, devuelve respuesta.
- [ ] **services/**: contiene la lógica de negocio. No sabe nada de HTTP.
- [ ] **models/**: representa datos y acceso a BD. No contiene reglas de negocio.
- [ ] **middlewares/**: funciones transversales (errores, autenticación, etc.)
- [ ] **config/**: configuración. No contiene lógica.

### Modelos de datos
- [ ] ¿Los modelos reflejan la realidad del negocio?
- [ ] ¿Hay separación entre modelo y lógica de negocio?
- [ ] ¿Los campos tienen tipos correctos?
- [ ] ¿Las relaciones están bien definidas?

### Configuración
- [ ] ¿Los valores sensibles vienen de variables de entorno?
- [ ] ¿Hay distinción entre entorno dev y producción?
- [ ] ¿El SECRET_KEY es seguro y no está en el código?

### Base de datos
- [ ] ¿El acceso a BD está encapsulado en los modelos/repositories?
- [ ] ¿Hay consultas SQL directas fuera de los modelos?
- [ ] ¿Se usan consultas parametrizadas para evitar SQL Injection?

### Dependencias entre módulos
- [ ] ¿Los módulos tienen dependencias claras y unidireccionales?
- [ ] ¿Hay importaciones circulares?
- [ ] ¿Las extensiones se inicializan correctamente para evitar circulares?

## 4. Reglas obligatorias

1. La arquitectura debe ser comprensible para un estudiante de quinto semestre.
2. Cada capa tiene una responsabilidad única. No mezclar.
3. Los controllers no contienen lógica de negocio.
4. Los services no saben nada de HTTP (no usan `request`, no devuelven `jsonify`).
5. Los models no contienen reglas de negocio complejas.
6. Nada sensible en el código fuente. Todo en variables de entorno.
7. No agregar capas innecesarias por seguir patrones abstractos.

## 5. Procedimiento

### Análisis de arquitectura actual
```
1. Mapear todas las capas existentes.
2. Verificar que cada archivo está en la capa correcta.
3. Identificar violaciones de separación de responsabilidades.
4. Identificar código en el lugar incorrecto.
```

### Propuesta de cambio
```
1. Documentar el problema detectado.
2. Proponer la solución mínima necesaria.
3. Identificar qué otros archivos se verán afectados.
4. Estimar el riesgo del cambio.
```

### Validación
```
1. Después del cambio, verificar que las capas siguen siendo correctas.
2. Verificar que no se rompieron dependencias.
3. Actualizar docs/ARQUITECTURA.md.
```

## 6. Checklist de revisión arquitectónica

- [ ] routes/ solo tienen URLs, métodos y limitadores
- [ ] controllers/ solo coordinan: reciben, validan, llaman, responden
- [ ] services/ solo tienen lógica de negocio
- [ ] models/ solo tienen representación de datos y acceso a BD
- [ ] config/ solo tiene configuración
- [ ] No hay lógica de negocio en routes/
- [ ] No hay código HTTP en services/
- [ ] No hay SQL fuera de models/
- [ ] Las extensiones se inicializan sin importaciones circulares
- [ ] docs/ARQUITECTURA.md está actualizado

## 7. Criterios de finalización

Un cambio arquitectónico está completo cuando:
- El código está en la capa correcta.
- La separación de responsabilidades se mantiene.
- No hay importaciones circulares.
- La documentación refleja la estructura real.

## 8. Errores que debe evitar

- Agregar capas que el equipo no puede mantener.
- Mover código sin entender sus dependencias.
- Crear abstracciones prematuras.
- Dejar lógica de negocio en los controladores.
- Mezclar acceso a datos con lógica de negocio.
- Documentar una arquitectura diferente a la implementada.

## 9. Documentación que debe actualizar

- `docs/ARQUITECTURA.md` — al hacer cualquier cambio estructural.
- `docs/CHANGELOG.md` — al hacer cambios significativos.
