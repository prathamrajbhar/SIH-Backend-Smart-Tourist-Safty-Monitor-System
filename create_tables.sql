-- 🗃️ Smart Tourist Safety System Database Schema
-- Copy and paste this into Supabase SQL Editor

-- Enable PostGIS if not already enabled (for spatial data)
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Tourists Table
CREATE TABLE IF NOT EXISTS tourists (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    contact VARCHAR UNIQUE NOT NULL,
    email VARCHAR,
    trip_info JSONB DEFAULT '{}',
    emergency_contact VARCHAR NOT NULL,
    safety_score INTEGER DEFAULT 100 CHECK (safety_score >= 0 AND safety_score <= 100),
    age INTEGER CHECK (age >= 0 AND age <= 150),
    nationality VARCHAR DEFAULT 'Indian',
    passport_number VARCHAR,
    is_active BOOLEAN DEFAULT true,
    last_location_update TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Locations Table
CREATE TABLE IF NOT EXISTS locations (
    id BIGSERIAL PRIMARY KEY,
    tourist_id BIGINT REFERENCES tourists(id) ON DELETE CASCADE,
    latitude NUMERIC(10,7) CHECK (latitude >= -90 AND latitude <= 90) NOT NULL,
    longitude NUMERIC(11,7) CHECK (longitude >= -180 AND longitude <= 180) NOT NULL,
    altitude NUMERIC,
    accuracy NUMERIC,
    speed NUMERIC,
    heading NUMERIC CHECK (heading >= 0 AND heading <= 360),
    timestamp TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Location History Table  
CREATE TABLE IF NOT EXISTS location_history (
    id BIGSERIAL PRIMARY KEY,
    tourist_id BIGINT REFERENCES tourists(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    location_data JSONB NOT NULL,
    total_distance NUMERIC,
    unique_locations INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    tourist_id BIGINT REFERENCES tourists(id) ON DELETE CASCADE,
    type VARCHAR NOT NULL CHECK (type IN ('panic', 'geofence', 'anomaly', 'temporal', 'low_safety_score', 'sos', 'manual')),
    severity VARCHAR DEFAULT 'LOW' NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    message TEXT NOT NULL,
    description TEXT,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    ai_confidence NUMERIC(3,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    auto_generated BOOLEAN DEFAULT false,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR,
    acknowledged_at TIMESTAMPTZ,
    resolved_by VARCHAR,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT now(),
    status VARCHAR DEFAULT 'active' NOT NULL CHECK (status IN ('active', 'acknowledged', 'resolved', 'false_alarm')),
    alert_metadata JSONB DEFAULT '{}'
);

-- 5. Safe Zones Table
CREATE TABLE IF NOT EXISTS safe_zones (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    zone_type VARCHAR CHECK (zone_type IN ('tourist_area', 'hotel', 'restaurant', 'transport_hub', 'hospital', 'police_station')),
    coordinates JSONB NOT NULL,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR DEFAULT 'India',
    safety_rating INTEGER DEFAULT 5 CHECK (safety_rating >= 1 AND safety_rating <= 5),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 6. Restricted Zones Table
CREATE TABLE IF NOT EXISTS restricted_zones (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    zone_type VARCHAR CHECK (zone_type IN ('restricted', 'military', 'private', 'dangerous', 'construction', 'natural_hazard')),
    coordinates JSONB NOT NULL,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR DEFAULT 'India',
    danger_level INTEGER DEFAULT 3 CHECK (danger_level >= 1 AND danger_level <= 5),
    buffer_zone_meters INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 7. AI Assessments Table
CREATE TABLE IF NOT EXISTS ai_assessments (
    id BIGSERIAL PRIMARY KEY,
    tourist_id BIGINT REFERENCES tourists(id) ON DELETE CASCADE,
    location_id BIGINT REFERENCES locations(id) ON DELETE CASCADE,
    safety_score INTEGER NOT NULL CHECK (safety_score >= 0 AND safety_score <= 100),
    severity VARCHAR NOT NULL CHECK (severity IN ('SAFE', 'WARNING', 'CRITICAL')),
    geofence_alert BOOLEAN DEFAULT false,
    anomaly_score NUMERIC(3,2) CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    temporal_risk_score NUMERIC(3,2) CHECK (temporal_risk_score >= 0 AND temporal_risk_score <= 1),
    supervised_prediction NUMERIC(3,2) CHECK (supervised_prediction >= 0 AND supervised_prediction <= 1),
    confidence_level NUMERIC(3,2) NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
    recommended_action VARCHAR,
    alert_message TEXT,
    model_versions JSONB DEFAULT '{}',
    processing_time_ms NUMERIC,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 8. AI Model Predictions Table
CREATE TABLE IF NOT EXISTS ai_model_predictions (
    id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT REFERENCES ai_assessments(id) ON DELETE CASCADE,
    model_name VARCHAR CHECK (model_name IN ('geofence', 'isolation_forest', 'temporal_autoencoder', 'lightgbm_classifier')),
    prediction_value NUMERIC(3,2) CHECK (prediction_value >= 0 AND prediction_value <= 1),
    confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    processing_time_ms NUMERIC,
    model_version VARCHAR,
    model_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 9. API Logs Table
CREATE TABLE IF NOT EXISTS api_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms NUMERIC,
    user_agent TEXT,
    ip_address INET,
    request_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 10. System Metrics Table
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_type VARCHAR CHECK (metric_type IN ('cpu_usage', 'memory_usage', 'active_tourists', 'requests_per_minute', 'error_rate')),
    value NUMERIC NOT NULL,
    unit VARCHAR,
    metric_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_tourists_contact ON tourists(contact);
CREATE INDEX IF NOT EXISTS idx_tourists_active ON tourists(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_locations_tourist_id ON locations(tourist_id);
CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_tourist_id ON alerts(tourist_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_assessments_tourist_id ON ai_assessments(tourist_id);
CREATE INDEX IF NOT EXISTS idx_ai_assessments_created_at ON ai_assessments(created_at);

-- Insert Sample Data

-- Sample Tourists
INSERT INTO tourists (name, contact, email, emergency_contact, trip_info) VALUES
('Rahul Sharma', '+91-9876543210', 'rahul@email.com', '+91-9876543211', '{"destination": "Delhi", "duration": 3}'),
('Priya Singh', '+91-8765432109', 'priya@email.com', '+91-8765432110', '{"destination": "Goa", "duration": 7}'),
('John Smith', '+1-555-0123', 'john@email.com', '+1-555-0124', '{"destination": "India Tour", "duration": 14}'),
('Alice Johnson', '+44-20-1234-5678', 'alice@email.com', '+44-20-1234-5679', '{"destination": "Golden Triangle", "duration": 10}'),
('David Brown', '+61-412-345-678', 'david@email.com', '+61-412-345-679', '{"destination": "Kerala", "duration": 12}')
ON CONFLICT (contact) DO NOTHING;

-- Sample Safe Zones
INSERT INTO safe_zones (name, zone_type, coordinates, city, state, safety_rating) VALUES
('India Gate Area', 'tourist_area', '{"type": "Polygon", "coordinates": [[[77.227, 28.612], [77.232, 28.612], [77.232, 28.616], [77.227, 28.616], [77.227, 28.612]]]}', 'Delhi', 'Delhi', 5),
('Red Fort Complex', 'tourist_area', '{"type": "Polygon", "coordinates": [[[77.238, 28.656], [77.242, 28.656], [77.242, 28.660], [77.238, 28.660], [77.238, 28.656]]]}', 'Delhi', 'Delhi', 4),
('Connaught Place', 'tourist_area', '{"type": "Polygon", "coordinates": [[[77.218, 28.628], [77.222, 28.628], [77.222, 28.632], [77.218, 28.632], [77.218, 28.628]]]}', 'Delhi', 'Delhi', 4),
('Baga Beach', 'tourist_area', '{"type": "Polygon", "coordinates": [[[73.751, 15.555], [73.755, 15.555], [73.755, 15.559], [73.751, 15.559], [73.751, 15.555]]]}', 'Panaji', 'Goa', 5),
('Calangute Beach', 'tourist_area', '{"type": "Polygon", "coordinates": [[[73.754, 15.543], [73.758, 15.543], [73.758, 15.547], [73.754, 15.547], [73.754, 15.543]]]}', 'Panaji', 'Goa', 5);

-- Sample Restricted Zones  
INSERT INTO restricted_zones (name, zone_type, coordinates, city, state, danger_level) VALUES
('Military Area - Red Fort Vicinity', 'military', '{"type": "Polygon", "coordinates": [[[77.240, 28.654], [77.244, 28.654], [77.244, 28.658], [77.240, 28.658], [77.240, 28.654]]]}', 'Delhi', 'Delhi', 5),
('Construction Zone - CP', 'construction', '{"type": "Polygon", "coordinates": [[[77.216, 28.626], [77.220, 28.626], [77.220, 28.630], [77.216, 28.630], [77.216, 28.626]]]}', 'Delhi', 'Delhi', 3),
('Restricted Naval Area', 'military', '{"type": "Polygon", "coordinates": [[[73.749, 15.553], [73.753, 15.553], [73.753, 15.557], [73.749, 15.557], [73.749, 15.553]]]}', 'Panaji', 'Goa', 4);

-- Sample Locations (recent)
INSERT INTO locations (tourist_id, latitude, longitude, speed, timestamp) VALUES
(1, 28.6129, 77.2295, 5.2, now() - interval '5 minutes'),
(2, 15.5557, 73.7519, 2.1, now() - interval '10 minutes'), 
(3, 28.6304, 77.2177, 0.0, now() - interval '2 minutes'),
(4, 28.6562, 77.2410, 3.5, now() - interval '7 minutes'),
(5, 15.5449, 73.7553, 1.8, now() - interval '15 minutes');

-- Welcome message
SELECT '🎉 Database setup completed successfully!' as status,
       '📊 All tables created with sample data' as details,
       '🚀 Ready to start the server!' as next_step;