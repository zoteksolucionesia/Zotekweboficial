const token = localStorage.getItem('zotek_token');

if (!token && (window.location.pathname.startsWith('/admin') || window.location.pathname === '/admin/')) {
    window.location.href = '/login';
}

let allClients = [];

function showSection(sectionId) {
    const sections = ['clients', 'docs', 'settings'];
    sections.forEach(s => {
        document.getElementById(`section-${s}`).classList.add('hidden');
        document.getElementById(`nav-${s}`).style.color = 'var(--text-muted)';
    });
    document.getElementById(`section-${sectionId}`).classList.remove('hidden');
    document.getElementById(`nav-${sectionId}`).style.color = 'var(--primary)';

    if (sectionId === 'docs') {
        populateClientSelector();
    }
    if (sectionId === 'settings') {
        loadSettings();
    }
}

async function fetchClients() {
    const response = await fetch('/api/clients', {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.status === 401) {
        localStorage.removeItem('zotek_token');
        window.location.href = '/login';
        return;
    }

    allClients = await response.json();
    const tbody = document.getElementById('client-table-body');
    tbody.innerHTML = '';

    allClients.forEach(client => {
        const row = `
            <tr>
                <td>${client.id}</td>
                <td>${client.name}</td>
                <td><code>${client.phone_number_id}</code></td>
                <td>${new Date(client.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn" onclick="editClient(${client.id})">Editar</button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function openModal(isEdit = false) {
    document.getElementById('clientModal').style.display = 'flex';
    document.getElementById('modalTitle').innerText = isEdit ? 'Editar Cliente' : 'Agregar Cliente';
    if (!isEdit) {
        document.getElementById('clientForm').reset();
        document.getElementById('clientId').value = '';
    }
}

function closeModal() {
    document.getElementById('clientModal').style.display = 'none';
}

async function editClient(id) {
    const response = await fetch(`/api/clients/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const client = await response.json();

    document.getElementById('clientId').value = client.id;
    document.getElementById('clientName').value = client.name;
    document.getElementById('whatsappToken').value = client.whatsapp_token;
    document.getElementById('phoneNumberId').value = client.phone_number_id;
    document.getElementById('verifyToken').value = client.verify_token;
    document.getElementById('systemInstruction').value = client.system_instruction || '';

    openModal(true);
}

async function saveClient(event) {
    event.preventDefault();
    const id = document.getElementById('clientId').value;
    const data = {
        name: document.getElementById('clientName').value,
        whatsapp_token: document.getElementById('whatsappToken').value,
        phone_number_id: document.getElementById('phoneNumberId').value,
        verify_token: document.getElementById('verifyToken').value,
        system_instruction: document.getElementById('systemInstruction').value,
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/clients/${id}` : '/api/clients';

    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        closeModal();
        fetchClients();
    } else {
        alert('Error al guardar cliente');
    }
}

// Knowledge Base Logic
function populateClientSelector() {
    const selector = document.getElementById('doc-client-selector');
    selector.innerHTML = '<option value="">Selecciona un cliente...</option>';
    allClients.forEach(client => {
        selector.innerHTML += `<option value="${client.id}">${client.name}</option>`;
    });
}

async function loadDocuments() {
    const clientId = document.getElementById('doc-client-selector').value;
    if (!clientId) return;

    const res = await fetch(`/api/clients/${clientId}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const docs = await res.json();
    const tbody = document.getElementById('doc-table-body');
    tbody.innerHTML = '';

    if (docs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No hay documentos cargados para este cliente</td></tr>';
        return;
    }

    docs.forEach(doc => {
        tbody.innerHTML += `
            <tr>
                <td>${doc.source_file}</td>
                <td>${new Date(doc.updated_at).toLocaleString()}</td>
                <td>
                    <button class="btn" style="color:#ff6b6b;">Eliminar</button>
                </td>
            </tr>
        `;
    });
}

// Settings Logic
async function loadSettings() {
    try {
        const res = await fetch('/api/settings', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 401) {
            localStorage.removeItem('zotek_token');
            window.location.href = '/login';
            return;
        }

        const data = await res.json();

        // Populate Security card
        document.getElementById('s-admin-email').textContent = data.admin_email || '—';

        // Populate Bot Config card
        const webhookEl = document.getElementById('s-webhook-url');
        webhookEl.textContent = data.webhook_url || '—';
        webhookEl.dataset.url = data.webhook_url || '';

        const geminiBadge = document.getElementById('s-gemini-badge');
        if (data.gemini_api_key_set) {
            geminiBadge.textContent = '✓ Configurada';
            geminiBadge.className = 'status-badge status-active';
        } else {
            geminiBadge.textContent = '✗ No configurada';
            geminiBadge.className = 'status-badge status-warning';
        }

        // Populate System Info card
        const env = data.environment || 'unknown';
        document.getElementById('s-environment').textContent = env === 'production' ? 'Producción' : 'Desarrollo';
        const envBadge = document.getElementById('s-env-badge');
        if (env === 'production') {
            envBadge.textContent = '🚀 Producción';
            envBadge.className = 'status-badge status-active';
        } else {
            envBadge.textContent = '🔧 Desarrollo';
            envBadge.className = 'status-badge status-info';
        }
        document.getElementById('s-version').textContent = `v${data.api_version || '1.0.0'}`;
        document.getElementById('s-clients').textContent = `${data.total_clients ?? '—'} cliente(s)`;

        // Timestamp
        document.getElementById('settings-last-updated').textContent =
            `Actualizado: ${new Date().toLocaleTimeString()}`;

    } catch (e) {
        console.error('Error cargando ajustes:', e);
    }
}

function logout() {
    localStorage.removeItem('zotek_token');
    window.location.href = '/login';
}

function copyWebhook() {
    const url = document.getElementById('s-webhook-url').dataset.url;
    if (url) {
        navigator.clipboard.writeText(url).then(() => {
            const btn = event.currentTarget;
            btn.textContent = '✓';
            setTimeout(() => { btn.textContent = '📋'; }, 2000);
        });
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', fetchClients);
