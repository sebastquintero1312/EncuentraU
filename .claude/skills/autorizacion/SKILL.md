---
name: autorizacion
description: Guía para implementar y revisar el sistema de autorización de EncuentraU: roles, permisos, ownership y protección contra escalamiento de privilegios.
---

# SKILL: Autorización

## 1. Propósito

Guiar la implementación y revisión del sistema de autorización de EncументraU. La autorización determina QUÉ puede hacer cada usuario autenticado. Un error en autorización puede permitir que usuarios accedan o modifiquen datos de otros (IDOR), o que usuarios normales realicen acciones de administrador.

## 2. Cuándo utilizarla

- Al agregar cualquier endpoint que requiera permisos.
- Al revisar si los endpoints verifican correctamente el rol.
- Al implementar verificación de ownership (que el objeto pertenece al usuario).
- Al agregar funcionalidades de administrador.
- Al revisar posibles vulnerabilidades IDOR/BOLA.

## 3. Roles del sistema

| Rol | Descripción | Permisos |
|-----|-------------|---------|
| ciudadano | Usuario registrado | CRUD de sus propios reportes, ver reportes de otros, solicitar recuperación de objetos |
| administrador | Administrador del sistema | Todo lo anterior + gestión de usuarios, moderación de reportes, gestión de solicitudes |

## 4. Principios fundamentales

### Deny by Default
Lo que no está explícitamente permitido está prohibido.
Un endpoint sin verificación de autorización es un endpoint ABIERTO.

### Least Privilege
Cada usuario accede solo a lo que necesita.
Los ciudadanos no ven datos de otros usuarios que no sean públicos.

### El frontend nunca es la autoridad
Ocultar un botón en el HTML no es autorización.
El backend SIEMPRE verifica permisos, independientemente de lo que el frontend muestre.

## 5. Qué debe revisar

### Autenticación previa
- [ ] ¿El endpoint verifica que el usuario esté autenticado?
- [ ] ¿Qué pasa si session['usuario_id'] no existe?
- [ ] ¿Se retorna 401 si no hay sesión?

### Verificación de rol
- [ ] ¿Los endpoints de admin verifican rol == 'administrador'?
- [ ] ¿El rol viene de la base de datos, no del cliente?
- [ ] ¿Se retorna 403 si el rol no es suficiente?

### Verificación de ownership (IDOR)
- [ ] Al modificar un reporte: ¿se verifica que pertenece al usuario?
- [ ] Al eliminar un reporte: ¿se verifica que pertenece al usuario?
- [ ] Al ver solicitudes: ¿se filtra por el usuario actual?
- [ ] Un usuario nunca puede acceder a datos de otro por su ID.

### Mass Assignment
- [ ] ¿Se filtran los campos que el usuario puede enviar?
- [ ] ¿El usuario puede enviar 'rol': 'administrador' y que se guarde?
- [ ] ¿Los campos permitidos están explícitamente listados?

### Escalamiento de privilegios
- [ ] ¿Puede un ciudadano acceder a rutas de admin?
- [ ] ¿Puede un ciudadano modificar el rol de su propia cuenta?
- [ ] ¿Las rutas de admin requieren verificación de rol en el backend?

## 6. Reglas obligatorias

1. Todo endpoint que modifica datos verifica autenticación.
2. Todo endpoint de administrador verifica rol en el backend.
3. Al acceder a un recurso por ID, verificar que pertenece al usuario o que el usuario es admin.
4. El rol nunca viene del cliente (cookie, body, header).
5. Los campos permitidos en un update están explícitamente listados (whitelist).
6. Los errores de autorización retornan 403 (no 404 para recursos existentes).

## 7. Patrón de middleware de autorización

```python
# Decorador de autenticacion requerida
def login_requerido(f):
    def decorador(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        usuario = buscar_por_id(usuario_id)
        if not usuario:
            session.clear()
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        return f(usuario, *args, **kwargs)
    return decorador

# Decorador de admin requerido
def admin_requerido(f):
    def decorador(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'mensaje': 'Autenticación requerida'}), 401
        usuario = buscar_por_id(usuario_id)
        if not usuario or usuario.get('rol') != 'administrador':
            return jsonify({'mensaje': 'Acceso no autorizado'}), 403
        return f(usuario, *args, **kwargs)
    return decorador
```

## 8. Verificación de ownership

```python
# Ejemplo: modificar un reporte
def actualizar_reporte(usuario_actual, reporte_id):
    reporte = obtener_reporte(reporte_id)
    if not reporte:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404
    # VERIFICACIÓN DE OWNERSHIP
    if reporte.usuario_id != usuario_actual['id'] and usuario_actual['rol'] != 'administrador':
        return jsonify({'mensaje': 'No autorizado'}), 403
    # Proceder con la actualización...
```

## 9. Checklist de autorización completa

- [ ] Endpoints de lectura pública no requieren auth
- [ ] Endpoints que modifican datos requieren login
- [ ] Endpoints de admin verifican rol en el backend
- [ ] Modificar/eliminar recurso verifica ownership
- [ ] Ver recursos de otros usuarios está controlado
- [ ] No hay campos de rol o permisos aceptados del cliente
- [ ] Los errores retornan 401 (no autenticado) o 403 (no autorizado)
- [ ] No hay rutas de admin accesibles sin verificación de rol

## 10. Criterios de finalización

La autorización está correctamente implementada cuando:
- Ningún endpoint de admin es accesible sin rol de admin.
- Ningún usuario puede modificar recursos de otro usuario (sin ser admin).
- Los tests de autorización verifican todos los casos borde.
- No hay endpoints sin verificación de autenticación cuando la requieren.

## 11. Errores que debe evitar

- Asumir que el frontend ocultó una funcionalidad entonces no hace falta verificarla en el backend.
- Confiar en el campo 'rol' que viene en el body de la petición.
- Olvidar verificar ownership al acceder a recursos por ID.
- Retornar 404 cuando el recurso existe pero el usuario no tiene permiso (en vez de 403).
- Permitir que un usuario normal edite su propio rol.

## 12. Documentación que debe actualizar

- `docs/AUTHORIZATION.md` — al cambiar roles o permisos.
- `docs/API.md` — al documentar qué endpoints requieren qué permisos.
- `docs/SECURITY.md` — al cambiar políticas de autorización.
