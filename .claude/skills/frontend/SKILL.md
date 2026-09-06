---
name: frontend
description: Guía para el desarrollo y revisión del frontend HTML/CSS/JS de EncuentraU.
---

# SKILL: Frontend

## 1. Propósito

Guiar el desarrollo, revisión y mejora del frontend de EncuentraU. El frontend consiste en páginas HTML + CSS + JavaScript vanilla que consumen la API REST del backend. Esta Skill garantiza que el frontend sea funcional, seguro y mantenible.

## 2. Cuándo utilizarla

- Al agregar o modificar páginas HTML.
- Al conectar el frontend al backend (reemplazar datos simulados).
- Al revisar validaciones del lado del cliente.
- Al revisar seguridad del frontend.
- Al modificar estilos o comportamiento.

## 3. Qué debe revisar

### Interfaz
- [ ] ¿Las páginas tienen estructura HTML semántica?
- [ ] ¿Los formularios tienen atributos correctos (name, id, type)?
- [ ] ¿La interfaz es consistente entre páginas?
- [ ] ¿Hay mensajes de error y éxito visibles al usuario?

### Formularios
- [ ] ¿Los formularios validan en el cliente antes de enviar? (experiencia de usuario)
- [ ] ¿La validación del cliente no reemplaza la del servidor?
- [ ] ¿Los campos obligatorios tienen required?
- [ ] ¿Los campos tienen longitudes máximas (maxlength)?

### Consumo de API
- [ ] ¿Las peticiones incluyen el CSRF token?
- [ ] ¿Se maneja correctamente el error cuando el token CSRF expira?
- [ ] ¿Las peticiones usan credentials: 'include' para enviar la cookie?
- [ ] ¿Los errores del servidor se muestran al usuario de forma útil?
- [ ] ¿No se exponen detalles técnicos en mensajes de error?

### Validaciones del cliente
- [ ] ¿Solo son experiencia de usuario, no seguridad?
- [ ] ¿Complementan (no reemplazan) las validaciones del servidor?
- [ ] ¿Los mensajes de error son claros para el usuario?

### Manejo de errores
- [ ] ¿Qué pasa cuando el servidor no responde?
- [ ] ¿Qué pasa cuando la sesión expira?
- [ ] ¿El usuario recibe feedback claro en cada caso?

### Accesibilidad
- [ ] ¿Las imágenes tienen atributo alt?
- [ ] ¿Los formularios tienen labels asociados a inputs?
- [ ] ¿El contraste de colores es adecuado?

### Seguridad frontend
- [ ] ¿No se guarda información sensible en localStorage/sessionStorage?
- [ ] ¿No se guarda el rol del usuario en el cliente (el backend debe verificarlo)?
- [ ] ¿No se muestran funcionalidades de admin solo ocultando HTML?
- [ ] ¿El CSRF token se obtiene y envía correctamente?

### Datos simulados
- [ ] ¿datos-temporales.js está claramente marcado como temporal?
- [ ] ¿Qué páginas usan datos simulados vs API real?
- [ ] ¿El plan de reemplazo de simulados está documentado?

## 4. Reglas obligatorias

1. El frontend NUNCA es la autoridad de permisos. El backend siempre valida.
2. Nunca guardar datos sensibles en localStorage o sessionStorage.
3. El rol del usuario NO debe usarse en el frontend para tomar decisiones de seguridad.
4. El CSRF token debe enviarse en todas las peticiones que modifican datos.
5. Los datos simulados (datos-temporales.js) deben estar claramente marcados.
6. No rediseñar la interfaz visual durante la fase de migración sin aprobación.

## 5. Procedimiento de conexión de página al backend

```
1. Identificar qué datos necesita la página.
2. Identificar los endpoints de API que los proveen.
3. Reemplazar los datos simulados por fetch() a la API.
4. Manejar errores de red y de servidor.
5. Manejar la sesión expirada (redirigir a login).
6. Probar que funciona con el backend real.
7. Actualizar docs/FRONTEND.md.
```

## 6. Estructura de una petición al backend

```javascript
// 1. Obtener CSRF token
const csrf = await fetch('/api/auth/csrf-token').then(r => r.json());

// 2. Hacer la petición
const respuesta = await fetch('/api/auth/login', {
  method: 'POST',
  credentials: 'include',          // enviar cookie de sesión
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf.csrf_token  // protección CSRF
  },
  body: JSON.stringify({ correo, contrasena })
});

// 3. Manejar la respuesta
const datos = await respuesta.json();
if (!respuesta.ok) {
  // mostrar error al usuario (sin exponer detalles técnicos)
}
```

## 7. Checklist de una página conectada correctamente

- [ ] Obtiene CSRF token antes de enviar formularios
- [ ] Envía credentials: 'include' en fetch
- [ ] Envía X-CSRFToken en headers de peticiones que modifican datos
- [ ] Maneja error 401 (sesión expirada → redirigir a login)
- [ ] Maneja error 403 (no autorizado → mensaje claro)
- [ ] Maneja errores de red (servidor no responde)
- [ ] No guarda datos sensibles en localStorage
- [ ] No usa datos del cliente para decisiones de seguridad
- [ ] Reemplazó completamente los datos simulados

## 8. Criterios de finalización

Una página está completa cuando:
- Consume la API real (no datos simulados).
- Maneja correctamente los estados de error.
- No expone información sensible al cliente.
- Fue probada con el backend en ejecución.

## 9. Errores que debe evitar

- Usar el rol del usuario guardado en el cliente para mostrar/ocultar funcionalidades críticas.
- Olvidar enviar el CSRF token.
- Dejar datos-temporales.js sin reemplazar en producción.
- Asumir que el frontend es suficiente para proteger rutas.
- Rediseñar la UI sin necesidad durante la migración.

## 10. Documentación que debe actualizar

- `docs/FRONTEND.md` — al conectar páginas o cambiar comportamiento.
- `docs/CHANGELOG.md` — al hacer cambios significativos.
