# Configuración de Variables de Entorno en Railway

## Variables OBLIGATORIAS para producción:

### 1. DATABASE_URL
```
DATABASE_URL=postgresql://username:password@ep-name.region.neon.tech/crystodolar?sslmode=require
```
**Valor real:** Tu conexión real a Neon.tech

### 2. SECRET_KEY
```
SECRET_KEY=tu-clave-super-secreta-de-64-caracteres-minimo
```
**Generar con:** `openssl rand -hex 32`

### 3. ENVIRONMENT
```
ENVIRONMENT=production
```

## Variables IMPORTANTES para producción:

### 4. API_DEBUG
```
API_DEBUG=False
```

### 5. API_RELOAD
```
API_RELOAD=False
```

### 6. LOG_LEVEL
```
LOG_LEVEL=INFO
```

## Variables OPCIONALES:

### 7. CORS_ORIGINS (si tienes frontend)
```
CORS_ORIGINS=["https://tu-dominio.com", "https://www.tu-dominio.com"]
```

### 8. SENTRY_DSN (si usas Sentry)
```
SENTRY_DSN=https://tu-dsn@sentry.io/project-id
```

## Variables que NO necesitas en Railway:

- `API_HOST` - Railway lo maneja automáticamente
- `API_PORT` - Railway usa `$PORT`
- `NEON_ENDPOINT`, `NEON_DATABASE`, etc. - Ya están en `DATABASE_URL`
- `REDIS_URL` - Solo si usas Redis
- `TELEGRAM_BOT_TOKEN` - Solo si usas bot de Telegram
- `EMAIL_*` - Solo si usas notificaciones por email

## Cómo configurar en Railway:

1. Ve a tu proyecto en Railway
2. Click en "Variables"
3. Agrega cada variable con su valor
4. Haz redeploy después de cambiar variables

## Ejemplo de configuración mínima:

```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.region.neon.tech/crystodolar?sslmode=require
SECRET_KEY=tu-clave-secreta-de-64-caracteres
ENVIRONMENT=production
API_DEBUG=False
API_RELOAD=False
LOG_LEVEL=INFO
```
