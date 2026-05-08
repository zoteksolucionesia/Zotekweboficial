"""
Automations package for Zotek IA
Scheduled tasks for lead follow-ups and appointment reminders
"""

from .followup_leads import followup_cold_leads
from .appointment_reminders import appointment_reminders

__all__ = [
    'followup_cold_leads',
    'appointment_reminders'
]
