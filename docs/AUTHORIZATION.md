# AUTHORIZATION.md — Roles, permisos y protección contra reclamaciones falsas (v2.0)

## 1. Principios

- **Deny by default**: cada ruta declara exactamente qué rol puede usarla (`@estudiante_requerido`, `@encargado_requerido`, `@admin_requerido`, `@login_requerido` en `backend/app/middlewares/autorizacion.py`). Lo que no está permitido devuelve 401 (sin sesión) o 403 (otro rol).
- **El rol se relee de la base de datos en cada petición**: nunca se toma del cliente. Si un administrador cambia el rol de alguien, aplica en su siguiente petición (`test_el_rol_se_relee_de_la_base_en_cada_peticion`).
- **El frontend no es la autoridad**: `js/layout.js` solo muestra el menú del rol y redirige por comodidad. Aunque alguien modifique el JavaScript, el servidor responde 401/403.
- **Defensa en profundidad**: además de Flask, la base de datos vuelve a exigir el rol en los procedimientos (`fn_exigir_encargado`) y en el trigger de nuevas reclamaciones (solo estudiantes).
- **Separación de funciones**: quien opera (encargado) no controla, y quien controla (administrador) no opera.

## 2. Matriz de permisos

| Acción | Estudiante | Encargado | Administrador |
|---|:-:|:-:|:-:|
| Reportar objeto perdido / encontrado | ✅ | ❌ | ❌ |
| Ver y editar **sus propios** reportes (mientras estén en estado inicial) | ✅ | ❌ | ❌ |
| Buscar objetos en la oficina (solo datos públicos) | ✅ | ❌ | ❌ |
| Reclamar un objeto y generar su código de retiro | ✅ | ❌ | ❌ |
| Ver **todos** los reportes con sus detalles privados | ❌ | ✅ | ✅ (solo lectura) |
| Confirmar la recepción de un objeto en la oficina | ❌ | ✅ | ❌ |
| Pre-aprobar o rechazar reclamaciones | ❌ | ✅ | ❌ |
| Registrar la entrega presencial y cerrar reportes | ❌ | ✅ | ❌ |
| Ver estadísticas de la oficina | ❌ | ✅ | ✅ |
| Activar/desactivar cuentas, nombrar encargados, levantar revisiones | ❌ | ❌ | ✅ |
| Gestionar categorías, ubicaciones y parámetros | ❌ | ❌ | ✅ |
| Ver la auditoría y exportar datos | ❌ | ❌ | ✅ |
| Crear administradores | ❌ | ❌ | ❌ (solo `flask crear-admin` en la terminal del servidor) |

Verificado ruta por ruta en `backend/tests/integration/test_roles.py` (las rutas de cada rol devuelven 403 para los otros dos y 401 sin sesión).

Reglas del administrador (`usuarios_admin_service.py`): desde la web solo asigna `estudiante` o `encargado`; no se modifica a sí mismo ni a otro administrador; solo una cuenta con el correo verificado puede ser encargado.

## 3. Ownership (IDOR)

- Un estudiante solo edita, cancela o consulta coincidencias de **sus** reportes (`_reporte_propio` en `objetos_controller.py`), y solo cancela o genera código de **sus** reclamaciones. Cambiar el id en la URL devuelve 403 (`test_idor_*` en `tests/security/test_ofensivas.py`).
- Los reportes de pérdida de otra persona y los objetos que aún no están en la oficina no son visibles (403).
- Una notificación ajena responde 404.
- Whitelist explícita contra *mass assignment*: campos como `estado`, `usuario_id`, `version`, `codigo_hash` o `rol` enviados por el cliente se ignoran (`test_mass_assignment_*`, `test_whitelist_al_actualizar_usuario`). Además, el usuario de base de datos de la app ni siquiera tiene permiso para cambiar esas columnas (ver `docs/DATABASE.md` §10).

## 4. Cómo se evita que alguien reclame algo ajeno

Problema: "veo un objeto perdido en la lista, digo que es mío y me lo llevo". Medidas, en capas:

1. **Verificación a ciegas**: los objetos encontrados tienen una parte pública (nombre genérico, categoría, lugar, fecha) y una privada (marca, color, señas, contenido) que nunca se publica, ni en la búsqueda, ni en el detalle, ni en la propia reclamación del estudiante (`test_busqueda_no_muestra_la_descripcion_privada`, `test_el_reclamante_nunca_ve_la_descripcion_privada`). La búsqueda tampoco filtra por la descripción privada, para que nadie la adivine probando palabras (`test_busqueda_no_filtra_por_la_descripcion_privada`). Quien reclama describe el objeto sin haber visto esos detalles y el encargado compara las dos columnas.
2. **Solo se publica lo que está en la oficina**: un objeto encontrado aparece en la búsqueda solo cuando un encargado confirma que lo recibió. Los reportes de pérdida no son públicos.
3. **Evidencia que no se puede falsificar**: si el estudiante reportó la pérdida *antes* de que apareciera el objeto, el encargado lo ve marcado. La fecha la pone el sistema (`created_at`), no el usuario.
4. **Aprobar no es entregar**: la pre-aprobación abre una ventana de 72 h. El estudiante genera desde su cuenta un **código de un solo uso** de 6 dígitos (en la base de datos solo queda su HMAC-SHA256 con la `SECRET_KEY`) y debe presentarse con su **carné** y una **prueba de propiedad** (desbloquearlo, factura…). Con 5 intentos fallidos el código se invalida; generar uno nuevo anula el anterior.
5. **Límites contra el abuso**: una reclamación abierta por objeto; máximo 3 abiertas por estudiante; con 3 reclamaciones rechazadas la cuenta queda en revisión y no puede reclamar hasta que un administrador la revise. Lo aplica la base de datos (trigger), no solo Python.
6. **Identidad verificada**: solo cuentas `@sanmateo.edu.co` con el correo confirmado (ver `docs/AUTHENTICATION.md`). Cada reclamación queda asociada a una persona identificable.
7. **Trazabilidad**: todo queda en la auditoría inmutable; el administrador ve cuántas reclamaciones aprueba, rechaza y entrega cada encargado (`v_desempeno_encargados`) para detectar complicidad.
8. **Avisos**: al entregar, el dueño recibe "si no fuiste tú, avisa" y quien lo encontró recibe "volvió a su dueño".
9. **Disuasión**: la reclamación exige aceptar la declaración "reclamar un objeto ajeno puede constituir una falta disciplinaria".

**Limitación honesta**: si el impostor conoce el objeto (por ejemplo, el celular de un compañero), puede describirlo bien. Por eso la última barrera es la prueba presencial. Ningún sistema elimina el fraude al 100%: el objetivo es que sea difícil, quede registrado y tenga consecuencias.
