# 🚀 CrystoAPIVzla - Setup con Neon.tech

## 📋 **Instrucciones de configuración**

### 1. **Crear proyecto en Neon.tech**
1. Ve a [neon.tech](https://neon.tech) y crea una cuenta
2. Crear nuevo proyecto: **crystoapivzla**
3. Seleccionar región más cercana (US East para mejor latencia desde Venezuela)
4. Copiar la cadena de conexión

### 2. **Ejecutar el schema**
```bash
# Conectarse a Neon usando psql
psql "postgresql://[user]:[password]@[endpoint]/[dbname]?sslmode=require"

# O ejecutar directamente el archivo
psql "postgresql://[connection_string]" -f database/crystoapivzla_schema.sql
```

### 3. **Variables de entorno para FastAPI**
Crear archivo `.env`:
```env
# Neon.tech Database
DATABASE_URL=postgresql://[user]:[password]@[endpoint]/[dbname]?sslmode=require
NEON_DATABASE_URL=postgresql://[user]:[password]@[endpoint]/[dbname]?sslmode=require

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# External APIs
BCV_API_URL=https://api.bcv.org.ve
BINANCE_API_URL=https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cache (Redis opcional)
REDIS_URL=redis://localhost:6379

# Rate Limiting
REQUESTS_PER_MINUTE=60
```

## 🔧 **Diferencias con Supabase**

### ❌ **No disponible en Neon.tech:**
- `pg_cron` (tareas programadas)
- `auth.role()` (sistema de autenticación)
- Funciones de autenticación integradas
- Storage de archivos
- Real-time subscriptions

### ✅ **Disponible en Neon.tech:**
- PostgreSQL completo
- Extensiones básicas (`uuid-ossp`, etc.)
- Triggers y funciones personalizadas
- Views y índices
- Conexiones serverless
- Branching de base de datos (perfecto para desarrollo)

## 📊 **Estrategias para reemplazar funcionalidades faltantes**

### 1. **Tareas programadas (reemplazo de pg_cron)**
Usar APScheduler en FastAPI:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# Limpiar datos cada día a las 2:00 AM
scheduler.add_job(
    cleanup_old_data,
    CronTrigger(hour=2, minute=0),
    id='cleanup_old_data'
)

scheduler.start()
```

### 2. **Autenticación (reemplazo de Supabase Auth)**
Usar JWT con FastAPI:
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
```

### 3. **Real-time (reemplazo de Supabase Realtime)**
Usar WebSockets con FastAPI:
```python
from fastapi import WebSocket
import asyncio

@app.websocket("/ws/rates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Enviar updates en tiempo real
```

## 🎯 **Ventajas de Neon.tech para CrystoAPIVzla**

### ✅ **Pros:**
- **Branching**: Crear ramas de BD para testing
- **Serverless**: Solo pagas por uso
- **Autoscaling**: Escala automáticamente
- **Backups automáticos**: Point-in-time recovery
- **Mejor rendimiento**: Para aplicaciones con mucha carga de BD
- **PostgreSQL puro**: Sin vendor lock-in

### ⚠️ **Consideraciones:**
- **Latencia**: Servidores en US (no Venezuela)
- **Cold starts**: Primera consulta puede ser lenta
- **Límites de conexiones**: En plan gratuito

## 🚀 **Comandos útiles**

### Backup local:
```bash
pg_dump "postgresql://[connection_string]" > backup.sql
```

### Restore:
```bash
psql "postgresql://[connection_string]" < backup.sql
```

### Monitoreo:
```bash
# Ver conexiones activas
SELECT count(*) FROM pg_stat_activity;

# Ver tamaño de tablas
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables 
WHERE schemaname = 'public';
```

## 📝 **Próximos pasos**

1. ✅ Ejecutar `crystoapivzla_schema.sql` en Neon
2. 🔄 Crear proyecto FastAPI 
3. 🔄 Implementar scraping de BCV y Binance
4. 🔄 Crear endpoints de API
5. 🔄 Conectar frontend React
6. 🔄 Implementar WebSockets para real-time
7. 🔄 Deploy en producción

---
**Última actualización:** $(date)
