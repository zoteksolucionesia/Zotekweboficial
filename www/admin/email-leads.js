/**
 * Email & Leads Management Functions
 * Para la sección "Email & Leads" del admin panel
 */

// NOTA: 'token' ya está declarado en zotek_v9.js, no redeclarar
// const token = localStorage.getItem('zotek_token');

// ============================================
// CLIENT LOADERS
// ============================================

async function loadClientsForSelectors() {
    // Carga clientes para todos los selectores de la sección
    try {
        const res = await fetch('/api/clients', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const clients = await res.json();

        const selectors = [
            'email-client-selector',
            'leads-client-selector',
            'appointments-client-selector'
        ];

        selectors.forEach(selectorId => {
            const selector = document.getElementById(selectorId);
            if (selector) {
                selector.innerHTML = '<option value="">Selecciona un cliente...</option>';
                clients.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.id;
                    option.textContent = `${client.name} (${client.phone_number_id})`;
                    selector.appendChild(option);
                });
            }
        });
    } catch (e) {
        console.error('Error loading clients:', e);
        showToast('Error al cargar clientes: ' + e.message, 'error');
    }
}

// ============================================
// EMAIL CONFIGURATION
// ============================================

async function loadEmailConfig() {
    const clientId = document.getElementById('email-client-selector').value;
    const form = document.getElementById('email-config-form');

    if (!clientId) {
        form.style.display = 'none';
        return;
    }

    try {
        const res = await fetch(`/api/clients/${clientId}/email-config`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const config = await res.json();

        document.getElementById('smtp-server').value = config.email_smtp_server || 'smtp.gmail.com';
        document.getElementById('smtp-port').value = config.email_smtp_port || 587;
        document.getElementById('email-user').value = config.email_user || '';
        document.getElementById('email-from-name').value = config.email_from_name || '';
        document.getElementById('email-notifications-enabled').checked = config.email_notifications_enabled || false;

        form.style.display = 'block';

        if (config.configured) {
            showToast('Configuración de email cargada', 'info');
        } else {
            showToast('Configura tu email para enviar notificaciones', 'warning');
        }
    } catch (e) {
        console.error(e);
        showToast('Error al cargar configuración', 'error');
    }
}

async function saveEmailConfig() {
    const clientId = document.getElementById('email-client-selector').value;

    if (!clientId) {
        showToast('Selecciona un cliente', 'warning');
        return;
    }

    const config = {
        smtp_server: document.getElementById('smtp-server').value,
        smtp_port: parseInt(document.getElementById('smtp-port').value),
        email_user: document.getElementById('email-user').value,
        email_password: document.getElementById('email-password').value,
        email_from_name: document.getElementById('email-from-name').value,
        notifications_enabled: document.getElementById('email-notifications-enabled').checked
    };

    if (!config.email_user || !config.email_password) {
        showToast('Email y contraseña son requeridos', 'warning');
        return;
    }

    try {
        const res = await fetch(`/api/clients/${clientId}/email-config`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const data = await res.json();

        if (data.status === 'updated') {
            showToast('Configuración guardada exitosamente', 'success');
        } else {
            showToast('Error: ' + (data.detail || 'Error desconocido'), 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error al guardar: ' + e.message, 'error');
    }
}

async function testEmailConfig() {
    const clientId = document.getElementById('email-client-selector').value;

    if (!clientId) {
        showToast('Selecciona un cliente', 'warning');
        return;
    }

    const testEmail = prompt('Ingresa el email donde recibirás la prueba:');
    if (!testEmail) return;

    try {
        const res = await fetch(`/api/clients/${clientId}/email-test`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: testEmail })
        });

        const data = await res.json();

        const resultDiv = document.getElementById('email-test-result');
        if (data.status === 'success') {
            resultDiv.innerHTML = `<p style="color: var(--success);">✅ ${data.message}</p>`;
            showToast('Email de prueba enviado', 'success');
        } else {
            resultDiv.innerHTML = `<p style="color: var(--danger);">❌ ${data.detail || 'Error'}</p>`;
            showToast('Error al enviar: ' + (data.detail || 'Error desconocido'), 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error: ' + e.message, 'error');
    }
}

// ============================================
// COLD LEADS
// ============================================

async function loadColdLeads() {
    const clientId = document.getElementById('leads-client-selector').value;
    const hours = document.getElementById('leads-hours').value;
    const container = document.getElementById('cold-leads-list');

    if (!clientId) {
        container.innerHTML = '<p class="chat-placeholder">Selecciona un cliente para ver leads fríos</p>';
        return;
    }

    try {
        const res = await fetch(`/api/clients/${clientId}/leads/cold?hours=${hours}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.leads || data.leads.length === 0) {
            container.innerHTML = '<p class="chat-placeholder">No hay leads fríos en este período</p>';
            return;
        }

        let html = `<p style="margin-bottom: 15px; color: var(--text-muted);">${data.total} leads fríos encontrados</p>`;
        html += '<div style="display: grid; gap: 10px;">';

        data.leads.forEach(lead => {
            const lastInteraction = lead.last_interaction ? new Date(lead.last_interaction).toLocaleString() : 'Desconocido';
            const statusBadge = getStatusBadge(lead.status);

            html += `
                <div class="chat-card" style="padding: 15px; border-left: 3px solid var(--warning);">
                    <div class="chat-card-header" style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="font-weight: 600;">📱 ${escapeHtml(lead.phone_number)}</span>
                        ${statusBadge}
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-muted);">
                        <p>Última interacción: ${lastInteraction}</p>
                        <p>Follow-ups: ${lead.followup_count || 0}</p>
                        ${lead.last_message_sent ? `<p>Último mensaje: ${escapeHtml(lead.last_message_sent.substring(0, 100))}...</p>` : ''}
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                        <button class="btn btn-sm btn-primary" onclick="sendFollowup(${lead.id}, '${escapeHtml(lead.phone_number)}')">
                            📤 Enviar Follow-up
                        </button>
                        <button class="btn btn-sm btn-success" onclick="markLeadConverted(${lead.id})">
                            ✅ Marcar como Convertido
                        </button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="chat-placeholder" style="color: var(--danger);">Error al cargar leads</p>';
    }
}

function getStatusBadge(status) {
    const colors = {
        'new': 'var(--info)',
        'contacted': 'var(--warning)',
        'qualified': 'var(--success)',
        'cold': 'var(--danger)',
        'converted': 'var(--success)'
    };
    const color = colors[status] || 'var(--text-muted)';
    return `<span style="background: ${color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem;">${status.toUpperCase()}</span>`;
}

async function sendFollowup(leadId, phone) {
    const message = prompt(`Mensaje para ${phone}:`, '¡Hola! ¿Pudiste ver la información que te enviamos? Estamos aquí para ayudarte.');
    if (!message) return;

    // TODO: Implementar envío real
    showToast('Follow-up enviado (simulado)', 'success');
}

async function markLeadConverted(leadId) {
    if (!confirm('¿Marcar este lead como convertido?')) return;

    // TODO: Implementar llamada API
    showToast('Lead marcado como convertido', 'success');
    loadColdLeads();
}

// ============================================
// APPOINTMENTS
// ============================================

async function loadAppointments() {
    const clientId = document.getElementById('appointments-client-selector').value;
    const container = document.getElementById('appointments-list');

    if (!clientId) {
        container.innerHTML = '<p class="chat-placeholder">Selecciona un cliente para ver citas</p>';
        return;
    }

    try {
        const res = await fetch(`/api/clients/${clientId}/appointments?status=tomorrow`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.appointments || data.appointments.length === 0) {
            container.innerHTML = '<p class="chat-placeholder">No hay citas programadas para mañana</p>';
            return;
        }

        let html = `<p style="margin-bottom: 15px; color: var(--text-muted);">${data.total} citas para mañana</p>`;
        html += '<div style="display: grid; gap: 10px;">';

        data.appointments.forEach(apt => {
            const aptDate = apt.appointment_date ? new Date(apt.appointment_date).toLocaleString() : 'Fecha inválida';
            const statusBadge = getStatusBadge(apt.status);

            html += `
                <div class="chat-card" style="padding: 15px; border-left: 3px solid var(--primary);">
                    <div class="chat-card-header" style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="font-weight: 600;">👤 ${escapeHtml(apt.customer_name || 'Sin nombre')}</span>
                        ${statusBadge}
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-muted);">
                        <p>📅 ${aptDate}</p>
                        <p>📱 ${escapeHtml(apt.phone_number)}</p>
                        ${apt.notes ? `<p>📝 ${escapeHtml(apt.notes)}</p>` : ''}
                        ${apt.reminder_sent ? '<p style="color: var(--success);">✅ Recordatorio enviado</p>' : '<p style="color: var(--warning);">⚠️ Recordatorio pendiente</p>'}
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                        <button class="btn btn-sm btn-success" onclick="confirmAppointment(${apt.id})">
                            ✅ Confirmar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="cancelAppointment(${apt.id})">
                            ❌ Cancelar
                        </button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="chat-placeholder" style="color: var(--danger);">Error al cargar citas</p>';
    }
}

async function confirmAppointment(appointmentId) {
    try {
        const res = await fetch(`/api/clients/0/appointments/${appointmentId}/confirm`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            showToast('Cita confirmada', 'success');
            loadAppointments();
        } else {
            showToast('Error al confirmar', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm('¿Cancelar esta cita?')) return;

    try {
        const res = await fetch(`/api/clients/0/appointments/${appointmentId}/cancel`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            showToast('Cita cancelada', 'success');
            loadAppointments();
        } else {
            showToast('Error al cancelar', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

// ============================================
// INITIALIZATION
// ============================================

// Cargar clientes cuando se muestra la sección Email & Leads
// Esperamos a que la función showSection esté disponible
function initEmailLeads() {
    console.log('Email & Leads initializing...');

    // Intentar cargar clientes inmediatamente
    loadClientsForSelectors();
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEmailLeads);
} else {
    initEmailLeads();
}
