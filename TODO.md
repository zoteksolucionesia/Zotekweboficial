# Tareas Pendientes Post-Lanzamiento (Zotek Soluciones IA SaaS)

*   [ ] **Revisión de Seguridad y Calidad de Código:** Integrar el repositorio con SonarQube (vía SonarCloud en GitHub Actions o SonarQube Local) para analizar deuda técnica, bugs latentes y vulnerabilidades (SAST).

# Gemini Live API 
Gemini Live API (usando el modelo 3.1-flash-live-preview). Esta es la "fruta prohibida" de los asistentes de voz en este momento por su capacidad de streaming bidireccional puro.

Aquí te explico por qué este modelo en particular es un cambio de juego para lo que estás haciendo en Zotek:

1. Olvida el ciclo "Pregunta -> Ruido -> Respuesta"
En lugar de que el servidor espere a que el usuario termine de hablar (Request) para luego procesar y responder (Response), este modelo usa WebSockets. Esto significa que el audio fluye constantemente en ambos sentidos. El asistente te puede interrumpir o reaccionar a un sonido de fondo al instante.

2. VAD Nativo (Detección de Actividad de Voz)
Tradicionalmente, tú como programador tenías que usar librerías externas para saber cuándo el usuario dejaba de hablar (silencio). Con el Live API, el modelo incluye su propio VAD. Él "siente" cuándo estás hablando y cuándo guardas silencio de forma mucho más natural, gestionando los turnos de palabra como lo haría un humano.

3. Multimodalidad "en vivo"
Este modelo puede procesar Audio, Video y Texto simultáneamente. Por ejemplo:

Podrías estar en una videollamada y el modelo "ve" que estás señalando un producto en la cámara mientras le haces una pregunta sobre su precio.
Puede emitir audio con emociones nativas (no es una voz robótica pegada después, sino que el modelo genera el tono y la entonación directamente desde el cerebro).
4. ¿Cómo lo conectas con tu proyecto actual?
Tú ya tienes una infraestructura con FastAPI y Database URL. Para integrar esto:

Usarías el SDK de google-genai (Python) que ya tienes o podrías instalar.
En lugar de un endpoint HTTP normal, abrirías un WebSocket hacia Google.
Esto es ideal para una integración con Vapi o directamente con un frontend web que use el micrófono del usuario.
# 2 abril 2026
Qué implicaría migrar a Railway:

Crear railway.toml con el comando de inicio (uvicorn src.main:app)
Conectar el repo de GitHub a Railway (deploy automático en cada push)
Configurar las variables de entorno en Railway (copiar el .env)
Actualizar la URL del webhook en Meta a la URL de Railway
Re-habilitar la verificación de firma WhatsApp (que está desactivada por el bug del ASGI bridge de Firebase)
Costo: ~$5/mes para el plan Hobby