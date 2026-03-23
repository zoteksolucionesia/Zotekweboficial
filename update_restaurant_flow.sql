-- Actualizar el menú del demo restaurante con flujo de reserva interactivo
-- Esto muestra cómo los clientes pueden tener flujos conversacionales

UPDATE clients 
SET menu_json = '{
  "text": "¡Hola! Bienvenido a *GourmetBot 2026* 🍕\n\nSoy el asistente virtual del restaurante *La Mesa Elegante*.\n\n¿Qué te gustaría hacer hoy?",
  "options": [
    {
      "icon": "📅",
      "title": "📅 Hacer Reserva",
      "response": "¡Excelente elección! 🎉\n\n*Vamos a agendar tu reserva*\n\nPrimero, ¿para qué fecha te gustaría reservar?\n\n*Opciones:*\n• Hoy\n• Mañana\n• Este fin de semana\n• Otra fecha (escribe la fecha)\n\n¿Cuál prefieres?"
    },
    {
      "icon": "🍕",
      "title": "🍕 Ver Menú",
      "response": "¡Nuestro menú te va a encantar! 😋\n\n*🥗 ENTRADAS*\n• Bruschetta - $120\n• Calamares - $150\n• Ensalada César - $140\n\n*🍕 PIZZAS*\n• Pepperoni - $180\n• Margarita - $160\n• Hawaiana - $170\n• La Casa - $220\n\n*🍝 PASTAS*\n• Carbonara - $190\n• Boloñesa - $200\n• Alfredo - $210\n\n*🍰 POSTRES*\n• Tiramisú - $90\n• Panna Cotta - $80\n\n¿Qué se te antojó?"
    },
    {
      "icon": "🚚",
      "title": "🚚 Pedido a Domicilio",
      "response": "¡Te lo llevamos caliente! 🛵\n\n*Zonas de reparto:*\n• Centro - $30\n• Norte - $50\n• Sur - $45\n\n*Tiempo estimado:*\n30-45 minutos\n\nPara tu pedido necesito:\n• Tu dirección completa\n• Tu orden\n• Forma de pago\n\n¿Qué se te antoja hoy?"
    }
  ],
  "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:",
  "reservation_flow": {
    "enabled": true,
    "steps": [
      {
        "step": 1,
        "question": "¿Para qué fecha te gustaría reservar?",
        "type": "buttons",
        "options": ["Hoy", "Mañana", "Otra fecha"]
      },
      {
        "step": 2,
        "question": "¿Para cuántas personas es la reserva?",
        "type": "buttons", 
        "options": ["1-2 personas", "3-4 personas", "5+ personas"]
      },
      {
        "step": 3,
        "question": "¿Qué horario prefieres?",
        "type": "buttons",
        "options": ["Comida (1-5pm)", "Cena (6-10pm)"]
      },
      {
        "step": 4,
        "question": "Perfecto! ¿Me das tu nombre para la reserva?",
        "type": "text"
      }
    ],
    "confirmation": "¡Reserva confirmada! ✅\n\n*Detalles:*\n📅 Fecha: {fecha}\n👥 Personas: {personas}\n⏰ Horario: {horario}\n👤 Nombre: {nombre}\n\n*Te esperamos en La Mesa Elegante!*\n\n📍 Av. Principal #123, Centro\n📞 Tel: 55-1234-5678"
  }
}'::jsonb
WHERE phone_number_id = 'demo_restaurant';

-- Verificar actualización
SELECT phone_number_id, 
       menu_json->>'text' as welcome_text,
       jsonb_array_length(menu_json->'options') as options_count,
       menu_json->'reservation_flow'->>'enabled' as has_reservation_flow
FROM clients 
WHERE phone_number_id = 'demo_restaurant';
