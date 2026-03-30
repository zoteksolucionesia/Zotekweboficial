#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar los menús de los bots demo con opciones interactivas
"""

import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Configuración de menús para cada demo
demo_menus = {
    "demo_restaurant": {
        "text": "¡Hola! Bienvenido a *GourmetBot 2026* 🍕\n\nSoy el asistente virtual del restaurante *La Mesa Elegante*. Estoy aquí para hacer tu experiencia increíble.\n\n¿Qué te gustaría hacer hoy?",
        "options": [
            {"title": "📅 Hacer Reserva", "icon": "📅", "response": "¡Excelente elección! 🎉\n\nPara reservar, necesito:\n• Fecha deseada\n• Número de personas\n• Hora preferida\n\n¿Me das esos datos?"},
            {"title": "🍕 Ver Menú", "icon": "🍕", "response": "¡Nuestro menú te va a encantar! 😋\n\n*Entradas:*\n• Bruschetta - $120\n• Calamares - $150\n\n*Pizzas:*\n• Pepperoni - $180\n• Margarita - $160\n• Hawaiana - $170\n\n*Pastas:*\n• Carbonara - $190\n• Boloñesa - $200\n\n¿Se te antojó algo?"},
            {"title": "🚚 Pedido a Domicilio", "icon": "🚚", "response": "¡Te lo llevamos caliente! 🛵\n\nPara tu pedido a domicilio necesito:\n• Tu dirección completa\n• Tu orden\n• Forma de pago\n\n¿Qué se te antoja hoy?"}
        ],
        "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
    },
    "demo_retail": {
        "text": "¡Hola! Bienvenido a *StyleBot 2026* 👗✨\n\nSoy tu *Personal Shopper* virtual de *Urban Vibe*. Estoy aquí para ayudarte a encontrar tu estilo perfecto.\n\n¿En qué puedo ayudarte hoy?",
        "options": [
            {"title": "👗 Buscar Prenda", "icon": "👗", "response": "¡Me encanta ayudarte a buscar! 💕\n\nPuedo ayudarte a encontrar:\n• Vestidos\n• Blusas\n• Pantalones\n• Accesorios\n\n¿Qué estás buscando? También puedes enviarme una foto de referencia."},
            {"title": "📦 Rastrear Pedido", "icon": "📦", "response": "¡Vamos a checar tu pedido! 🚚\n\nPara rastrearlo necesito:\n• Número de orden\n• O el email de tu compra\n\n¿Me lo compartes?"},
            {"title": "📏 Guía de Tallas", "icon": "📏", "response": "¡Para que te quede perfecto! ✨\n\n*Tallas disponibles:*\n• XS: Busto 80cm, Cintura 64cm\n• S: Busto 84cm, Cintura 68cm\n• M: Busto 88cm, Cintura 72cm\n• L: Busto 92cm, Cintura 76cm\n\n¿Qué talla usas normalmente?"}
        ],
        "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
    },
    "demo_dental": {
        "text": "¡Hola! Bienvenido a *SonrisaPerfecta IA* 🦷✨\n\nSoy el asistente virtual de la *Clínica Dental Sonrisa Perfecta*. Cuidar tu sonrisa es mi prioridad.\n\n¿Cómo puedo ayudarte hoy?",
        "options": [
            {"title": "📅 Agendar Cita", "icon": "📅", "response": "¡Qué gusto que cuidas tu sonrisa! 😁\n\nPara agendar necesito:\n• Tu nombre completo\n• Fecha preferida\n• Hora (matutino o vespertino)\n• ¿Es tu primera visita?\n\n¿Me compartes esos datos?"},
            {"title": "🚨 Urgencia Dental", "icon": "🚨", "response": "¡Entiendo que tienes dolor! 😰\n\nPara urgencias:\n• Llámanos al: 55-1234-5678\n• O ven a: Av. Dental #456\n\n*Horario urgencias:*\nLun-Vie: 9am-8pm\nSáb: 10am-3pm\n\n¿Necesitas que te ayude con algo más?"},
            {"title": "💰 Precios y Seguros", "icon": "💰", "response": "¡Transparentemos los costos! 💵\n\n*Servicios principales:*\n• Limpieza: $800\n• Blanqueamiento: $2,500\n• Ortodoncia: desde $15,000\n\n*Aceptamos:*\n• Seguros: GNP, MetLife, AXA\n• Meses sin intereses\n\n¿Te gustaría agendar una valoración?"}
        ],
        "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
    },
    "demo_psychology": {
        "text": "Hola, te comunicas con el consultorio del *Dr. Alejandro Ruiz* 🧠\n\nSoy su asistente virtual. El Dr. Ruiz es psicólogo clínico con 15 años de experiencia.\n\n¿Cómo puedo apoyarte hoy?",
        "options": [
            {"title": "📅 Agendar Sesión", "icon": "📅", "response": "Me da mucho gusto que des el primer paso 💚\n\nPara agendar necesito:\n• Tu nombre\n• Preferencia: ¿Online o presencial?\n• Día y hora preferida\n\n*Sesiones:*\n• Individual: $900 (50 min)\n• Pareja: $1,200 (60 min)\n\n¿Qué te gustaría agendar?"},
            {"title": "🆘 Crisis Urgencia", "icon": "🆘", "response": "Entiendo que estás pasando por un momento difícil 💚\n\n*Contacto de urgencias 24/7:*\n• Teléfono: 55-CRISIS\n• WhatsApp: 55-1234-5678\n\n*Recuerda:*\nNo estás solo/a. Pedir ayuda es de valientes.\n\n¿Hay algo más en lo que pueda apoyarte?"},
            {"title": "ℹ Info Terapia", "icon": "ℹ", "response": "¡Con gusto te informo! 💚\n\n*Especialidades del Dr. Ruiz:*\n• Ansiedad y estrés\n• Depresión\n• Terapia de pareja\n• Autoestima\n\n*Enfoque:*\nTerapia Cognitivo-Conductual\n\n*Primera sesión:*\nIncluye evaluación completa\n\n¿Te gustaría agendar una valoración?"}
        ],
        "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
    },
    "demo_salon": {
        "text": "¡Hola! Bienvenid@ a *GlamourBot 2026* 💇‍♀✨\n\nSoy el asistente virtual de *Estilo y Glamour Salón*. Tu belleza es nuestra pasión.\n\n¿Qué te gustaría hacer hoy?",
        "options": [
            {"title": "💇‍♀ Agendar Cita", "icon": "💇‍♀", "response": "¡Te vamos a consentir! 💅\n\nPara tu cita necesito:\n• Servicio deseado\n• Fecha y hora preferida\n• ¿Con qué estilista?\n\n*Nuestros servicios:*\n• Corte: desde $350\n• Color: desde $800\n• Manicure: $250\n\n¿Qué servicio te gustaría?"},
            {"title": "💰 Consultar Precios", "icon": "💰", "response": "¡Con gusto te informo! 💕\n\n*Servicios de Cabello:*\n• Corte: $350-$600\n• Tinte: $800-$1,500\n• Mechas: $1,200-$2,500\n\n*Servicios de Uñas:*\n• Manicure: $250\n• Pedicure: $350\n• Gel: $450\n\n*Promociones:*\n¡Martes de 2x1 en manicure!\n\n¿Te gustaría agendar?"},
            {"title": " Cancelar Cita", "icon": "", "response": "Entiendo, a veces surgen imprevistos 😊\n\nPara cancelar necesito:\n• Tu nombre\n• Fecha de la cita\n\n*Política de cancelación:*\n• Cancela con 24hrs de anticipación\n• Sin show: 50% de recargo\n\n¿Me compartes tus datos para buscar tu cita?"}
        ],
        "fallback_text": "No entendí tu solicitud. Por favor selecciona una de las opciones:"
    }
}

print("="*60)
print("ACTUALIZANDO MENÚS DE DEMOS")
print("="*60)

for phone_id, menu_data in demo_menus.items():
    print(f"\nActualizando {phone_id}...")
    
    try:
        cur.execute("""
            UPDATE clients 
            SET menu_json = %s 
            WHERE phone_number_id = %s
        """, (json.dumps(menu_data, ensure_ascii=False), phone_id))
        
        if cur.rowcount > 0:
            print(f"   Actualizado correctamente")
        else:
            print(f"   No se encontró el bot con phone_number_id: {phone_id}")
            
    except Exception as e:
        print(f"   Error: {e}")

conn.commit()
print("\n" + "="*60)
print("ACTUALIZACIÓN COMPLETADA")
print("="*60)

cur.close()
conn.close()
