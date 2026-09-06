---
name: despliegue
description: Guía para preparar EncuentraU para despliegue en producción. NO ejecutar en Fase 0.
---

# SKILL: Despliegue

## 1. Propósito

Guiar la preparación y ejecución del despliegue de EncuentraU en un entorno de producción. Esta Skill solo debe activarse cuando el proyecto haya pasado todas las fases de desarrollo y seguridad.

## ADVERTENCIA

**NO DESPLEGAR EN FASE 0.**

Esta Skill es de referencia para cuando el proyecto esté listo para producción. Activarla prematuramente puede exponer una aplicación incompleta.

El despliegue solo procede cuando:
- Todas las funcionalidades de v1.0 están VERIFICADAS.
- Las pruebas de seguridad pasaron.
- La revisión OWASP está completa.
- Las 100 reglas están evaluadas.
- El revisor-final aprobó.

## 2. Cuándo utilizarla

- Al preparar la configuración de producción.
- Al configurar el servidor web (WSGI).
- Al configurar variables de entorno de producción.
- Al migrar de SQLite a PostgreSQL.
- Al configurar HTTPS.

## 3. Qué debe cubrir

### HTTPS
- [ ] Certificado SSL/TLS válido (Let's Encrypt o equivalente)
- [ ] Redirección automática HTTP → HTTPS
- [ ] HSTS configurado (Strict-Transport-Security)
- [ ] Certificado con renovación automática

### Configuración de producción
- [ ] DEBUG=False
- [ ] FLASK_ENV=production
- [ ] SECRET_KEY larga, aleatoria, única (≥ 64 caracteres)
- [ ] SESSION_COOKIE_SECURE=True
- [ ] Todas las variables sensibles en variables de entorno del sistema (no en .env)

### WSGI
- [ ] Servidor WSGI configurado (Gunicorn recomendado)
- [ ] Workers configurados según capacidad del servidor
- [ ] Logging de acceso configurado

### Base de datos de producción
- [ ] PostgreSQL instalado y configurado
- [ ] Usuario de BD con solo los permisos necesarios (no root)
- [ ] DATABASE_URL en variable de entorno
- [ ] Backups automáticos configurados
- [ ] Migraciones ejecutadas en producción con Flask-Migrate

### Headers de seguridad
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Content-Security-Policy configurado
- [ ] HSTS con max-age adecuado

### CORS en producción
- [ ] Solo el dominio de producción está en ALLOWED_ORIGINS
- [ ] NO usar `*` como origen permitido

### Monitoreo
- [ ] Logging de errores configurado
- [ ] Alertas para errores 500
- [ ] Monitoreo de disponibilidad

## 4. Variables de entorno de producción

```bash
# Obligatorias en producción
SECRET_KEY=<64+ caracteres aleatorios>
FLASK_ENV=production
DATABASE_URL=postgresql://usuario:password@host:5432/encuentrau
FRONTEND_ORIGIN=https://encuentrau.universidad.edu

# Opcionales pero recomendadas
MAX_CONTENT_LENGTH=5242880  # 5 MB
```

## 5. Comando de generación de SECRET_KEY segura

```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

## 6. Configuración de Gunicorn

```bash
gunicorn --workers 2 \
         --bind 0.0.0.0:8000 \
         --access-logfile /var/log/encuentrau/access.log \
         --error-logfile /var/log/encuentrau/error.log \
         "app:create_app()"
```

## 7. Checklist de preparación para producción

### Antes del despliegue
- [ ] Todas las pruebas pasan en el entorno de staging
- [ ] La revisión de seguridad está completa
- [ ] Las 100 reglas están evaluadas
- [ ] El revisor-final aprobó

### Configuración
- [ ] DEBUG=False verificado
- [ ] SECRET_KEY cambiada (no la del desarrollo)
- [ ] SESSION_COOKIE_SECURE=True
- [ ] CORS solo con dominio de producción
- [ ] DATABASE_URL apunta a PostgreSQL

### Infraestructura
- [ ] HTTPS configurado y funcionando
- [ ] WSGI servidor corriendo
- [ ] Migraciones de BD ejecutadas
- [ ] Backups de BD configurados
- [ ] Logs configurados

### Post-despliegue
- [ ] Acceder al sistema y verificar login/registro
- [ ] Verificar que las cookies tienen Secure=True
- [ ] Verificar headers de seguridad
- [ ] Verificar que DEBUG no está activo

## 8. Reglas obligatorias

1. HTTPS es obligatorio en producción. Sin excepciones.
2. DEBUG=False. Sin excepciones.
3. SECRET_KEY es diferente en desarrollo y producción.
4. Los backups de BD se verifican antes del primer despliegue.
5. Nunca desplegar sin haber pasado el checklist de seguridad.

## 9. Errores que debe evitar

- Desplegar con DEBUG=True.
- Usar la misma SECRET_KEY del desarrollo en producción.
- Desplegar sin HTTPS.
- Olvidar ejecutar las migraciones de BD.
- Desplegar sin revisar las 100 reglas de seguridad.

## 10. Documentación que debe actualizar

- `docs/DEPLOYMENT.md` — con los detalles del despliegue realizado.
- `docs/CHANGELOG.md` — con el registro del despliegue.
