# CrystoDolar Backend

Backend completo para cotizaciones de criptomonedas y divisas en Venezuela, con enfoque en USDT/VES, BCV y Binance P2P.

## 🚀 Características Principales

- **🏦 Web Scraping del BCV**: Obtención automática de cotizaciones oficiales del Banco Central de Venezuela
- **🟡 API Binance P2P**: Consulta en tiempo real de precios de compra/venta de USDT con VES
- **🗄️ Base de Datos PostgreSQL**: Almacenamiento persistente con Neon.tech
- **📊 Histórico Completo**: Registro de todas las cotizaciones con timestamps
- **🔄 Scheduler Automático**: Actualizaciones programadas de cotizaciones
- **📝 Logging Avanzado**: Sistema de logs con Loguru y auditoría completa
- **🔒 API REST Completa**: Endpoints para todas las funcionalidades
- **🌐 CORS Configurado**: Soporte para aplicaciones frontend

## 🏗️ Arquitectura del Sistema

### Componentes Principales
- **Data Fetcher**: Servicio para scraping del BCV y API de Binance P2P
- **Database Service**: Capa de abstracción para operaciones de base de datos
- **Models**: Modelos SQLAlchemy para exchanges, cotizaciones y logs
- **API Endpoints**: REST API completa con FastAPI
- **Scheduler**: Sistema de tareas programadas

### Base de Datos
- **PostgreSQL** con Neon.tech (serverless)
- **5 Tablas principales**: exchanges, currency_pairs, rate_history, current_rates, api_logs
- **Relaciones optimizadas** con claves foráneas e índices
- **Auditoría completa** de todas las operaciones

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints Disponibles

#### 🏦 BCV (Banco Central de Venezuela)

##### 1. Scraping en Tiempo Real
```http
GET /api/v1/rates/scrape-bcv
```

**Descripción**: Obtiene cotizaciones actuales del BCV mediante web scraping

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": {
    "usd_ves": 133.5159,
    "eur_ves": 155.75964894,
    "timestamp": "2025-08-12T17:31:00.765405",
    "source": "bcv",
    "scraping_method": "web_scraping",
    "url": "http://www.bcv.org.ve/"
  }
}
```

**Respuesta de Error:**
```json
{
  "status": "error",
  "error": "No se pudieron extraer las cotizaciones"
}
```

#### 🟡 Binance P2P

##### 2. Precios de Compra de USDT (Vender USDT por VES)
```http
GET /api/v1/rates/binance-p2p
```

**Descripción**: Obtiene el mejor precio para vender USDT y recibir VES

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": {
    "usdt_ves_buy": 37.20,
    "usdt_ves_avg": 37.45,
    "volume_24h": 1250.50,
    "best_ad": {
      "price": 37.20,
      "min_amount": 10.0,
      "max_amount": 1000.0,
      "merchant": "TraderPro",
      "pay_types": ["PagoMovil"],
      "user_type": "merchant"
    },
    "total_ads": 15,
    "timestamp": "2025-08-12T17:31:00.765405",
    "source": "binance_p2p",
    "api_method": "official_api",
    "trade_type": "sell_usdt"
  }
}
```

##### 3. Precios de Venta de USDT (Comprar USDT con VES)
```http
GET /api/v1/rates/binance-p2p/sell
```

**Descripción**: Obtiene el mejor precio para comprar USDT con VES

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": {
    "usdt_ves_sell": 37.80,
    "usdt_ves_avg": 37.65,
    "volume_24h": 1250.50,
    "best_ad": {
      "price": 37.80,
      "min_amount": 10.0,
      "max_amount": 1000.0,
      "merchant": "CryptoVendor",
      "pay_types": ["PagoMovil"],
      "user_type": "merchant"
    },
    "total_ads": 12,
    "timestamp": "2025-08-12T17:31:00.765405",
    "source": "binance_p2p",
    "api_method": "official_api",
    "trade_type": "buy_usdt"
  }
}
```

##### 4. Análisis Completo de Binance P2P
```http
GET /api/v1/rates/binance-p2p/complete
```

**Descripción**: Obtiene precios de compra y venta con análisis de spread y liquidez

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": {
    "buy_usdt": {
      "price": 37.80,
      "avg_price": 37.65,
      "best_ad": {...},
      "total_ads": 12
    },
    "sell_usdt": {
      "price": 37.20,
      "avg_price": 37.45,
      "best_ad": {...},
      "total_ads": 15
    },
    "market_analysis": {
      "spread_internal": 0.60,
      "spread_percentage": 1.59,
      "volume_24h": 2501.0,
      "liquidity_score": "high"
    },
    "timestamp": "2025-08-12T17:31:00.765405",
    "source": "binance_p2p",
    "api_method": "official_api"
  }
}
```

#### 📊 Base de Datos

##### 5. Cotizaciones Actuales
```http
GET /api/v1/rates/current
```

**Descripción**: Obtiene las cotizaciones más recientes de la base de datos

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": [
    {
      "exchange_code": "BCV",
      "currency_pair": "USD/VES",
      "buy_price": 133.5159,
      "sell_price": 133.5159,
      "avg_price": 133.5159,
      "volume_24h": null,
      "source": "bcv",
      "last_update": "2025-08-12T17:31:00.765405",
      "market_status": "active"
    },
    {
      "exchange_code": "BINANCE_P2P",
      "currency_pair": "USDT/VES",
      "buy_price": 37.20,
      "sell_price": 37.80,
      "avg_price": 37.50,
      "volume_24h": 2501.0,
      "source": "binance_p2p",
      "last_update": "2025-08-12T17:31:00.765405",
      "market_status": "active"
    }
  ]
}
```

##### 6. Histórico General de Cotizaciones
```http
GET /api/v1/rates/history?limit=100
```

**Descripción**: Obtiene el histórico general de todas las cotizaciones almacenadas

**Parámetros:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": [
    {
      "buy_price": 133.5159,
      "sell_price": 133.5159,
      "avg_price": 133.5159,
      "volume": null,
      "timestamp": "2025-08-12T17:31:00.765405",
      "exchange_name": "Banco Central de Venezuela",
      "exchange_code": "BCV",
      "currency_pair": "USD/VES",
      "base_currency": "USD",
      "quote_currency": "VES"
    }
  ],
  "count": 1,
  "limit": 100
}
```

##### 7. Histórico por Exchange y Par
```http
GET /api/v1/rates/history/{exchange_code}/{pair}?limit=100
```

**Descripción**: Obtiene el histórico de cotizaciones para un exchange y par específico

**Parámetros de Ruta:**
- `exchange_code`: Código del exchange (ej: "BCV", "BINANCE_P2P")
- `pair`: Símbolo del par de divisas (ej: "USD/VES", "USDT/VES")

**Parámetros de Consulta:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": [
    {
      "buy_price": 133.5159,
      "sell_price": 133.5159,
      "avg_price": 133.5159,
      "volume": null,
      "timestamp": "2025-08-12T17:31:00.765405"
    }
  ],
  "count": 1,
  "exchange": "BCV",
  "pair": "USD/VES"
}
```

##### 8. Comparación de Fuentes
```http
GET /api/v1/rates/compare
```

**Descripción**: Compara cotizaciones entre diferentes fuentes (BCV vs Binance P2P)

**Respuesta de Éxito:**
```json
{
  "status": "success",
  "data": {
    "bcv": {
      "usd_ves": 133.5159,
      "eur_ves": 155.75964894,
      "timestamp": "2025-08-12T17:31:00.765405"
    },
    "binance_p2p": {
      "usdt_ves_buy": 37.20,
      "usdt_ves_sell": 37.80,
      "usdt_ves_avg": 37.50,
      "timestamp": "2025-08-12T17:31:00.765405"
    },
    "analysis": {
      "spread_bcv_binance": 96.32,
      "spread_percentage": 258.0,
      "timestamp": "2025-08-12T17:31:00.765405"
    }
  }
}
```

#### 🔧 Utilidades

##### 9. Estado del Servidor
```http
GET /health
```

**Descripción**: Verifica el estado de salud del servidor

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-12T17:31:00.765405",
  "version": "1.0.0"
}
```

## 🛠️ Instalación y Configuración

### Requisitos del Sistema
- **Python**: 3.11+ (recomendado 3.12)
- **Base de Datos**: PostgreSQL (Neon.tech recomendado)
- **Sistema Operativo**: Windows, macOS, Linux

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/crystodolar-backend.git
cd crystodolar-backend
```

### 2. Instalar Dependencias
```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# O instalar individualmente
pip install fastapi uvicorn sqlalchemy asyncpg loguru beautifulsoup4 aiohttp
```

### 3. Configurar Variables de Entorno
Crear archivo `.env` basado en `env.example`:
```bash
cp env.example .env
```

**Variables principales requeridas:**
```env
# Base de Datos (Neon.tech)
DATABASE_URL=postgresql://username:password@ep-name.region.neon.tech/crystodolar?sslmode=require

# Configuración de la API
ENVIRONMENT=development
API_DEBUG=true
LOG_LEVEL=INFO

# Configuración del servidor
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Inicializar la Base de Datos
```bash
# Crear tablas y datos iniciales
python3.12 init_database.py
```

## 🚀 Ejecución

### Servidor Simple (Recomendado para Testing)
```bash
python simple_server.py
```

### Servidor Completo con FastAPI
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Servidor en Producción
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📊 Estructura del Proyecto

```
crystodolar-backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── rates.py              # Endpoints de cotizaciones
│   ├── core/
│   │   ├── config.py             # Configuración de la aplicación
│   │   ├── database.py           # Conexión y configuración de BD
│   │   └── scheduler.py          # Sistema de tareas programadas
│   ├── models/                   # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── rate_models.py        # Modelos de cotizaciones
│   │   ├── exchange_models.py    # Modelos de exchanges
│   │   └── api_models.py         # Modelos de logs
│   └── services/
│       ├── data_fetcher.py       # Scraping BCV y API Binance
│       └── database_service.py   # Operaciones de base de datos
├── database/
│   └── crystodolar_schema.sql    # Esquema de base de datos
├── simple_server.py              # Servidor de prueba simple
├── init_database.py              # Script de inicialización de BD
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Este archivo
```

## 🔧 Configuración Avanzada

### Frecuencias de Actualización
```env
# BCV: Actualización cada hora
BCV_UPDATE_INTERVAL=3600

# Binance P2P: Actualización cada 5 minutos
BINANCE_UPDATE_INTERVAL=300

# Limpieza de datos antiguos: Cada día a las 2 AM
CLEANUP_HOUR=2
```

### Configuración de Scraping
```env
# Máximo de reintentos
MAX_RETRIES=3

# Timeout para conexiones
TIMEOUT_SECONDS=30

# Headers personalizados para scraping
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Configuración de Base de Datos
```env
# Pool de conexiones
POOL_SIZE=5
MAX_OVERFLOW=10
POOL_RECYCLE=300

# Logging de SQL (solo en desarrollo)
API_DEBUG=true
```

## 📝 Sistema de Logs

### Niveles de Log
- **INFO**: Operaciones normales del sistema
- **WARNING**: Situaciones que requieren atención
- **ERROR**: Errores que impiden la operación normal
- **DEBUG**: Información detallada para desarrollo

### Ejemplo de Logs
```
2025-08-12 17:31:00.123 | INFO | 🏦 Iniciando scraping del BCV...
2025-08-12 17:31:00.123 | INFO | 🔗 Intentando conectar a: http://www.bcv.org.ve/
2025-08-12 17:31:00.722 | INFO | ✅ Conexión exitosa a: http://www.bcv.org.ve/
2025-08-12 17:31:00.764 | INFO | 💵 Dólar encontrado: 133.5159
2025-08-12 17:31:00.765 | INFO | 💶 Euro encontrado: 155.75964894
2025-08-12 17:31:00.765 | INFO | ✅ BCV scraping exitoso: USD/VES = 133.5159, EUR/VES = 155.75964894
2025-08-12 17:31:00.766 | INFO | 💾 BCV rates guardados en base de datos
```

## 🧪 Testing y Desarrollo

### Probar Endpoints Individuales

#### BCV Scraping
```bash
curl http://localhost:8000/api/v1/rates/scrape-bcv
```

#### Binance P2P
```bash
# Precios de compra
curl http://localhost:8000/api/v1/rates/binance-p2p

# Precios de venta
curl http://localhost:8000/api/v1/rates/binance-p2p/sell

# Análisis completo
curl http://localhost:8000/api/v1/rates/binance-p2p/complete
```

#### Base de Datos
```bash
# Cotizaciones actuales
curl http://localhost:8000/api/v1/rates/current

# Histórico general
curl http://localhost:8000/api/v1/rates/history?limit=50

# Histórico por exchange y par específico
curl http://localhost:8000/api/v1/rates/history/BCV/USD%2FVES?limit=50
curl http://localhost:8000/api/v1/rates/history/BINANCE_P2P/USDT%2FVES?limit=50

# Comparación
curl http://localhost:8000/api/v1/rates/compare
```

### Verificar Estado del Sistema
```bash
# Salud del servidor
curl http://localhost:8000/health

# Información de la BD
curl http://localhost:8000/api/v1/database/info
```

## 🔒 Seguridad y Monitoreo

### Características de Seguridad
- **Rate Limiting**: Protección contra abuso de la API
- **CORS Configurado**: Solo orígenes autorizados
- **Validación de Datos**: Verificación de valores extraídos
- **Logging de Errores**: Registro de intentos fallidos
- **Auditoría Completa**: Log de todas las operaciones

### Monitoreo Disponible
- **Métricas de Scraping**: Tasa de éxito, tiempo de respuesta
- **Estado de la Base de Datos**: Conexiones activas, performance
- **Logs de API**: Endpoints más usados, errores comunes
- **Alertas Automáticas**: Fallos consecutivos, valores anómalos

## 🚨 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión a la Base de Datos
```bash
# Verificar variables de entorno
echo $DATABASE_URL

# Probar conexión manual
python3.12 -c "from app.core.database import health_check_db; import asyncio; print(asyncio.run(health_check_db()))"
```

#### 2. Error de Scraping del BCV
```bash
# Verificar conectividad
curl -I http://www.bcv.org.ve/

# Revisar logs del servidor
tail -f logs/app.log
```

#### 3. Error de API de Binance
```bash
# Verificar conectividad
curl -I https://p2p.binance.com/

# Probar endpoint directamente
curl -X POST https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search
```

### Logs de Debug
```bash
# Activar logging detallado
export LOG_LEVEL=DEBUG

# Ejecutar servidor con debug
uvicorn app.main:app --reload --log-level debug
```

## 🤝 Contribución

### Cómo Contribuir
1. **Fork** del proyecto
2. **Crear rama** para feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** de cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abrir Pull Request**

### Estándares de Código
- **Python**: PEP 8, type hints
- **SQL**: Estándares PostgreSQL
- **API**: OpenAPI 3.0, RESTful
- **Logging**: Estructurado con Loguru
- **Testing**: pytest, cobertura mínima 80%

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver `LICENSE` para más detalles.

## 🆘 Soporte y Contacto

### Canales de Soporte
- **GitHub Issues**: Para reportar bugs y solicitar features
- **Documentación**: `/docs` endpoint para documentación automática de la API
- **Logs del Sistema**: Para debugging y monitoreo

### Recursos Adicionales
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Documentación alternativa)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

**⚠️ Nota Importante**: Este sistema está diseñado para uso educativo y de desarrollo. Para uso en producción, considere implementar medidas adicionales de seguridad, monitoreo y backup de datos.

**🚀 Última Actualización**: Agosto 2025 - Versión 1.0.0 con Base de Datos Completa
