# Guía de Testing - Deploy en Firebase

**Deploy Status:** ✅ Completado  
**URL:** `https://zotek-ia.cloudfunctions.net/api_handler`  
**Fecha:** 2026-04-04  

---

## 1. Test: Crear una cita con teléfono sin normalizar

Crea una cita con Lili con número en formato local (sin código de país):

```bash
curl -X POST https://zotek-ia.cloudfunctions.net/api_handler/api/clients/1/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [JWT_TOKEN]" \
  -d '{
    "paciente_nombre": "Test User",
    "cliente_telefono": "3121149153",
    "fecha_hora": "2026-04-05 10:00",
    "motivo": "Test de normalización"
  }'
```

**Verificar:**
- La cita se crea correctamente
- En la BD, `cliente_telefono` está guardado como `+523121149153` (normalizado)

---

## 2. Test: Webhook de VAPI

Simula un webhook de VAPI con costo:

```bash
curl -X POST https://zotek-ia.cloudfunctions.net/api_handler/api/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "x-vapi-secret: [tu VAPI_WEBHOOK_SECRET]" \
  -d '{
    "id": "call_test_12345",
    "status": "ended",
    "cost": 0.15,
    "duration": 45,
    "endedReason": "userHungUp"
  }'
```

**Verificar:**
- Webhook responde con `{"status": "received"}`
- En tabla `consumo_eventos`, aparece nuevo registro:
  - `proveedor`: "VAPI"
  - `tipo`: "CALL"
  - `costo_usd`: 0.15
  - `duracion_segundos`: 45

---

## 3. Test: Dashboard de costos

**Obtén token JWT primero:**
```bash
curl -X POST https://zotek-ia.cloudfunctions.net/api_handler/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tu@email.com",
    "password": "tu_password"
  }'
# Respuesta: {"access_token": "eyJ...", "token_type": "bearer"}
```

**Consulta el dashboard:**
```bash
curl -X GET "https://zotek-ia.cloudfunctions.net/api_handler/api/admin/consumo?mes=4&anio=2026" \
  -H "Authorization: Bearer [JWT_TOKEN]"
```

**Respuesta esperada:**
```json
{
  "periodo": "2026-04",
  "total_gastado_usd": 0.15,
  "por_proveedor": {
    "VAPI": 0.15
  },
  "facturacion_clientes": [],
  "total_eventos": 1
}
```

---

## 4. Test: Configurar tarifas de cliente

Para que el dashboard muestre margen, agrégale tarifas a Lili:

```sql
INSERT INTO tarifas_cliente 
(client_id, fee_mensual_mxn, precio_por_llamada_mxn, activo)
VALUES (1, 1500, 5.00, TRUE);
```

Después, el dashboard mostrará:
```json
"facturacion_clientes": [
  {
    "id": 1,
    "nombre_cliente": "Lili",
    "costo_real_usd": 0.15,           ← lo que le cuesta VAPI
    "fee_mensual_mxn": 1500,
    "precio_llamada_mxn": 5.00,
    "total_eventos": 1
  }
]
```

---

## 5. Test End-to-End: Llamada de recordatorio

1. Crea una cita para mañana con teléfono local:
```bash
POST /api/clients/1/appointments
{
  "paciente_nombre": "Juan Pérez",
  "cliente_telefono": "5551234567",   ← sin +52
  "fecha_hora": "2026-04-05 14:00",
  "motivo": "Cita de prueba"
}
```

2. Mañana a las 10 AM, el cron ejecuta `/api/cron/reminders`:
   - Busca citas de mañana
   - Normaliza: `5551234567` → `+525551234567`
   - Envía WhatsApp al número normalizado

3. O manualmente con `/api/reminders/run`:
```bash
POST /api/reminders/run
Authorization: Bearer [JWT_TOKEN]
```

4. Verifica logs:
   - "Cita actualizada a 'llamado' para call_id=..."
   - "Consumo registrado: client=1, proveedor=VAPI, costo=$..."

5. Consulta dashboard:
```bash
GET /api/admin/consumo?client_id=1
```
   - `total_gastado_usd` y `facturacion_clientes` se actualizan automáticamente

---

## 🔍 Verificación rápida de BD

```sql
-- Ver eventos registrados
SELECT * FROM consumo_eventos ORDER BY timestamp DESC LIMIT 5;

-- Ver tarifas de cliente
SELECT * FROM tarifas_cliente WHERE client_id = 1;

-- Ver consumo total del mes (abril 2026)
SELECT 
  proveedor,
  COUNT(*) as cantidad,
  SUM(costo_usd) as total
FROM consumo_eventos
WHERE EXTRACT(MONTH FROM timestamp) = 4
GROUP BY proveedor;
```

---

## 📝 Checklist de Testing

- [ ] Crear cita con teléfono local (3121149153) → verifica normalización en BD
- [ ] Simular webhook VAPI con costo → verifica registro en consumo_eventos
- [ ] Consultar dashboard sin datos → responde con estructura correcta
- [ ] Agregar tarifas a cliente → dashboard muestra margen
- [ ] Test end-to-end: cita → webhook → dashboard actualizado
- [ ] Verificar que normalización ocurre en 3 lugares (save, cron, reminders/run)

---

## 🚨 Troubleshooting

**"NameError: name 'Optional' is not defined"**
→ ✅ Arreglado: agregado `Optional` a imports en ambos main.py

**Dashboard devuelve error 401**
→ Token JWT expirado o incorrecto. Obtén uno nuevo con `/api/auth/login`

**Webhook no registra costo**
→ Verifica que VAPI está enviando `cost` en el payload (algunos eventos no tienen costo)

**Teléfonos no se normalizan**
→ Verifica que `save_appointment()` se está llamando (no que se está escribiendo directamente en BD)
