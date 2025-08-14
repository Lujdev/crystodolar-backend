-- ========================================
-- CrystoAPIVzla - Estructura de Base de Datos
-- FastAPI + Neon.tech
-- ========================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- TABLAS PRINCIPALES
-- ========================================

-- Tabla de fuentes de datos (exchanges)
CREATE TABLE exchanges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  code VARCHAR(20) UNIQUE NOT NULL,
  type VARCHAR(20) NOT NULL CHECK (type IN ('fiat', 'crypto')),
  base_url VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  operating_hours JSONB,
  update_frequency INTEGER DEFAULT 300,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de pares de monedas
CREATE TABLE currency_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_currency VARCHAR(10) NOT NULL,
  quote_currency VARCHAR(10) NOT NULL,
  symbol VARCHAR(20) UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de cotizaciones actuales
CREATE TABLE current_rates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE CASCADE,
  currency_pair_id UUID REFERENCES currency_pairs(id) ON DELETE CASCADE,
  buy_price DECIMAL(15,4) NOT NULL,
  sell_price DECIMAL(15,4) NOT NULL,
  variation_24h DECIMAL(8,4) DEFAULT 0,
  volume_24h DECIMAL(20,4),
  last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  source_timestamp TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT true,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(exchange_id, currency_pair_id)
);

-- Tabla de histórico de cotizaciones
CREATE TABLE rate_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE CASCADE,
  currency_pair_id UUID REFERENCES currency_pairs(id) ON DELETE CASCADE,
  buy_price DECIMAL(15,4) NOT NULL,
  sell_price DECIMAL(15,4) NOT NULL,
  avg_price DECIMAL(15,4) GENERATED ALWAYS AS ((buy_price + sell_price) / 2) STORED,
  volume DECIMAL(20,4),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de estado del mercado
CREATE TABLE market_status (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE CASCADE,
  is_open BOOLEAN DEFAULT false,
  status VARCHAR(50) DEFAULT 'unknown' CHECK (status IN ('open', 'closed', 'maintenance', 'unknown')),
  next_open TIMESTAMP WITH TIME ZONE,
  next_close TIMESTAMP WITH TIME ZONE,
  last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(exchange_id)
);

-- Tabla de logs de APIs externas
CREATE TABLE api_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE SET NULL,
  endpoint VARCHAR(255),
  status_code INTEGER,
  response_time_ms INTEGER,
  error_message TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ========================================

-- Índices para rate_history (consultas de gráficas)
CREATE INDEX idx_rate_history_timestamp ON rate_history(timestamp DESC);
CREATE INDEX idx_rate_history_exchange_pair ON rate_history(exchange_id, currency_pair_id);
CREATE INDEX idx_rate_history_timeframe ON rate_history(exchange_id, currency_pair_id, timestamp DESC);

-- Índices para current_rates
CREATE INDEX idx_current_rates_active ON current_rates(is_active) WHERE is_active = true;
CREATE INDEX idx_current_rates_last_update ON current_rates(last_update DESC);

-- Índices para api_logs
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX idx_api_logs_exchange ON api_logs(exchange_id, timestamp DESC);

-- ========================================
-- FUNCIONES Y TRIGGERS
-- ========================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_exchanges_updated_at
  BEFORE UPDATE ON exchanges
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_status_updated_at
  BEFORE UPDATE ON market_status
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Función para limpiar datos antiguos
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
  -- Eliminar histórico mayor a 90 días
  DELETE FROM rate_history 
  WHERE timestamp < NOW() - INTERVAL '90 days';
  
  -- Eliminar logs mayor a 30 días
  DELETE FROM api_logs 
  WHERE timestamp < NOW() - INTERVAL '30 days';
  
  -- Log de limpieza
  RAISE NOTICE 'Limpieza de datos antiguos completada en %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Función para calcular variación de precio
CREATE OR REPLACE FUNCTION calculate_price_variation(
  p_exchange_id UUID,
  p_currency_pair_id UUID,
  p_current_price DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
  yesterday_price DECIMAL;
  variation DECIMAL;
BEGIN
  -- Obtener precio de hace 24 horas
  SELECT avg_price INTO yesterday_price
  FROM rate_history
  WHERE exchange_id = p_exchange_id
    AND currency_pair_id = p_currency_pair_id
    AND timestamp >= NOW() - INTERVAL '24 hours 30 minutes'
    AND timestamp <= NOW() - INTERVAL '23 hours 30 minutes'
  ORDER BY timestamp ASC
  LIMIT 1;
  
  -- Calcular variación porcentual
  IF yesterday_price IS NOT NULL AND yesterday_price > 0 THEN
    variation := ((p_current_price - yesterday_price) / yesterday_price) * 100;
  ELSE
    variation := 0;
  END IF;
  
  RETURN ROUND(variation, 4);
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- VISTAS PARA EL FRONTEND
-- ========================================

-- Vista principal para datos del mercado
CREATE VIEW current_market_data AS
SELECT 
  e.id as exchange_id,
  e.name as exchange_name,
  e.code as exchange_code,
  e.type as exchange_type,
  e.description,
  cp.id as currency_pair_id,
  cp.symbol as currency_pair,
  cp.base_currency,
  cp.quote_currency,
  cr.buy_price,
  cr.sell_price,
  cr.variation_24h,
  cr.volume_24h,
  cr.last_update,
  ms.is_open as market_open,
  ms.status as market_status,
  ms.next_open,
  ms.next_close
FROM current_rates cr
JOIN exchanges e ON cr.exchange_id = e.id
JOIN currency_pairs cp ON cr.currency_pair_id = cp.id
LEFT JOIN market_status ms ON e.id = ms.exchange_id
WHERE cr.is_active = true AND e.is_active = true
ORDER BY e.type, e.name;

-- Vista para datos históricos optimizada
CREATE VIEW historical_rates_view AS
SELECT 
  rh.id,
  e.code as exchange_code,
  e.name as exchange_name,
  e.type as exchange_type,
  cp.symbol as currency_pair,
  rh.buy_price,
  rh.sell_price,
  rh.avg_price,
  rh.volume,
  rh.timestamp,
  DATE_TRUNC('hour', rh.timestamp) as hour_bucket,
  DATE_TRUNC('day', rh.timestamp) as day_bucket
FROM rate_history rh
JOIN exchanges e ON rh.exchange_id = e.id
JOIN currency_pairs cp ON rh.currency_pair_id = cp.id
WHERE e.is_active = true;

-- ========================================
-- POLÍTICAS RLS (Row Level Security)
-- ========================================
-- Nota: RLS deshabilitado para Neon.tech
-- Se manejará la seguridad desde FastAPI

-- ========================================
-- DATOS INICIALES
-- ========================================

-- Insertar exchanges iniciales
INSERT INTO exchanges (name, code, type, description, operating_hours, update_frequency) VALUES
(
  'Banco Central de Venezuela', 
  'bcv', 
  'fiat', 
  'Tasa oficial del Banco Central de Venezuela',
  '{"start": "09:00", "end": "16:00", "timezone": "VET", "days": [1,2,3,4,5]}'::jsonb,
  3600
),
(
  'Binance P2P Venezuela', 
  'binance_p2p', 
  'crypto', 
  'Mercado P2P de Binance para Venezuela',
  '{"start": "00:00", "end": "23:59", "timezone": "UTC", "days": [0,1,2,3,4,5,6]}'::jsonb,
  300
);

-- Insertar pares de monedas
INSERT INTO currency_pairs (base_currency, quote_currency, symbol) VALUES
('USDT', 'VES', 'USDT/VES'),
('USD', 'VES', 'USD/VES');

-- Insertar estado inicial del mercado
INSERT INTO market_status (exchange_id, is_open, status) 
SELECT id, true, 'open' FROM exchanges;

-- ========================================
-- DATOS MOCK PARA DESARROLLO
-- ========================================

-- Solo insertar si no hay datos de producción
DO $$
DECLARE
  bcv_id UUID;
  binance_id UUID;
  usdt_ves_id UUID;
  usd_ves_id UUID;
BEGIN
  -- Obtener IDs
  SELECT id INTO bcv_id FROM exchanges WHERE code = 'bcv';
  SELECT id INTO binance_id FROM exchanges WHERE code = 'binance_p2p';
  SELECT id INTO usdt_ves_id FROM currency_pairs WHERE symbol = 'USDT/VES';
  SELECT id INTO usd_ves_id FROM currency_pairs WHERE symbol = 'USD/VES';
  
  -- Datos mock para current_rates
  INSERT INTO current_rates (exchange_id, currency_pair_id, buy_price, sell_price, variation_24h) VALUES
  (bcv_id, usdt_ves_id, 36.50, 36.50, 0.0),
  (binance_id, usdt_ves_id, 37.20, 37.80, -1.2);
  
  -- Generar histórico mock (últimos 30 días)
  INSERT INTO rate_history (exchange_id, currency_pair_id, buy_price, sell_price, timestamp)
  SELECT 
    bcv_id,
    usdt_ves_id,
    36.5 + (random() * 2 - 1), -- Variación de ±1
    36.5 + (random() * 2 - 1),
    NOW() - (i || ' hours')::INTERVAL
  FROM generate_series(1, 720) i; -- 30 días cada hora
  
  INSERT INTO rate_history (exchange_id, currency_pair_id, buy_price, sell_price, timestamp)
  SELECT 
    binance_id,
    usdt_ves_id,
    37.0 + (random() * 3 - 1.5), -- Variación de ±1.5
    37.5 + (random() * 3 - 1.5),
    NOW() - (i || ' hours')::INTERVAL
  FROM generate_series(1, 720) i;
  
  RAISE NOTICE 'Datos mock insertados correctamente';
END $$;

-- ========================================
-- TAREAS AUTOMÁTICAS
-- ========================================
-- Nota: Neon.tech no incluye pg_cron por defecto
-- La limpieza se ejecutará desde FastAPI con un scheduler
-- Ejemplo: APScheduler para ejecutar cleanup_old_data() diariamente

-- ========================================
-- COMENTARIOS FINALES
-- ========================================

-- COMMENT ON DATABASE postgres IS 'CrystoAPIVzla - Base de datos para cotizaciones USDT/VES';
-- Nota: El comando COMMENT ON DATABASE puede requerir permisos especiales en Neon.tech
COMMENT ON TABLE exchanges IS 'Fuentes de datos de cotizaciones (BCV, Binance, etc.)';
COMMENT ON TABLE currency_pairs IS 'Pares de monedas soportados';
COMMENT ON TABLE current_rates IS 'Cotizaciones actuales en tiempo real';
COMMENT ON TABLE rate_history IS 'Histórico de cotizaciones para gráficas';
COMMENT ON TABLE market_status IS 'Estado actual de cada mercado';
COMMENT ON TABLE api_logs IS 'Logs de llamadas a APIs externas';

-- ========================================
-- VERSIÓN Y METADATOS
-- ========================================

CREATE TABLE IF NOT EXISTS schema_version (
  version VARCHAR(10) PRIMARY KEY,
  applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  description TEXT
);

INSERT INTO schema_version (version, description) VALUES 
('1.0.0', 'Schema inicial de CrystoAPIVzla con soporte para BCV y Binance P2P');

-- Fin del archivo
