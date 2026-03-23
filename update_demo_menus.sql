-- Script SQL para actualizar los menús de los bots demo
-- Ejecutar en PostgreSQL para que los clientes vean la configuración completa

-- ============================================
-- DEMO RESTAURANTE - GourmetBot 2026
-- ============================================
UPDATE clients 
SET menu_json = '{
  "text": "¡Hola! Bienvenido a *GourmetBot 2026* 🍕\n\nSoy el asistente virtual del restaurante *La Mesa Elegante*.\n\n¿Qué te gustaría hacer hoy?",
  "options": [
    {
      "icon": "📅",
      "title": "📅 Hacer Reserva",
      "response": "¡Excelente elección! 🎉\n\nPara reservar, necesito:\n• Fecha deseada\n• Número de personas\n• Hora preferida\n\n¿Me das esos datos?"
    },
    {
      "icon": "🍕",
      "title": "🍕 Ver Menú",
      "response": "¡Nuestro menú te va a encantar! 😋\n\n*Entradas:*\n• Bruschetta - $120\n• Calamares - $150\n\n*Pizzas:*\n• Pepperoni - $180\n• Margarita - $160\n• Hawaiana - $170\n\n*Pastas:*\n• Carbonara - $190\n• Boloñesa - $200\n\n¿Se te antojó algo?"
    },
    {
      "icon": "🚚",
      "title": "🚚 Pedido a Domicilio",
      "response": "¡Te lo llevamos caliente! 🛵\n\nPara tu pedido a domicilio necesito:\n• Tu dirección completa\n• Tu orden\n• Forma de pago\n\n¿Qué se te antoja hoy?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
}'::jsonb
WHERE phone_number_id = 'demo_restaurant';

-- ============================================
-- DEMO TIENDA - StyleBot 2026
-- ============================================
UPDATE clients 
SET menu_json = '{
  "text": "¡Hola! Bienvenido a *StyleBot 2026* 👗✨\n\nSoy tu *Personal Shopper* virtual de *Urban Vibe*.\n\n¿En qué puedo ayudarte hoy?",
  "options": [
    {
      "icon": "👗",
      "title": "👗 Buscar Prenda",
      "response": "¡Me encanta ayudarte a buscar! 💕\n\nPuedo ayudarte a encontrar:\n• Vestidos\n• Blusas\n• Pantalones\n• Accesorios\n\n¿Qué estás buscando? También puedes enviarme una foto de referencia."
    },
    {
      "icon": "📦",
      "title": "📦 Rastrear Pedido",
      "response": "¡Vamos a checar tu pedido! 🚚\n\nPara rastrearlo necesito:\n• Número de orden\n• O el email de tu compra\n\n¿Me lo compartes?"
    },
    {
      "icon": "📏",
      "title": "📏 Guía de Tallas",
      "response": "¡Para que te quede perfecto! ✨\n\n*Tallas disponibles:*\n• XS: Busto 80cm, Cintura 64cm\n• S: Busto 84cm, Cintura 68cm\n• M: Busto 88cm, Cintura 72cm\n• L: Busto 92cm, Cintura 76cm\n\n¿Qué talla usas normalmente?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
}'::jsonb
WHERE phone_number_id = 'demo_retail';

-- ============================================
-- DEMO DENTAL - SonrisaPerfecta IA
-- ============================================
UPDATE clients 
SET menu_json = '{
  "text": "¡Hola! Bienvenido a *SonrisaPerfecta IA* 🦷✨\n\nSoy el asistente virtual de la *Clínica Dental Sonrisa Perfecta*.\n\n¿Cómo puedo ayudarte hoy?",
  "options": [
    {
      "icon": "📅",
      "title": "📅 Agendar Cita",
      "response": "¡Qué gusto que cuidas tu sonrisa! 😁\n\nPara agendar necesito:\n• Tu nombre completo\n• Fecha preferida\n• Hora (matutino o vespertino)\n• ¿Es tu primera visita?\n\n¿Me compartes esos datos?"
    },
    {
      "icon": "🚨",
      "title": "🚨 Urgencia Dental",
      "response": "¡Entiendo que tienes dolor! 😰\n\nPara urgencias:\n• Llámanos al: 55-1234-5678\n• O ven a: Av. Dental #456\n\n*Horario urgencias:*\nLun-Vie: 9am-8pm\nSáb: 10am-3pm\n\n¿Necesitas que te ayude con algo más?"
    },
    {
      "icon": "💰",
      "title": "💰 Precios y Seguros",
      "response": "¡Transparentemos los costos! 💵\n\n*Servicios principales:*\n• Limpieza: $800\n• Blanqueamiento: $2,500\n• Ortodoncia: desde $15,000\n\n*Aceptamos:*\n• Seguros: GNP, MetLife, AXA\n• Meses sin intereses\n\n¿Te gustaría agendar una valoración?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
}'::jsonb
WHERE phone_number_id = 'demo_dental';

-- ============================================
-- DEMO PSICOLOGO - MenteSana Bot
-- ============================================
UPDATE clients 
SET menu_json = '{
  "text": "Hola, te comunicas con el consultorio del *Dr. Alejandro Ruiz* 🧠\n\nSoy su asistente virtual.\n\n¿Cómo puedo apoyarte hoy?",
  "options": [
    {
      "icon": "📅",
      "title": "📅 Agendar Sesión",
      "response": "Me da mucho gusto que des el primer paso 💚\n\nPara agendar necesito:\n• Tu nombre\n• Preferencia: ¿Online o presencial?\n• Día y hora preferida\n\n*Sesiones:*\n• Individual: $900 (50 min)\n• Pareja: $1,200 (60 min)\n\n¿Qué te gustaría agendar?"
    },
    {
      "icon": "🆘",
      "title": "🆘 Crisis Urgencia",
      "response": "Entiendo que estás pasando por un momento difícil 💚\n\n*Contacto de urgencias 24/7:*\n• Teléfono: 55-CRISIS\n• WhatsApp: 55-1234-5678\n\n*Recuerda:*\nNo estás solo/a. Pedir ayuda es de valientes.\n\n¿Hay algo más en lo que pueda apoyarte?"
    },
    {
      "icon": "ℹ️",
      "title": "ℹ️ Info Terapia",
      "response": "¡Con gusto te informo! 💚\n\n*Especialidades del Dr. Ruiz:*\n• Ansiedad y estrés\n• Depresión\n• Terapia de pareja\n• Autoestima\n\n*Enfoque:*\nTerapia Cognitivo-Conductual\n\n*Primera sesión:*\nIncluye evaluación completa\n\n¿Te gustaría agendar una valoración?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
}'::jsonb
WHERE phone_number_id = 'demo_psychology';

-- ============================================
-- DEMO SALON - GlamourBot 2026
-- ============================================
UPDATE clients 
SET menu_json = '{
  "text": "¡Hola! Bienvenid@ a *GlamourBot 2026* 💇‍♀️✨\n\nSoy el asistente virtual de *Estilo y Glamour Salón*.\n\n¿Qué te gustaría hacer hoy?",
  "options": [
    {
      "icon": "💇‍♀️",
      "title": "💇‍♀️ Agendar Cita",
      "response": "¡Te vamos a consentir! 💅\n\nPara tu cita necesito:\n• Servicio deseado\n• Fecha y hora preferida\n• ¿Con qué estilista?\n\n*Nuestros servicios:*\n• Corte: desde $350\n• Color: desde $800\n• Manicure: $250\n\n¿Qué servicio te gustaría?"
    },
    {
      "icon": "💰",
      "title": "💰 Consultar Precios",
      "response": "¡Con gusto te informo! 💕\n\n*Servicios de Cabello:*\n• Corte: $350-$600\n• Tinte: $800-$1,500\n• Mechas: $1,200-$2,500\n\n*Servicios de Uñas:*\n• Manicure: $250\n• Pedicure: $350\n• Gel: $450\n\n*Promociones:*\n¡Martes de 2x1 en manicure!\n\n¿Te gustaría agendar?"
    },
    {
      "icon": "❌",
      "title": "❌ Cancelar Cita",
      "response": "Entiendo, a veces surgen imprevistos 😊\n\nPara cancelar necesito:\n• Tu nombre\n• Fecha de la cita\n\n*Política de cancelación:*\n• Cancela con 24hrs de anticipación\n• Sin show: 50% de recargo\n\n¿Me compartes tus datos para buscar tu cita?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
}'::jsonb
WHERE phone_number_id = 'demo_salon';

-- Verificar actualización
SELECT phone_number_id, 
       menu_json->>'text' as welcome_text,
       jsonb_array_length(menu_json->'options') as options_count
FROM clients 
WHERE phone_number_id LIKE 'demo%'
ORDER BY phone_number_id;
