---
name: pruebas
description: Guía para escribir, ejecutar y documentar pruebas en EncuentraU usando pytest.
---

# SKILL: Pruebas

## 1. Propósito

Guiar la escritura, ejecución y documentación de pruebas en EncuentraU. Las pruebas son la única forma de afirmar con certeza que algo funciona. Sin pruebas ejecutadas con evidencia, el estado máximo es IMPLEMENTADO, nunca VERIFICADO.

## 2. Cuándo utilizarla

- Al escribir pruebas para una nueva funcionalidad.
- Al ejecutar el suite de pruebas.
- Al reportar resultados de pruebas.
- Al diseñar casos de prueba para seguridad.
- Antes de declarar cualquier funcionalidad como VERIFICADA.

## 3. Tecnología

- **Framework**: pytest
- **Testing de API**: Flask test client
- **Cobertura**: pytest-cov (opcional)

## 4. Tipos de pruebas

### Unit Tests
Prueban una función o módulo en aislamiento.

```python
# tests/unit/test_auth_service.py
def test_validar_contrasena_debil():
    errores = validar_contrasena("12345678")
    assert len(errores) > 0

def test_validar_contrasena_fuerte():
    errores = validar_contrasena("MiClave$Segura2024")
    assert errores == []

def test_correo_valido():
    assert correo_valido("usuario@universidad.edu") == True

def test_correo_invalido():
    assert correo_valido("no-es-correo") == False
```

### Integration Tests
Prueban flujos completos a través de múltiples capas.

```python
# tests/integration/test_auth.py
def test_registro_exitoso(client):
    respuesta = client.post('/api/auth/registro', json={
        'primer_nombre': 'Test',
        'primer_apellido': 'Usuario',
        'correo': 'test@test.com',
        'contrasena': 'Prueba$Segura2024',
        'confirmar_contrasena': 'Prueba$Segura2024'
    })
    assert respuesta.status_code == 201

def test_login_exitoso(client, usuario_de_prueba):
    respuesta = client.post('/api/auth/login', json={
        'correo': 'test@test.com',
        'contrasena': 'Prueba$Segura2024'
    })
    assert respuesta.status_code == 200
```

### API Tests
Verifican el contrato de la API (códigos, formato de respuesta).

```python
def test_login_credenciales_incorrectas(client):
    respuesta = client.post('/api/auth/login', json={
        'correo': 'noexiste@test.com',
        'contrasena': 'Cualquiera123!'
    })
    assert respuesta.status_code == 401
    datos = respuesta.get_json()
    assert 'mensaje' in datos
    # Verificar que el mensaje no revela si el correo existe
    assert 'correo' not in datos['mensaje'].lower()
```

### Authentication Tests
Verifican que la autenticación funciona y falla correctamente.

```python
def test_endpoint_protegido_sin_sesion(client):
    respuesta = client.get('/api/mis-reportes')
    assert respuesta.status_code == 401

def test_endpoint_admin_con_estudiante(client, estudiante):
    respuesta = client.get('/api/admin/usuarios')
    assert respuesta.status_code == 403
```

### Authorization Tests
Verifican que la autorización protege correctamente los recursos.

```python
def test_no_puede_editar_reporte_ajeno(client, estudiante_a, reporte_estudiante_b):
    respuesta = client.put(f'/api/objetos/{reporte_estudiante_b.id}', json={...})
    assert respuesta.status_code == 403

def test_si_puede_editar_reporte_propio(client, estudiante_a, reporte_estudiante_a):
    respuesta = client.put(f'/api/objetos/{reporte_estudiante_a.id}', json={...})
    assert respuesta.status_code == 200
```

### Security Tests
Verifican resistencia a ataques conocidos.

```python
def test_rate_limit_login(client):
    for _ in range(11):
        client.post('/api/auth/login', json={...})
    respuesta = client.post('/api/auth/login', json={...})
    assert respuesta.status_code == 429

def test_csrf_requerido(client):
    # Petición sin token CSRF
    respuesta = client.post('/api/auth/login',
                            json={...},
                            headers={})  # sin X-CSRFToken
    assert respuesta.status_code == 400
```

## 5. Estructura de tests

```
tests/
├── conftest.py          # fixtures compartidas (app, client, usuarios de prueba)
├── unit/
│   ├── test_auth_service.py
│   ├── test_validaciones.py
│   └── ...
├── integration/
│   ├── test_auth.py
│   ├── test_objetos.py
│   └── ...
└── security/
    ├── test_autorizacion.py
    ├── test_rate_limiting.py
    └── ...
```

## 6. Reglas obligatorias

1. Nunca marcar una prueba como exitosa sin haberla ejecutado.
2. Los tests deben poder ejecutarse con: `pytest tests/`
3. Los tests usan una base de datos o almacenamiento de prueba separado.
4. Los tests deben limpiar su estado después de ejecutarse.
5. Un test que no se ejecutó no cuenta como evidencia.
6. Los resultados de pytest deben guardarse como evidencia antes de declarar VERIFICADO.

## 7. Checklist de pruebas por funcionalidad

### Autenticación
- [ ] Registro exitoso con datos válidos
- [ ] Registro falla con datos inválidos (cada campo)
- [ ] Registro falla si el correo ya existe
- [ ] Login exitoso
- [ ] Login falla con contraseña incorrecta
- [ ] Login falla con correo inexistente
- [ ] Logout limpia la sesión
- [ ] Recuperación envía token (verificar en log)
- [ ] Restablecimiento exitoso con token válido
- [ ] Restablecimiento falla con token expirado
- [ ] Restablecimiento falla con token ya usado

### Autorización
- [ ] Endpoint protegido rechaza sin sesión (401)
- [ ] Endpoint de admin rechaza estudiante y encargado (403)
- [ ] Modificar reporte ajeno falla (403)
- [ ] Modificar reporte propio funciona (200)

### Rate Limiting
- [ ] Login: falla después de 10 intentos por minuto
- [ ] Registro: falla después de 5 intentos por minuto

## 8. Criterios de finalización

Las pruebas están completas cuando:
- Existe un test por cada funcionalidad implementada.
- Los tests se ejecutan con `pytest` sin errores.
- Los resultados están documentados.
- Casos de error y casos felices están cubiertos.

## 9. Errores que debe evitar

- Escribir tests que siempre pasan (sin assertions).
- Marcar como VERIFICADO sin ejecutar los tests.
- Tests que dependen del orden de ejecución.
- Tests que no limpian su estado.
- Omitir tests de seguridad y autorización.

## 10. Documentación que debe actualizar

- `docs/TESTING.md` — al agregar tests o cambiar la estrategia de pruebas.
- `docs/CHANGELOG.md` — al agregar cobertura de tests significativa.
