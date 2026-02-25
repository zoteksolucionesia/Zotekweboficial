const token = localStorage.getItem('zotek_token');
let currentUser = null;

if (!token && (window.location.pathname.startsWith('/admin') || window.location.pathname === '/admin-control' || window.location.pathname === '/dashboard')) {
    window.location.href = '/login';
}

async function checkUserRole() {
    try {
        const res = await fetch('/api/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            currentUser = await res.json();
            applyRoleRestrictions();
        } else {
            logout();
        }
    } catch (e) {
        console.error("Auth error:", e);
    }
}

function applyRoleRestrictions() {
    if (!currentUser) return;

    if (currentUser.role === 'client') {
        // Ocultar sección de lista de clientes
        const navClients = document.getElementById('nav-clients');
        if (navClients) navClients.style.display = 'none';

        // Ocultar ajustes globales
        const navSettings = document.getElementById('nav-settings');
        if (navSettings) navSettings.style.display = 'none';

        // Redirigir a sección de documentos si está en la de clientes
        if (document.getElementById('section-clients') && !document.getElementById('section-clients').classList.contains('hidden')) {
            showSection('docs');
        }

        // Bloquear selector de clientes en docs y chats
        const selectors = ['doc-client-selector', 'chat-client-selector'];
        selectors.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.value = currentUser.client_id;
                el.disabled = true;
                el.style.opacity = '0.5';
                // Disparar carga manual
                if (id === 'doc-client-selector') loadDocuments();
                if (id === 'chat-client-selector') loadChats();
            }
        });

        // Añadir botón de "Mi Bot" en el sidebar si no existe
        const sidebar = document.querySelector('.sidebar-nav');
        if (sidebar && !document.getElementById('nav-mybot')) {
            const botBtn = document.createElement('a');
            botBtn.id = 'nav-mybot';
            botBtn.href = '#';
            botBtn.className = 'nav-item';
            botBtn.innerHTML = '🤖 Mi Bot';
            botBtn.onclick = () => editClient(currentUser.client_id);
            sidebar.prepend(botBtn);
        }
    }
}

let allClients = [];

function showSection(sectionId) {
    // Ocultar TODAS las secciones por ID para evitar que se mezclen (p. ej. con caché viejo)
    document.querySelectorAll('[id^="section-"]').forEach(el => {
        el.classList.add('hidden');
    });
    document.querySelectorAll('[id^="nav-"]').forEach(nav => {
        nav.style.color = 'var(--text-muted)';
    });

    const activeSection = document.getElementById(`section-${sectionId}`);
    const activeNav = document.getElementById(`nav-${sectionId}`);
    if (activeSection) activeSection.classList.remove('hidden');
    if (activeNav) activeNav.style.color = 'var(--primary)';

    if (sectionId === 'docs' || sectionId === 'chats') {
        if (allClients.length === 0) {
            fetchClients().then(() => populateClientSelector());
        } else {
            populateClientSelector();
        }
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
        // En la tabla general (Admin), mostrar el email de login si existe
        const row = `
            <tr>
                <td><small style="color:var(--text-muted);">${client.id}</small></td>
                <td>
                    <b>${client.name}</b><br>
                    <small style="color:var(--text-muted);">${client.email || 'Sin email configurado'}</small>
                </td>
                <td><code>${client.phone_number_id}</code></td>
                <td>${client.created_at ? new Date(client.created_at).toLocaleDateString() : '—'}</td>
                <td>
                    <button class="btn" onclick="editClient('${String(client.id).replace(/'/g, "\\'")}')">Editar</button>
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
        currentMenu = { options: [] };
        renderMenuEditor();
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
    document.getElementById('whatsappToken').value = client.whatsapp_token || '';
    document.getElementById('phoneNumberId').value = client.phone_number_id || '';
    document.getElementById('verifyToken').value = client.verify_token || '';
    document.getElementById('systemInstruction').value = client.system_instruction || '';

    // SaaS Phase 3 fields
    document.getElementById('clientEmail').value = client.email || '';
    document.getElementById('calendlyUrl').value = client.calendly_url || '';

    // Load Menu
    await loadClientMenu(id);

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
        email: document.getElementById('clientEmail').value,
        calendly_url: document.getElementById('calendlyUrl').value,
        menu: {
            ...currentMenu,
            text: document.getElementById('menuWelcomeText').value
        }
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
let currentPdfClientId = null;

// Menu Editor Logic
let currentMenu = { options: [] };

async function loadClientMenu(clientId) {
    try {
        const res = await fetch(`/api/clients/${clientId}/menu`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            currentMenu = await res.json();
            document.getElementById('menuWelcomeText').value = currentMenu.text || '';
        } else {
            currentMenu = { options: [] };
            document.getElementById('menuWelcomeText').value = '';
        }
    } catch (e) {
        console.error("Error loading menu:", e);
        currentMenu = { options: [] };
    }
    renderMenuEditor();
}

function renderMenuEditor() {
    const container = document.getElementById('menu-editor-container');
    if (!container) return;
    container.innerHTML = '';

    if (!currentMenu.options || currentMenu.options.length === 0) {
        container.innerHTML = '<div style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:1rem;">El menú está vacío. Añade tu primera opción principal.</div>';
        return;
    }

    const menuList = document.createElement('div');
    menuList.style.display = 'flex';
    menuList.style.flexDirection = 'column';
    menuList.style.gap = '0.8rem';

    currentMenu.options.forEach((option, index) => {
        menuList.appendChild(createMenuNode(option, [index]));
    });

    container.appendChild(menuList);
}

function createMenuNode(option, path) {
    const isString = typeof option === 'string';
    const title = isString ? option : (option.title || '');
    const response = isString ? '' : (option.response || '');
    const hasSubmenu = !isString && option.submenu && option.submenu.options;

    const node = document.createElement('div');
    node.className = 'menu-node';
    node.style.border = '1px solid rgba(255,193,7,0.2)';
    node.style.borderRadius = '8px';
    node.style.padding = '0.8rem';
    node.style.background = 'rgba(255,255,255,0.03)';

    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.gap = '0.5rem';
    header.style.marginBottom = '0.5rem';

    const titleInput = document.createElement('input');
    titleInput.type = 'text';
    titleInput.placeholder = 'Título (ej: Precios)';
    titleInput.value = title;
    titleInput.style.flex = '1';
    titleInput.style.fontSize = '0.85rem';
    titleInput.onchange = (e) => updateMenuValue(path, 'title', e.target.value);

    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.innerHTML = '×';
    deleteBtn.className = 'btn';
    deleteBtn.style.padding = '0.2rem 0.5rem';
    deleteBtn.style.background = 'rgba(255,107,107,0.1)';
    deleteBtn.style.color = '#ff6b6b';
    deleteBtn.onclick = () => removeMenuOption(path);

    header.appendChild(titleInput);
    header.appendChild(deleteBtn);
    node.appendChild(header);

    if (!hasSubmenu) {
        const respArea = document.createElement('textarea');
        respArea.placeholder = 'Respuesta del bot...';
        respArea.value = response;
        respArea.style.width = '100%';
        respArea.style.height = '40px';
        respArea.style.fontSize = '0.8rem';
        respArea.style.marginTop = '0.2rem';
        respArea.onchange = (e) => updateMenuValue(path, 'response', e.target.value);
        node.appendChild(respArea);

        const subBtn = document.createElement('button');
        subBtn.type = 'button';
        subBtn.textContent = '+ Sub-menú';
        subBtn.className = 'btn';
        subBtn.style.fontSize = '0.7rem';
        subBtn.style.marginTop = '0.5rem';
        subBtn.style.background = 'rgba(255,193,7,0.1)';
        subBtn.style.color = 'var(--primary)';
        subBtn.onclick = () => addSubmenu(path);
        node.appendChild(subBtn);
    } else {
        const subContainer = document.createElement('div');
        subContainer.style.marginLeft = '1.5rem';
        subContainer.style.marginTop = '0.8rem';
        subContainer.style.paddingLeft = '0.8rem';
        subContainer.style.borderLeft = '2px dashed rgba(255,193,7,0.2)';

        const subHeader = document.createElement('div');
        subHeader.style.fontSize = '0.7rem';
        subHeader.style.color = 'var(--text-muted)';
        subHeader.style.marginBottom = '0.5rem';
        subHeader.textContent = 'SUB-MENÚ:';
        subContainer.appendChild(subHeader);

        option.submenu.options.forEach((subOpt, subIndex) => {
            subContainer.appendChild(createMenuNode(subOpt, [...path, 'submenu', 'options', subIndex]));
        });

        const addSubBtn = document.createElement('button');
        addSubBtn.type = 'button';
        addSubBtn.textContent = '+ Opción hija';
        addSubBtn.className = 'btn';
        addSubBtn.style.fontSize = '0.7rem';
        addSubBtn.style.width = '100%';
        addSubBtn.style.marginTop = '0.5rem';
        addSubBtn.onclick = () => addMenuOption([...path, 'submenu', 'options']);
        subContainer.appendChild(addSubBtn);

        node.appendChild(subContainer);
    }

    return node;
}

function updateMenuValue(path, key, value) {
    let current = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
    }
    const lastIdx = path[path.length - 1];

    if (typeof current[lastIdx] === 'string') {
        current[lastIdx] = { title: current[lastIdx], response: '' };
    }
    current[lastIdx][key] = value;
}

function addMenuOption(parentPath) {
    const newOpt = { title: '', response: '' };
    if (parentPath === null) {
        currentMenu.options.push(newOpt);
    } else {
        let target = currentMenu.options;
        for (let i = 0; i < parentPath.length; i++) {
            target = target[parentPath[i]];
        }
        target.push(newOpt);
    }
    renderMenuEditor();
}

function removeMenuOption(path) {
    let current = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
    }
    current.splice(path[path.length - 1], 1);
    renderMenuEditor();
}

function addSubmenu(path) {
    let current = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
    }
    const idx = path[path.length - 1];
    if (typeof current[idx] === 'string') {
        current[idx] = { title: current[idx], response: '' };
    }
    current[idx].submenu = { text: 'Selecciona una opción:', options: [] };
    current[idx].response = ''; // Limpiamos respuesta si se vuelve submenú
    renderMenuEditor();
}

function populateClientSelector() {
    console.log("DEBUG: Populating client selectors with", allClients.length, "clients");
    const selectors = ['doc-client-selector', 'chat-client-selector'];
    selectors.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const currentValue = el.value;
            el.innerHTML = '<option value="">Selecciona un cliente...</option>';
            allClients.forEach(client => {
                const selected = client.id == currentValue ? 'selected' : '';
                el.innerHTML += `<option value="${client.id}" ${selected}>${client.name}</option>`;
            });
        }
    });
}

function populateChatClientSelector() {
    // Redirigir a la función genérica para mantener coherencia
    populateClientSelector();
}

async function loadChats() {
    const clientId = document.getElementById('chat-client-selector').value;
    const container = document.getElementById('chat-history-list');
    if (!container) return;

    if (!clientId) {
        container.innerHTML = '<p class="chat-placeholder">Selecciona un cliente para ver el historial de conversaciones con el bot.</p>';
        return;
    }

    try {
        const res = await fetch(`/api/clients/${clientId}/chats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) {
            localStorage.removeItem('zotek_token');
            window.location.href = '/login';
            return;
        }
        const chats = await res.json();

        if (chats.length === 0) {
            container.innerHTML = '<p class="chat-placeholder">No hay mensajes registrados para este cliente aún.</p>';
            return;
        }

        container.innerHTML = chats.map(chat => {
            const date = chat.timestamp ? new Date(chat.timestamp).toLocaleString() : '—';
            const msg = escapeHtml(chat.message || '');
            const resp = escapeHtml(chat.response || '');
            return `
                <div class="chat-card">
                    <div class="chat-card-header">
                        <span class="chat-card-user">📱 ${escapeHtml(chat.user_number || '')}</span>
                        <span class="chat-card-date">${escapeHtml(date)}</span>
                    </div>
                    <div class="chat-card-message">
                        <div class="chat-card-label">Usuario</div>
                        <div>${msg}</div>
                    </div>
                    <div>
                        <div class="chat-card-label">Bot</div>
                        <div class="chat-card-response">${resp}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="chat-placeholder">Error al cargar el historial. Intenta de nuevo.</p>';
    }
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
        const fileName = doc.source_file || 'Documento sin nombre';
        tbody.innerHTML += `
            <tr>
                <td>${escapeHtml(fileName)}</td>
                <td>${doc.updated_at ? new Date(doc.updated_at).toLocaleString() : '—'}</td>
                <td>
                    <button type="button" class="btn" style="color:#ff6b6b;" data-client-id="${escapeAttr(clientId)}" data-doc-id="${escapeAttr(doc.id)}" data-source="${escapeAttr(fileName)}" onclick="deleteDocument(this)">Eliminar</button>
                </td>
            </tr>
        `;
    });
}

function triggerPdfUpload() {
    const clientId = document.getElementById('doc-client-selector') && document.getElementById('doc-client-selector').value;
    if (!clientId) {
        showConfirmDelete({
            title: 'Selecciona un cliente',
            message: 'Elige un cliente en el desplegable antes de subir un documento PDF. El archivo se vinculará como fuente de datos del bot de ese cliente.',
            showCancel: false,
            confirmText: 'Entendido'
        });
        return;
    }
    currentPdfClientId = clientId;
    const input = document.getElementById('pdfInput');
    if (!input) {
        showConfirmDelete({
            title: 'Error',
            message: 'No se pudo abrir el selector de archivos. Recarga la página e inténtalo de nuevo.',
            showCancel: false,
            confirmText: 'Cerrar'
        });
        return;
    }
    input.value = '';
    input.click();
}

async function handleFileSelect(event) {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;
    if (!currentPdfClientId) return;

    if (file.type !== 'application/pdf') {
        showConfirmDelete({
            title: 'Archivo no válido',
            message: 'Solo se permiten archivos PDF.',
            showCancel: false,
            confirmText: 'Cerrar'
        });
        currentPdfClientId = null;
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const btn = document.getElementById('btnSubirPdf');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Subiendo…';
    }

    try {
        const response = await fetch(`/api/clients/${currentPdfClientId}/upload-pdf`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            loadDocuments();
            showConfirmDelete({
                title: 'Documento agregado',
                message: result.message || `"${file.name}" se añadió a la base de conocimientos. El bot usará este contenido para responder.`,
                showCancel: false,
                confirmText: 'Cerrar'
            });
        } else {
            showConfirmDelete({
                title: 'Error al subir',
                message: result.detail || 'No se pudo procesar el PDF.',
                showCancel: false,
                confirmText: 'Cerrar'
            });
        }
    } catch (e) {
        console.error(e);
        showConfirmDelete({
            title: 'Error de conexión',
            message: 'No se pudo subir el archivo. Revisa tu conexión e inténtalo de nuevo.',
            showCancel: false,
            confirmText: 'Cerrar'
        });
    } finally {
        currentPdfClientId = null;
        if (btn) {
            btn.disabled = false;
            btn.textContent = '📄 Subir PDF';
        }
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
function escapeAttr(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

async function deleteDocument(button) {
    const clientId = button.getAttribute('data-client-id');
    const docId = button.getAttribute('data-doc-id');
    const sourceName = button.getAttribute('data-source') || 'este documento';
    if (!clientId || !docId) return;

    showConfirmDelete({
        title: '¿Eliminar documento?',
        message: `¿Estás seguro de que deseas eliminar "${sourceName}" de la base de conocimientos de este cliente? El bot dejará de usar este contenido.`,
        onConfirm: async () => {
            button.disabled = true;
            button.textContent = '…';
            try {
                const res = await fetch(`/api/clients/${clientId}/documents/${docId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    hideConfirmDelete();
                    loadDocuments();
                } else {
                    const err = await res.json().catch(() => ({}));
                    showConfirmDelete({
                        title: 'Error',
                        message: err.detail || 'No se pudo eliminar el documento.',
                        showCancel: false,
                        confirmText: 'Cerrar'
                    });
                    button.disabled = false;
                    button.textContent = 'Eliminar';
                }
            } catch (e) {
                console.error(e);
                showConfirmDelete({
                    title: 'Error',
                    message: 'Error de conexión al eliminar.',
                    showCancel: false,
                    confirmText: 'Cerrar'
                });
                button.disabled = false;
                button.textContent = 'Eliminar';
            }
        }
    });
}

function hideConfirmDelete() {
    const overlay = document.getElementById('confirmDeleteOverlay');
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
}

function showConfirmDelete(options) {
    const overlay = document.getElementById('confirmDeleteOverlay');
    const titleEl = document.getElementById('confirmDeleteTitle');
    const messageEl = document.getElementById('confirmDeleteMessage');
    const cancelBtn = document.getElementById('confirmDeleteCancel');
    const okBtn = document.getElementById('confirmDeleteOk');

    titleEl.textContent = options.title || '¿Estás seguro?';
    messageEl.textContent = options.message || '';
    okBtn.textContent = options.confirmText || 'Eliminar';

    const showCancel = options.showCancel !== false;
    cancelBtn.style.display = showCancel ? '' : 'none';

    const onConfirm = options.onConfirm || (() => { });
    const onCancel = options.onCancel || (() => { });

    function close() {
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
        okBtn.onclick = null;
        cancelBtn.onclick = null;
        overlay.onclick = null;
    }

    okBtn.onclick = () => {
        close();
        onConfirm();
    };
    cancelBtn.onclick = () => {
        close();
        onCancel();
    };

    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            close();
            onCancel();
        }
    };
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

        const adminEl = document.getElementById('s-admin-email');
        if (adminEl) adminEl.textContent = data.admin_email || '—';

        const webhookEl = document.getElementById('s-webhook-url');
        if (webhookEl) {
            webhookEl.textContent = data.webhook_url || '—';
            webhookEl.dataset.url = data.webhook_url || '';
        }

        const geminiBadge = document.getElementById('s-gemini-badge');
        if (geminiBadge) {
            if (data.gemini_api_key_set) {
                geminiBadge.textContent = '✓ Configurada';
                geminiBadge.className = 'status-badge status-active';
            } else {
                geminiBadge.textContent = '✗ No configurada';
                geminiBadge.className = 'status-badge status-warning';
            }
        }

        const env = data.environment || 'unknown';
        const envEl = document.getElementById('s-environment');
        if (envEl) envEl.textContent = env === 'production' ? 'Producción' : 'Desarrollo';

        const envBadge = document.getElementById('s-env-badge');
        if (envBadge) {
            if (env === 'production') {
                envBadge.textContent = '🚀 Producción';
                envBadge.className = 'status-badge status-active';
            } else {
                envBadge.textContent = '🔧 Desarrollo';
                envBadge.className = 'status-badge status-info';
            }
        }

        const versionEl = document.getElementById('s-version');
        if (versionEl) versionEl.textContent = `v${data.api_version || '1.0.0'}`;

        const clientsEl = document.getElementById('s-clients');
        if (clientsEl) clientsEl.textContent = `${data.total_clients ?? '—'} cliente(s)`;

        const lastUpdated = document.getElementById('settings-last-updated');
        if (lastUpdated) lastUpdated.textContent = `Actualizado: ${new Date().toLocaleTimeString()}`;

    } catch (e) {
        console.error('Error cargando ajustes:', e);
    }
}

function logout() {
    localStorage.removeItem('zotek_token');
    window.location.href = '/login';
}

function copyWebhook() {
    const webhookEl = document.getElementById('s-webhook-url');
    const url = webhookEl && webhookEl.dataset.url;
    if (url) {
        navigator.clipboard.writeText(url).then(() => {
            const btn = event.currentTarget;
            btn.textContent = '✓';
            setTimeout(() => { btn.textContent = '📋'; }, 2000);
        });
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', async () => {
    await checkUserRole();
    if (currentUser && currentUser.role === 'admin') {
        fetchClients();
    }
});
