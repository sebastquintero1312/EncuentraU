# DIAGRAMAS.md — Diagramas complementarios de EncuentraU v1.0

Los diagramas de arquitectura de componentes, secuencia (creación de un reporte) y despliegue ya están en `docs/ARQUITECTURA.md`. Este documento agrega los que faltaban: entidad-relación, casos de uso, clases y actividad del proceso de reclamación.

## 1. Entidad-relación

```mermaid
erDiagram
    USUARIO ||--o{ OBJETO : "reporta"
    USUARIO ||--o{ SOLICITUD : "solicita"
    USUARIO ||--o{ TOKEN_RECUPERACION : "tiene"
    OBJETO ||--o{ SOLICITUD : "recibe"

    USUARIO {
        int id PK
        string primer_nombre
        string primer_apellido
        string correo UK
        string password_hash
        string rol
        bool activo
    }
    TOKEN_RECUPERACION {
        int id PK
        string token UK
        int usuario_id FK
        datetime expira_en
        bool usado
    }
    OBJETO {
        int id PK
        string tipo
        string nombre
        string categoria
        string descripcion
        string ubicacion
        date fecha_evento
        string estado
        int usuario_id FK
    }
    SOLICITUD {
        int id PK
        int objeto_id FK
        int solicitante_id FK
        string contacto
        string mensaje
        string estado
        string respuesta_admin
    }
```

## 2. Casos de uso

```mermaid
flowchart LR
    Ciudadano((Ciudadano))
    Admin((Administrador))

    subgraph EncuentraU
        UC1[Registrarse / Iniciar sesión]
        UC2[Reportar objeto perdido]
        UC3[Reportar objeto encontrado]
        UC4[Buscar objetos]
        UC5[Ver posibles coincidencias]
        UC6[Solicitar recuperación]
        UC7[Ver solicitudes recibidas]
        UC8[Gestionar reportes]
        UC9[Gestionar solicitudes]
        UC10[Gestionar usuarios]
    end

    Ciudadano --> UC1
    Ciudadano --> UC2
    Ciudadano --> UC3
    Ciudadano --> UC4
    Ciudadano --> UC5
    Ciudadano --> UC6
    Ciudadano --> UC7

    Admin --> UC1
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    UC9 -.incluye.-> UC7
```

## 3. Clases (modelos del backend)

```mermaid
classDiagram
    class Usuario {
        +int id
        +string correo
        +string password_hash
        +string rol
        +bool activo
    }
    class TokenRecuperacion {
        +int id
        +string token
        +datetime expira_en
        +bool usado
    }
    class Objeto {
        +int id
        +string tipo
        +string nombre
        +string categoria
        +string estado
        +puede_transicionar_a(estado) bool
        +publico() dict
    }
    class Solicitud {
        +int id
        +string contacto
        +string mensaje
        +string estado
        +publica() dict
    }

    Usuario "1" --> "*" Objeto : reporta
    Usuario "1" --> "*" Solicitud : solicita
    Usuario "1" --> "*" TokenRecuperacion : tiene
    Objeto "1" --> "*" Solicitud : recibe
```

## 4. Actividad — proceso de reclamación (de solicitud a resolución)

```mermaid
flowchart TD
    A[Ciudadano B ve un objeto reportado] --> B{"¿Es su propio reporte?"}
    B -- Sí --> C[Rechazado: no puede reclamar lo propio]
    B -- No --> D{"¿Ya tiene una solicitud abierta sobre este objeto?"}
    D -- Sí --> E[Rechazado: solicitud duplicada]
    D -- No --> F[Crea solicitud con mensaje de verificación]
    F --> G[Objeto pasa a 'en_proceso']
    G --> H[Dueño del objeto ve la solicitud y su información privada]
    H --> I[Administrador revisa la solicitud]
    I --> J{"¿Aprueba?"}
    J -- Sí --> K[Objeto pasa a 'resuelto']
    K --> L[Otras solicitudes abiertas sobre el mismo objeto se rechazan automáticamente]
    J -- No --> M[Solicitud rechazada]
    M --> N{"¿Quedan otras solicitudes abiertas?"}
    N -- No --> O[Objeto vuelve a 'activo']
    N -- Sí --> P[Objeto permanece 'en_proceso']
```

## 5. Autenticación (secuencia)

```mermaid
sequenceDiagram
    participant N as Navegador
    participant F as Flask (auth_controller)
    participant S as auth_service (Argon2id)
    participant BD as Base de datos

    N->>F: GET /api/auth/csrf-token
    F-->>N: csrf_token

    N->>F: POST /api/auth/login (correo, contraseña, X-CSRFToken)
    F->>BD: buscar_por_correo(correo)
    BD-->>F: Usuario o None
    F->>S: verificar_password(contraseña, hash)
    S-->>F: True/False
    alt credenciales válidas y cuenta activa
        F->>F: session.clear(); session['usuario_id'] = id
        F-->>N: 200 {usuario, csrf_token nuevo}
    else inválidas
        F-->>N: 401 {mensaje genérico}
    end
```
