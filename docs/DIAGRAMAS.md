# DIAGRAMAS.md — Diagramas de EncuentraU v2.0

Arquitectura, secuencia de una entrega y despliegue: `docs/ARQUITECTURA.md`. Aquí: entidad-relación, casos de uso por rol, estados y actividad del proceso de reclamación, y autenticación. (Los diagramas usan Mermaid: GitHub los dibuja automáticamente.)

## 1. Entidad-relación (esquema real de `backend/migrations/sql/01_tablas.sql`)

```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : "rol"
    USUARIOS ||--o{ TOKENS_USUARIO : "tiene"
    USUARIOS ||--o{ OBJETOS : "reporta"
    USUARIOS ||--o{ OBJETOS : "recibe en la oficina"
    USUARIOS ||--o{ SOLICITUDES : "reclama"
    USUARIOS ||--o{ SOLICITUDES : "revisa"
    USUARIOS ||--o{ ENTREGAS : "entrega"
    USUARIOS ||--o{ NOTIFICACIONES : "recibe"
    CATEGORIAS ||--o{ OBJETOS : "clasifica"
    UBICACIONES ||--o{ OBJETOS : "ubica"
    ESTADOS_OBJETO ||--o{ OBJETOS : "estado (tipo, codigo)"
    ESTADOS_OBJETO ||--o{ TRANSICIONES_OBJETO : "origen / destino"
    OBJETOS ||--o{ SOLICITUDES : "es reclamado"
    OBJETOS ||--o{ SOLICITUDES : "reporte de perdida vinculado"
    ESTADOS_SOLICITUD ||--o{ SOLICITUDES : "estado"
    SOLICITUDES ||--o| ENTREGAS : "(solicitud_id, objeto_id)"

    ROLES {
        string codigo PK
    }
    USUARIOS {
        int id PK
        string correo UK
        string password_hash
        string rol FK
        bool activo
        timestamptz correo_verificado_en
        bool marcado_revision
    }
    TOKENS_USUARIO {
        int id PK
        int usuario_id FK
        string proposito
        string token_hash UK
        timestamptz expira_en
        timestamptz usado_en
    }
    CATEGORIAS {
        int id PK
        string nombre UK
        bool activa
    }
    UBICACIONES {
        int id PK
        string nombre UK
        bool activa
    }
    ESTADOS_OBJETO {
        string tipo PK
        string codigo PK
        bool es_inicial
        bool es_final
    }
    TRANSICIONES_OBJETO {
        string tipo PK
        string estado_origen PK
        string estado_destino PK
        string actor
    }
    OBJETOS {
        int id PK
        string tipo
        string nombre "publico"
        int categoria_id FK
        int ubicacion_id FK
        date fecha_evento
        string descripcion "privado"
        string estado FK
        int usuario_id FK
        int recibido_por_id FK
        int version
    }
    ESTADOS_SOLICITUD {
        string codigo PK
        bool es_abierta
        bool cuenta_como_rechazo
    }
    SOLICITUDES {
        int id PK
        int objeto_id FK
        int solicitante_id FK
        int reporte_perdida_id FK
        string descripcion
        string estado FK
        timestamptz vence_en
        string codigo_hash
        int intentos_codigo
        int version
    }
    ENTREGAS {
        int id PK
        int objeto_id UK
        int solicitud_id UK
        int entregado_por_id FK
        bool carne_verificado
        string prueba_propiedad
    }
    NOTIFICACIONES {
        int id PK
        int usuario_id FK
        string titulo
        timestamptz leida_en
    }
    PARAMETROS {
        string clave PK
        int valor
        int minimo
        int maximo
    }
    AUDITORIA {
        bigint id PK
        string tabla
        bigint registro_id
        string operacion
        int usuario_id
        inet ip
        jsonb datos_anteriores
        jsonb datos_nuevos
        bigint transaccion_id
    }
```

`AUDITORIA` y `PARAMETROS` no tienen relaciones a propósito: la auditoría no debe depender de otras tablas, y los parámetros los leen los triggers por su clave.

## 2. Casos de uso por rol

```mermaid
flowchart LR
    E((Estudiante))
    C((Encargado))
    A((Administrador))
    T((Terminal del servidor))

    subgraph EncuentraU
        U1[Registrarse y verificar el correo]
        U2[Reportar objeto perdido / encontrado]
        U3[Buscar objetos en la oficina]
        U4[Reclamar describiendo el objeto]
        U5[Generar código de retiro]
        U6[Confirmar recepción en la oficina]
        U7[Comparar y pre-aprobar / rechazar]
        U8[Entrega presencial: carné + código + prueba]
        U9[Cerrar reporte]
        U10[Nombrar encargados / desactivar cuentas]
        U11[Gestionar catálogos y parámetros]
        U12[Revisar auditoría y estadísticas]
        U13[Crear administrador]
    end

    E --> U1 & U2 & U3 & U4 & U5
    C --> U6 & U7 & U8 & U9
    A --> U10 & U11 & U12
    T --> U13
```

## 3. Estados de un objeto encontrado (tabla `transiciones_objeto`)

```mermaid
stateDiagram-v2
    [*] --> pendiente_entrega : estudiante reporta
    pendiente_entrega --> en_oficina : encargado lo recibe
    pendiente_entrega --> cancelado : quien lo reportó cancela
    pendiente_entrega --> cerrado : encargado (nunca llegó)
    en_oficina --> reservado : reclamación pre-aprobada
    en_oficina --> cerrado : encargado (fin de custodia)
    reservado --> entregado : entrega con código + carné
    reservado --> en_oficina : vence, se rechaza o se cancela
    entregado --> [*]
    cerrado --> [*]
    cancelado --> [*]
```

Objeto perdido: `buscando` → `recuperado` (al entregarle un objeto con ese reporte vinculado) · `cancelado` · `cerrado`.

## 4. Actividad — de la reclamación a la entrega

```mermaid
flowchart TD
    A[Estudiante ve un objeto en la oficina<br/>solo datos públicos] --> B[Describe el objeto sin ver los detalles privados]
    B --> C{Trigger: ¿objeto en la oficina, no propio,<br/>sin otra abierta, menos del máximo,<br/>cuenta no en revisión?}
    C -- No --> X[Rechazado con el motivo]
    C -- Sí --> D[Reclamación pendiente<br/>avisos al estudiante y a los encargados]
    D --> E[Encargado compara lado a lado<br/>+ evidencia del reporte de pérdida previo]
    E --> F{¿Coincide?}
    F -- No --> G[Rechazada con motivo<br/>al 3er rechazo: cuenta en revisión]
    F -- Sí --> H[Pre-aprobada: objeto reservado 72 h]
    H --> I[Estudiante genera código de un solo uso]
    I --> J[En la oficina: carné + código + prueba]
    J --> K{sp_registrar_entrega}
    K -- código incorrecto --> L[Se descuenta un intento<br/>al 5º el código se invalida]
    L --> J
    K -- venció --> M[Reserva liberada: objeto vuelve a la oficina]
    K -- correcto --> N[Acta de entrega · objeto entregado ·<br/>otras reclamaciones descartadas ·<br/>reporte de pérdida recuperado]
    N --> O[Avisos: dueño 'si no fuiste tú, avisa'<br/>y quien lo encontró 'volvió a su dueño']
```

## 5. Autenticación con verificación de correo

```mermaid
sequenceDiagram
    participant N as Navegador
    participant F as Flask
    participant BD as PostgreSQL
    participant M as Correo

    N->>F: POST /api/auth/registro (correo @sanmateo.edu.co)
    F->>F: valida + Argon2id (siempre, exista o no la cuenta)
    F->>BD: INSERT usuario (estudiante, sin verificar) + hash del token
    F->>M: enlace verificar-correo.html?token=…
    F-->>N: 201 (misma respuesta exista o no la cuenta)
    N->>F: POST /api/auth/verificar-correo {token}
    F->>BD: busca por SHA-256(token), válido y sin usar → marca usado + verificado
    N->>F: POST /api/auth/login
    alt contraseña correcta y correo verificado
        F->>F: session.clear(); session['usuario_id'] = id
        F-->>N: 200 {usuario, csrf_token nuevo}
    else contraseña correcta, correo sin verificar
        F-->>N: 403 correo_no_verificado
    else credenciales inválidas
        F-->>N: 401 mensaje genérico
    end
```
