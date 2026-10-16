---
name: seguridad-ofensiva-defensiva
description: Guía para ejecutar pruebas de seguridad controladas sobre el propio proyecto EncuentraU. SOLO sobre localhost o entornos de prueba autorizados.
---

# SKILL: Seguridad Ofensiva y Defensiva

## 1. Propósito

Permitir el diseño y ejecución de pruebas de seguridad controladas sobre el propio proyecto EncuentraU. El objetivo es encontrar vulnerabilidades antes de que lo hagan los atacantes.

## ADVERTENCIA CRÍTICA

**ESTA SKILL ES EXCLUSIVAMENTE PARA PRUEBAS SOBRE EL PROPIO PROYECTO.**

Está TERMINANTEMENTE PROHIBIDO:
- Ejecutar cualquier prueba contra sistemas que no sean localhost o entornos de prueba propios.
- Usar estas técnicas contra sistemas de terceros.
- Realizar cualquier actividad que pueda interpretarse como un ataque.

Todo debe ejecutarse ÚNICAMENTE sobre:
- `http://localhost`
- `http://127.0.0.1`
- Entornos de prueba explícitamente autorizados

## 2. Cuándo utilizarla

- Durante la auditoría de seguridad de v0.25.
- Antes de declarar v1.0 como lista para producción.
- Después de implementar medidas de seguridad (para verificar que funcionan).
- Durante la revisión final antes del despliegue.

## 3. Pruebas de SQL Injection

### Descripción
Intentar insertar SQL malicioso en campos de entrada para verificar que el backend lo rechaza.

### Payloads de prueba
```
' OR '1'='1
'; DROP TABLE usuarios; --
' UNION SELECT * FROM usuarios --
admin'--
```

### Cómo verificar la protección
1. Ejecutar el backend en modo desarrollo.
2. Enviar peticiones con payloads maliciosos a los endpoints de login y registro.
3. Verificar que el backend retorna 400/401 y NO ejecuta SQL malicioso.
4. SQLAlchemy con ORM previene SQL Injection automáticamente.

### Resultado esperado
- Status 400 o 401 con mensaje de error seguro.
- NO ejecución de SQL malicioso.
- NO stack trace en la respuesta.

## 4. Pruebas de XSS

### Descripción
Intentar insertar scripts JavaScript en campos de texto.

### Payloads de prueba
```
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
javascript:alert('XSS')
"><script>alert('XSS')</script>
```

### Cómo verificar
1. Enviar payloads en campos de nombre, descripción de objetos, etc.
2. Verificar que el backend almacena el texto como texto (escapado).
3. Verificar que el frontend no ejecuta el script al mostrarlo.

### Resultado esperado
- El texto se guarda escapado o como texto plano.
- NO se ejecuta ningún script al mostrar los datos.

## 5. Pruebas de IDOR (Insecure Direct Object Reference)

### Descripción
Intentar acceder a recursos de otro usuario cambiando el ID en la URL.

### Cómo verificar
```
# Como usuario A (ID 1), intentar ver/modificar objeto del usuario B (ID 2)
GET /api/objetos/reporte-de-usuario-B
PUT /api/objetos/reporte-de-usuario-B {...}
```

### Resultado esperado
- Status 403 (o 404 si se oculta la existencia).
- NO acceso al recurso ajeno.

## 6. Pruebas de Brute Force controlado

### Descripción
Enviar múltiples peticiones de login para verificar que el rate limiting funciona.

### Script de prueba (solo localhost)
```python
import requests

for i in range(15):
    respuesta = requests.post('http://localhost:5000/api/auth/login', json={
        'correo': 'test@test.com',
        'contrasena': f'intento{i}'
    })
    print(f'Intento {i+1}: {respuesta.status_code}')
    if respuesta.status_code == 429:
        print('Rate limit activado correctamente')
        break
```

### Resultado esperado
- Después de 10 intentos: status 429.
- Los intentos posteriores también retornan 429.

## 7. Pruebas de manipulación de roles

### Descripción
Intentar escalar privilegios enviando rol='administrador' en el body.

### Payloads de prueba
```json
// En registro:
{
  "primer_nombre": "Test",
  "correo": "test@test.com",
  "contrasena": "Clave$123456",
  "confirmar_contrasena": "Clave$123456",
  "rol": "administrador"
}
```

### Resultado esperado
- El rol se ignora y el usuario se registra como 'estudiante'.
- Status 201 pero con rol='estudiante' en la respuesta.

## 8. Pruebas de tokens

### Descripción
Intentar usar tokens de recuperación expirados, ya usados, o modificados.

### Casos de prueba
1. Token expirado (esperar 31 minutos o modificar el tiempo de expiración en pruebas).
2. Token ya usado (usar el mismo token dos veces).
3. Token inexistente (enviar cualquier string como token).
4. Token de otro usuario.

### Resultado esperado
- Todos los casos: status 400 con mensaje genérico.
- NO se permite restablecer la contraseña.

## 9. Pruebas de CSRF

### Descripción
Intentar hacer peticiones que modifiquen datos sin el token CSRF.

### Cómo verificar
```python
# Sin X-CSRFToken header
respuesta = requests.post('http://localhost:5000/api/auth/login',
    json={'correo': 'test@test.com', 'contrasena': 'Clave$123456'})
# Debe retornar 400
```

### Resultado esperado
- Status 400 sin el token CSRF.
- La operación NO se realiza.

## 10. Pruebas de Path Traversal

### Descripción
Si hay upload de archivos, intentar subir con nombres maliciosos.

### Payloads de prueba
```
../../../etc/passwd
../../config/.env
/etc/shadow
```

### Resultado esperado
- Los nombres se rechazan o se sanean.
- NO se accede a archivos fuera del directorio permitido.

## 11. Pruebas de payloads grandes

### Descripción
Enviar body extremadamente grande para verificar que hay límite.

### Cómo verificar
```python
payload_grande = 'A' * 10_000_000  # 10 MB
respuesta = requests.post('http://localhost:5000/api/auth/login',
    data=payload_grande)
# Debe retornar 413 o rechazar
```

### Resultado esperado
- Status 413 o 400.
- El servidor no consume memoria excesiva.

## 12. Checklist de pruebas de seguridad

- [ ] SQL Injection: probado, sistema protegido
- [ ] XSS: probado, texto escapado correctamente
- [ ] IDOR: probado, ownership verificado
- [ ] Brute force: probado, rate limiting activo
- [ ] CSRF: probado, token requerido
- [ ] Escalamiento de roles: probado, rol ignorado del cliente
- [ ] Tokens expirados: probado, rechazados correctamente
- [ ] Tokens usados: probado, rechazados correctamente
- [ ] Payloads grandes: probado, limitados

## 13. Criterios de finalización

Las pruebas de seguridad están completas cuando:
- Todos los items del checklist tienen resultado.
- Los resultados están documentados con evidencia (outputs reales).
- Las vulnerabilidades encontradas están corregidas y re-probadas.

## 14. Documentación que debe actualizar

- `docs/SECURITY.md` — con resultados de las pruebas.
- `docs/MATRIZ_SEGURIDAD.md` — con estado actualizado de cada control.
- `docs/TESTING.md` — con las pruebas de seguridad ejecutadas.
