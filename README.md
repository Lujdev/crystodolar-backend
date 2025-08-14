# 🚀 CrystoDolar API

API para cotizaciones USDT/VES en tiempo real con guardado automático en base de datos.

## 📋 Características

- **Cotizaciones en tiempo real** de BCV y Binance P2P
- **Guardado automático** en `rate_history` para análisis histórico
- **Comparación de exchanges** con cálculo de spreads
- **Variaciones y tendencias** calculadas automáticamente
- **Optimizado para Railway** con configuración de producción

## 🏗️ Estructura del Proyecto

```
crystodolar-backend/
├── app/
│   ├── api/v1/endpoints/     # Endpoints de la API
│   ├── core/                 # Configuración y base de datos
│   ├── models/               # Modelos de datos
│   └── services/             # Lógica de negocio
├── database/                 # Esquemas y configuración de BD
├── simple_server_railway.py  # Servidor principal para Railway
└── requirements.txt          # Dependencias
```

## 🚀 Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd crystodolar-backend

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar servidor
python simple_server_railway.py
```

## ⚙️ Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db

# Entorno
ENVIRONMENT=production  # production, development
PORT=8000

# Logs
LOG_LEVEL=warning  # warning, info, debug
```

## 📚 Endpoints de la API

### 🔍 Información General

#### `GET /`
Información básica de la API.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message": "CrystoDolar API Simple",
    "version": "1.0.0",
    "description": "Cotizaciones USDT/VES en tiempo real",
    "sources": ["BCV", "Binance P2P"],
    "docs": "/docs",
    "status": "operational",
    "environment": "production"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /health`
Health check para Railway.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "crystodolar-backend",
    "message": "Service is running",
    "environment": "production",
    "database_url": "configured"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/status`
Estado del sistema.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "service": "crystodolar-backend",
    "version": "1.0.0",
    "environment": "production",
    "database_configured": true
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### 💰 Cotizaciones

#### `GET /api/v1/rates/current`
Obtener cotizaciones actuales con guardado automático.

**Parámetros:**
- `exchange_code` (opcional): Filtrar por exchange (`bcv`, `binance_p2p`)
- `currency_pair` (opcional): Filtrar por par de monedas

**Ejemplo:**
```bash
GET /api/v1/rates/current?exchange_code=bcv
```

**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "exchange_code": "bcv",
      "currency_pair": "USD/VES",
      "base_currency": "USD",
      "quote_currency": "VES",
      "buy_price": 35.85,
      "sell_price": 35.85,
      "avg_price": 35.85,
      "variation_percentage": "+0.15%",
      "trend_main": "up",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "count": 1,
  "source": "realtime_with_variations",
  "auto_saved_to_history": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/summary`
Resumen del mercado con análisis de spreads.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "total_rates": 2,
    "exchanges_active": 2,
    "last_update": "2024-01-15T10:30:00",
    "rates": [...],
    "market_analysis": {
      "bcv_usd": 35.85,
      "binance_usdt": 36.20,
      "spread_ves": 0.35,
      "spread_percentage": 0.98,
      "market_difference": "premium"
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/compare`
Comparar cotizaciones entre BCV y Binance P2P.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "bcv": {
      "exchange_code": "bcv",
      "currency_pair": "USD/VES",
      "usd_ves": 35.85,
      "eur_ves": 39.12
    },
    "binance_p2p": {
      "exchange_code": "binance_p2p",
      "currency_pair": "USDT/VES",
      "usdt_ves_buy": 36.20,
      "usdt_ves_sell": 36.15,
      "usdt_ves_avg": 36.18
    },
    "analysis": {
      "spread_bcv_binance": 0.33,
      "spread_percentage": 0.92
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 🏦 Fuentes Específicas

#### `GET /api/v1/rates/bcv`
Cotización oficial del BCV.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "exchange_code": "bcv",
    "currency_pair": "USD/VES",
    "buy_price": 35.85,
    "sell_price": 35.85,
    "avg_price": 35.85,
    "source": "bcv",
    "api_method": "web_scraping",
    "trade_type": "official"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/binance-p2p/complete`
Precios completos de Binance P2P.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "exchange_code": "binance_p2p",
    "currency_pair": "USDT/VES",
    "buy_usdt": {
      "price": 36.20,
      "avg_price": 36.18
    },
    "sell_usdt": {
      "price": 36.15,
      "avg_price": 36.18
    },
    "market_analysis": {
      "spread_internal": 0.05,
      "spread_percentage": 0.14,
      "volume_24h": 1250.50,
      "liquidity_score": "high"
    }
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### 📊 Histórico y Estado

#### `GET /api/v1/rates/history`
Obtener histórico de cotizaciones.

**Parámetros:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Ejemplo:**
```bash
GET /api/v1/rates/history?limit=50
```

#### `GET /api/v1/rates/auto-save-status`
Estado del guardado automático.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "auto_save_enabled": true,
    "database_available": true,
    "total_records_in_history": 15420,
    "exchange_statistics": [
      {
        "exchange_code": "BCV",
        "total_records": 8230,
        "last_update": "2024-01-15T10:30:00"
      }
    ],
    "auto_save_endpoints": [
      "/api/v1/rates/current",
      "/api/v1/rates/summary",
      "/api/v1/rates/compare"
    ]
  }
}
```

### 🔄 Operaciones

#### `POST /api/v1/rates/refresh`
Forzar actualización de cotizaciones.

**Parámetros:**
- `exchange_code` (opcional): Exchange específico a actualizar

**Ejemplo:**
```bash
POST /api/v1/rates/refresh
Content-Type: application/json

{
  "exchange_code": "bcv"
}
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message": "Actualización iniciada",
    "exchanges_updated": ["bcv"],
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

## 🗄️ Base de Datos

### Esquema Principal

```sql
-- Tabla de historial de tasas
CREATE TABLE rate_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange_code VARCHAR(50) NOT NULL,
    currency_pair VARCHAR(20) NOT NULL,
    buy_price DECIMAL(15,4),
    sell_price DECIMAL(15,4),
    avg_price DECIMAL(15,4),
    volume_24h DECIMAL(15,2),
    source VARCHAR(100),
    api_method VARCHAR(50),
    trade_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Guardado Automático

Los siguientes endpoints guardan automáticamente en `rate_history`:
- `/api/v1/rates/current` - Todas las tasas obtenidas
- `/api/v1/rates/summary` - Tasas del resumen
- `/api/v1/rates/compare` - Tasas de comparación

**Lógica inteligente:** Solo se insertan tasas con cambios significativos (>0.01% por defecto).

## 🚀 Despliegue en Railway

### Configuración Automática

```bash
# Railway detecta automáticamente:
# - PORT desde variables de entorno
# - DATABASE_URL para conexión a PostgreSQL
# - ENVIRONMENT para configuración de producción
```

### Variables de Entorno en Railway

```bash
DATABASE_URL=postgresql://...
ENVIRONMENT=production
PORT=8000
LOG_LEVEL=warning
```

## 🧪 Testing

### Endpoints de Prueba

```bash
# Health check
curl https://your-app.railway.app/health

# Cotizaciones actuales
curl https://your-app.railway.app/api/v1/rates/current

# Estado del sistema
curl https://your-app.railway.app/api/v1/status
```

### Validación de Respuestas

Todas las respuestas incluyen:
- `status`: `success` o `error`
- `timestamp`: ISO 8601
- `data` o `error`: Contenido de la respuesta

## 📈 Monitoreo

### Métricas Disponibles

- **Total de registros** en `rate_history`
- **Estadísticas por exchange** y día
- **Estado del guardado automático**
- **Últimas tasas registradas**

### Logs del Sistema

```bash
# Nivel de log configurable por ENVIRONMENT
# production: warning
# development: info
```

## 🔧 Desarrollo

### Estructura de Código

- **FastAPI** para la API web
- **asyncpg** para conexiones a PostgreSQL
- **BeautifulSoup** para scraping del BCV
- **httpx** para llamadas HTTP asíncronas

### Agregar Nuevos Exchanges

1. Implementar función de scraping
2. Agregar endpoint en `/api/v1/rates/`
3. Integrar con sistema de guardado automático
4. Actualizar documentación

## 📝 Licencia

Este proyecto está bajo la licencia MIT.

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Revisar la documentación en `/docs`
- Verificar el estado del sistema en `/api/v1/status`
