-- ============================================
-- AGREGAR CONFIGURACIÓN DE EMAIL A CLIENTS
-- ============================================

-- Columnas para configuración SMTP
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS email_smtp_server TEXT DEFAULT 'smtp.gmail.com',
ADD COLUMN IF NOT EXISTS email_smtp_port INTEGER DEFAULT 587,
ADD COLUMN IF NOT EXISTS email_user TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS email_password TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS email_from_name TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT FALSE;

-- Columnas para seguimiento de leads
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS lead_followup_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS lead_followup_hours INTEGER DEFAULT 24,
ADD COLUMN IF NOT EXISTS appointment_reminder_enabled BOOLEAN DEFAULT FALSE;

-- Tabla para tracking de leads
CREATE TABLE IF NOT EXISTS lead_tracking (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    status TEXT DEFAULT 'new',  -- new, contacted, qualified, cold, converted
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_sent TEXT,
    last_message_response TEXT,
    followup_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para lead_tracking
CREATE INDEX IF NOT EXISTS idx_lead_tracking_client ON lead_tracking(client_id);
CREATE INDEX IF NOT EXISTS idx_lead_tracking_phone ON lead_tracking(phone_number);
CREATE INDEX IF NOT EXISTS idx_lead_tracking_status ON lead_tracking(status);
CREATE INDEX IF NOT EXISTS idx_lead_tracking_last_interaction ON lead_tracking(last_interaction);

-- Tabla para citas/reservas
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    customer_name TEXT,
    appointment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, confirmed, cancelled, completed, no_show
    notes TEXT,
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para appointments
CREATE INDEX IF NOT EXISTS idx_appointments_client ON appointments(client_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- Tabla para plantillas de email
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    template_key TEXT NOT NULL,  -- followup_24h, appointment_reminder, etc.
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, template_key)
);

-- Insertar plantillas por defecto para todos los clientes existentes
INSERT INTO email_templates (client_id, template_key, subject, body)
SELECT 
    id,
    'followup_24h',
    '¡Hola! ¿Te quedaste con dudas?',
    'Hola {{nombre}},\n\nVimos que nos escribiste ayer pero no pudimos continuar la conversación.\n\n¿Te gustaría que te ayudemos con algo?\n\n{{nombre_negocio}}'
FROM clients
ON CONFLICT (client_id, template_key) DO NOTHING;

INSERT INTO email_templates (client_id, template_key, subject, body)
SELECT 
    id,
    'appointment_reminder',
    'Recordatorio de tu cita mañana',
    'Hola {{nombre}},\n\nTe recordamos que tienes una cita agendada para mañana a las {{hora}}.\n\n¿Confirmas tu asistencia?\n\n{{nombre_negocio}}'
FROM clients
ON CONFLICT (client_id, template_key) DO NOTHING;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✅ Configuración de email agregada exitosamente';
    RAISE NOTICE '✅ Tablas lead_tracking, appointments, email_templates creadas';
    RAISE NOTICE '✅ Plantillas de email insertadas';
END $$;
