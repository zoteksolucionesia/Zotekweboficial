"""
Configuración centralizada de Zotek Soluciones IA SaaS.

Este módulo centraliza toda la configuración de la aplicación,
incluyendo variables de entorno, constantes de negocio y límites del sistema.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración general de la aplicación."""
    
    # ============================================
    # API KEYS Y SECRETOS
    # ============================================
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    SECRET_KEY = os.getenv("SECRET_KEY", "ZOTEK_SECRET_DEFAULT_CHANGE_ME")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "zoteksolucionesia@gmail.com")
    EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
    
    # WhatsApp
    WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")  # Para verificar firma de webhooks
    
    # ============================================
    # CONFIGURACIÓN DE GEMINI
    # ============================================
    GEMINI_MODEL_ID = "gemini-2.0-flash"
    GEMINI_TEMPERATURE = 0.5
    GEMINI_MAX_RETRIES = 3
    GEMINI_RETRY_DELAY_SECONDS = 2
    
    # ============================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ============================================
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    ORIGINAL_DB = os.path.join(DATA_DIR, "consultorio.db")
    
    # Firebase/Production
    IS_PRODUCTION = bool(os.environ.get('K_SERVICE') or os.environ.get('FIREBASE_CONFIG'))
    TEMP_DB = "/tmp/consultorio.db"  # Para Firebase Functions
    
    # ============================================
    # IDs DE DEMO (Hardcodeados para demos siempre disponibles)
    # ============================================
    DEMO_RESTAURANTE_ID = 9991
    DEMO_CLINICA_ID = 9992
    DEMO_TIENDA_ID = 9993
    
    # ============================================
    # PLANES Y LÍMITES DE USO
    # ============================================
    CLIENT_PLANS: Dict[str, Dict[str, Any]] = {
        'free': {
            'monthly_messages': 100,
            'knowledge_base_mb': 5,
            'price_usd': 0
        },
        'basic': {
            'monthly_messages': 1000,
            'knowledge_base_mb': 20,
            'price_usd': 29
        },
        'pro': {
            'monthly_messages': 10000,
            'knowledge_base_mb': 100,
            'price_usd': 79
        },
        'enterprise': {
            'monthly_messages': -1,  # -1 = ilimitado
            'knowledge_base_mb': 500,
            'price_usd': 199
        },
    }
    
    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_MESSAGES_PER_MINUTE = 100  # Máximo de mensajes por minuto por IP
    RATE_LIMIT_API_PER_HOUR = 1000  # Máximo de requests API por hora por usuario
    
    # ============================================
    # CACHE
    # ============================================
    KNOWLEDGE_CACHE_TTL_SECONDS = 300  # 5 minutos
    CONVERSATION_HISTORY_LIMIT = 10  # Últimos mensajes a mantener en contexto
    
    # ============================================
    # LOGGING Y PRIVACIDAD
    # ============================================
    LOG_PHONE_NUMBER_VISIBLE_DIGITS = 4  # Dígitos visibles en logs
    LOG_MESSAGE_PREVIEW_LENGTH = 50  # Longitud de preview de mensajes en logs
    
    # ============================================
    # WEBHOOK
    # ============================================
    WEBHOOK_VERIFY_TOKEN_PARAM = "hub.verify_token"
    WEBHOOK_CHALLENGE_PARAM = "hub.challenge"
    WEBHOOK_MODE_PARAM = "hub.mode"
    
    # ============================================
    # FIREBASE FUNCTIONS
    # ============================================
    FUNCTIONS_TIMEOUT_SEC = 120
    FUNCTIONS_MEMORY_MB = 1024
    
    # ============================================
    # MÉTRICAS Y MONITOREO
    # ============================================
    METRICS_WINDOW_SECONDS = 3600  # Ventana de métricas (1 hora)
    
    # ============================================
    # URLs Y RUTAS
    # ============================================
    WHATSAPP_API_VERSION = "v22.0"
    WHATSAPP_API_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"
    
    # ============================================
    # SEGURIDAD
    # ============================================
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = 8
    JWT_TOKEN_TYPE = "bearer"
    
    # ============================================
    # EMAIL (SMTP)
    # ============================================
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USE_TLS = True
    
    # ============================================
    # DIRECTORIOS
    # ============================================
    WWW_DIR = os.path.join(BASE_DIR, "www")
    ADMIN_DIR = os.path.join(WWW_DIR, "admin")
    
    # ============================================
    # MÉTODOS DE UTILIDAD
    # ============================================
    
    @classmethod
    def get_db_path(cls) -> str:
        """Obtiene la ruta de la base de datos según el entorno."""
        if cls.IS_PRODUCTION:
            import shutil
            import os as _os
            
            # Copiar DB a tmp si no existe
            if not _os.path.exists(cls.TEMP_DB):
                try:
                    shutil.copy2(cls.ORIGINAL_DB, cls.TEMP_DB)
                    _os.chmod(cls.TEMP_DB, 0o666)
                except Exception as e:
                    print(f"⚠️ Error copying DB to /tmp: {e}")
            return cls.TEMP_DB
        return cls.ORIGINAL_DB
    
    @classmethod
    def get_plan_limits(cls, plan: str) -> Dict[str, Any]:
        """Obtiene los límites de un plan específico."""
        return cls.CLIENT_PLANS.get(plan, cls.CLIENT_PLANS['free'])
    
    @classmethod
    def is_unlimited_plan(cls, plan: str) -> bool:
        """Verifica si un plan tiene mensajes ilimitados."""
        limits = cls.get_plan_limits(plan)
        return limits.get('monthly_messages', 0) == -1
    
    @classmethod
    def get_demo_client_ids(cls) -> list:
        """Retorna la lista de IDs de clientes demo."""
        return [cls.DEMO_RESTAURANTE_ID, cls.DEMO_CLINICA_ID, cls.DEMO_TIENDA_ID]
    
    @classmethod
    def is_demo_client(cls, client_id: int) -> bool:
        """Verifica si un ID corresponde a un cliente demo."""
        return client_id in cls.get_demo_client_ids()


# Instancia global para acceso rápido
config = Config()
