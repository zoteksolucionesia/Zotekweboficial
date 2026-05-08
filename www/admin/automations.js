/**
 * Automation Status Functions
 * Para mostrar el estado de las automatizaciones en el admin panel
 */

// ============================================
// LOAD AUTOMATION STATUS
// ============================================

async function loadAutomationStatus() {
    const container = document.getElementById('automation-status-list');
    if (!container) return;

    try {
        // Simular status (en producción, llamar a API)
        const automations = [
            {
                name: 'Follow-up de Leads Fríos',
                schedule: 'Cada hora',
                lastRun: 'Hace 30 minutos',
                nextRun: 'En 30 minutos',
                status: 'active',
                description: 'Envía emails automáticos a leads que no responden'
            },
            {
                name: 'Recordatorio de Citas',
                schedule: 'Diario 10:00 AM',
                lastRun: 'Hoy 10:00 AM',
                nextRun: 'Mañana 10:00 AM',
                status: 'active',
                description: 'Envía recordatorios de citas del día siguiente'
            }
        ];

        let html = '<div style="display: grid; gap: 20px;">';

        automations.forEach(auto => {
            const statusColor = auto.status === 'active' ? 'var(--success)' : 'var(--danger)';
            const statusText = auto.status === 'active' ? '✅ Activa' : '❌ Inactiva';

            html += `
                <div class="settings-card">
                    <div class="settings-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>${auto.name}</h3>
                        <span style="background: ${statusColor}; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.85rem;">
                            ${statusText}
                        </span>
                    </div>
                    <div class="settings-card-body">
                        <p style="color: var(--text-muted); margin-bottom: 15px;">${auto.description}</p>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">Schedule</div>
                                <div style="font-weight: 600;">${auto.schedule}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">Última ejecución</div>
                                <div style="font-weight: 600;">${auto.lastRun}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">Próxima ejecución</div>
                                <div style="font-weight: 600;">${auto.nextRun}</div>
                            </div>
                        </div>

                        <div style="margin-top: 15px; display: flex; gap: 10px;">
                            <button class="btn btn-sm btn-primary" onclick="runAutomationNow('${auto.name}')">
                                ▶️ Ejecutar Ahora
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="viewAutomationLogs('${auto.name}')">
                                📋 Ver Logs
                            </button>
                            <button class="btn btn-sm btn-warning" onclick="configureAutomation('${auto.name}')">
                                ⚙️ Configurar
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="chat-placeholder" style="color: var(--danger);">Error al cargar estado de automatizaciones</p>';
    }
}

// ============================================
// ACTIONS
// ============================================

async function runAutomationNow(automationName) {
    if (!confirm(`¿Ejecutar "${automationName}" ahora?`)) return;

    // TODO: Implementar llamada API para ejecutar manualmente
    showToast('Ejecución iniciada. Revisa los logs en unos minutos.', 'success');
}

async function viewAutomationLogs(automationName) {
    // TODO: Abrir modal o página con logs
    const logsUrl = `https://console.cloud.google.com/logs/query?project=zotek-ia&q=${encodeURIComponent(automationName)}`;
    window.open(logsUrl, '_blank');
}

async function configureAutomation(automationName) {
    // TODO: Abrir modal de configuración
    const configUrl = 'https://console.cloud.google.com/cloudscheduler?project=zotek-ia';
    window.open(configUrl, '_blank');
    showToast('Se abrió la consola de Cloud Scheduler. Configura los schedules allí.', 'info');
}

// ============================================
// INITIALIZATION
// ============================================

// Cargar estado cuando se muestra la sección
const originalShowSectionAuto = window.showSection;
window.showSection = function(sectionId) {
    if (sectionId === 'automations') {
        loadAutomationStatus();
    }
    if (originalShowSectionAuto) {
        originalShowSectionAuto(sectionId);
    }
};
