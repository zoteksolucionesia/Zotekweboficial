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
        // Forzar recarga si ya hay un cliente seleccionado (para persistencia visual)
        if (sectionId === 'docs') loadDocuments();
        if (sectionId === 'chats') loadChats();
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
                    <button class="btn btn-primary" onclick="editClient('${String(client.id).replace(/'/g, "\\'")}')">Editar</button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });

    // Popular selectores de chats y documentos
    populateClientSelector();
}

function populateClientSelector() {
    console.log("Populating client selectors...");
    const chatSelector = document.getElementById('chat-client-selector');
    const docSelector = document.getElementById('doc-client-selector');
    if (!chatSelector || !docSelector) {
        console.warn("Selectors not found in DOM");
        return;
    }

    let options = '<option value="">Selecciona un cliente...</option>';

    if (allClients && allClients.length > 0) {
        allClients.forEach(client => {
            options += `<option value="${client.id}">${client.name}</option>`;
        });
    } else if (currentUser && currentUser.client_id) {
        // Si no hay lista completa pero tenemos cliente actual (rol cliente)
        options += `<option value="${currentUser.client_id}">Mi Empresa</option>`;
    }

    chatSelector.innerHTML = options;
    docSelector.innerHTML = options;

    // Si somos cliente, seleccionar automáticamente
    if (currentUser && currentUser.role === 'client') {
        chatSelector.value = currentUser.client_id;
        docSelector.value = currentUser.client_id;
    }
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
    // Asegurar que el scroll empiece arriba
    const modalGrid = document.querySelector('.modal-grid');
    if (modalGrid) modalGrid.scrollTop = 0;

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

let currentEditingPath = null; // null means 'Home', arrays like [0, 1] means specific node

function renderMenuEditor() {
    renderMenuTree();

    if (currentEditingPath === null) {
        showBotHome(); // Render the Home Cards or Welcome message
    } else {
        renderEditorForm(currentEditingPath);
    }
}

function renderMenuTree() {
    const treeContainer = document.getElementById('menu-tree');
    if (!treeContainer) return;
    treeContainer.innerHTML = '';

    // Raíz
    const rootLi = document.createElement('li');
    rootLi.className = 'tree-node';

    const rootDiv = document.createElement('div');
    rootDiv.className = `tree-item ${currentEditingPath === null ? 'active' : ''}`;
    rootDiv.innerHTML = `<i class="fas fa-robot tree-icon"></i> Inicio del Menú`;
    rootDiv.onclick = () => { currentEditingPath = null; renderMenuEditor(); };

    rootLi.appendChild(rootDiv);

    if (currentMenu.options && currentMenu.options.length > 0) {
        const rootUl = document.createElement('ul');
        rootUl.className = 'tree-children open';
        renderTreeNodes(currentMenu.options, [], rootUl);
        rootLi.appendChild(rootUl);
    }

    treeContainer.appendChild(rootLi);
}

function renderTreeNodes(options, basePath, parentUl) {
    if (!options) return;
    options.forEach((opt, index) => {
        const currentPath = [...basePath, index];
        const isString = typeof opt === 'string';
        const title = isString ? opt : (opt.title || `Opción ${index + 1}`);
        const hasSubmenu = !isString && opt.submenu && opt.submenu.options;
        const isActive = JSON.stringify(currentEditingPath) === JSON.stringify(currentPath);

        const li = document.createElement('li');
        li.className = 'tree-node';

        const div = document.createElement('div');
        div.className = `tree-item ${isActive ? 'active' : ''} ${hasSubmenu ? 'expanded' : ''}`;

        // Icono dependiendo de si tiene submenu
        const iconClass = hasSubmenu ? 'fas fa-chevron-right' : 'far fa-circle';
        div.innerHTML = `<i class="${iconClass} tree-icon"></i> ${escapeHtml(title)}`;

        const toggleIcon = div.querySelector('.tree-icon');

        div.onclick = (e) => {
            currentEditingPath = currentPath;
            renderMenuEditor();
        };

        if (hasSubmenu) {
            // Permitir colapsar/expandir haciendo clic en el icono
            toggleIcon.onclick = (e) => {
                e.stopPropagation(); // Evitar seleccionar el nodo si solo se quiere expandir
                const childrenUl = li.querySelector('.tree-children');
                if (childrenUl) {
                    childrenUl.classList.toggle('open');
                    div.classList.toggle('expanded');
                }
            };
        }

        li.appendChild(div);

        if (hasSubmenu) {
            const ul = document.createElement('ul');
            // Si hay un nodo activo dentro, asegurarnos de que el panel esté abierto por defecto
            const isChildActive = JSON.stringify(currentEditingPath || []).startsWith(JSON.stringify(currentPath).slice(0, -1));

            ul.className = `tree-children ${isChildActive || currentEditingPath === null ? 'open' : ''}`;
            // siempre abierto inicialmente para mejor UX
            ul.classList.add('open');
            div.classList.add('expanded');

            renderTreeNodes(opt.submenu.options, [...currentPath, 'submenu', 'options'], ul);
            li.appendChild(ul);
        }

        parentUl.appendChild(li);
    });
}

function showBotHome() {
    currentEditingPath = null;
    const panel = document.getElementById('bot-editor-panel');
    if (!panel) return;

    panel.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h4 style="color: var(--primary); margin:0; font-size: 1.2rem;">Panel Principal del Bot</h4>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 5px;">Configura el flujo inicial y las opciones principales.</p>
        </div>
        
        <div class="form-group" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
            <label style="color: #58a6ff; font-weight: bold; font-size: 0.8rem; text-transform: uppercase;">Mensaje de Bienvenida</label>
            <textarea id="menuWelcomeText" class="menu-field-input" rows="3" placeholder="Ej: Hola, bienvenido a..." style="margin-top: 10px; width: 100%;">${escapeHtml(currentMenu.text || '')}</textarea>
            <small style="color: var(--text-muted); font-size: 0.75rem;">Este es el primer mensaje que envía el bot junto con el menú principal.</small>
        </div>

        <div class="action-cards-grid">
            <div class="action-card" onclick="addMenuOption(null)">
                <i class="fas fa-plus-circle"></i>
                <h4>Añadir Opción Principal</h4>
                <p>Crea un nuevo botón en el menú de inicio.</p>
            </div>
            <div class="action-card" onclick="closeModal(); showSection('docs');">
                <i class="fas fa-file-pdf"></i>
                <h4>Base de Conocimientos</h4>
                <p>Gestiona los documentos PDF del bot.</p>
            </div>
            <div class="action-card" onclick="closeModal(); showSection('settings');">
                <i class="fas fa-cog"></i>
                <h4>Ajustes Globales</h4>
                <p>Configura llaves del bot y webhooks.</p>
            </div>
        </div>
    `;

    const welcomeInput = document.getElementById('menuWelcomeText');
    if (welcomeInput) {
        welcomeInput.onchange = (e) => {
            currentMenu.text = e.target.value;
        };
    }
}

function renderEditorForm(path) {
    const panel = document.getElementById('bot-editor-panel');
    if (!panel) return;

    let target = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        target = target[path[i]];
    }
    const idx = path[path.length - 1];
    const option = target[idx];

    if (!option) {
        currentEditingPath = null;
        renderMenuEditor();
        return;
    }

    const isString = typeof option === 'string';
    const title = isString ? option : (option.title || '');
    const response = isString ? '' : (option.response || '');
    const hasSubmenu = !isString && option.submenu && option.submenu.options;

    let contentHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
            <h4 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-edit" style="color: var(--primary);"></i> Editando Opción
            </h4>
            <button type="button" class="btn btn-danger btn-sm" onclick="removeMenuOption(${JSON.stringify(path)})" style="padding: 6px 12px; font-size: 0.8rem; background: rgba(255, 107, 107, 0.1); color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.3);">
                <i class="fas fa-trash"></i> Eliminar
            </button>
        </div>

        <div class="menu-node" style="border: none; background: transparent; padding: 0 !important; box-shadow: none;">
            <div class="form-group">
                <label class="menu-field-label">Etiqueta del Botón (Título visual)</label>
                <input type="text" id="editor-node-title" class="menu-field-input" value="${escapeHtml(title)}" placeholder="Por ejemplo: Servicios, Ventas, FAQ..." style="font-size: 1.1rem; padding: 12px; font-weight: 500;">
            </div>
    `;

    if (hasSubmenu) {
        contentHTML += `
            <div style="background: rgba(88, 166, 255, 0.05); border: 1px solid rgba(88, 166, 255, 0.2); border-radius: 8px; padding: 25px 15px; text-align: center; margin-top: 20px;">
                <i class="fas fa-sitemap" style="font-size: 2.5rem; color: var(--primary); margin-bottom: 15px; opacity: 0.8;"></i>
                <h5 style="margin: 0 0 10px 0; color: #fff; font-size: 1.1rem;">Este botón abre un Sub-menú</h5>
                <p style="font-size: 0.9rem; color: var(--text-muted); margin: 0 0 20px 0;">Actualmente contiene ${option.submenu.options.length} opciones hijas.</p>
                <button type="button" class="btn btn-primary" onclick="addMenuOption(${JSON.stringify([...path, 'submenu', 'options'])})">
                    <i class="fas fa-plus"></i> Añadir Opción a este Sub-menú
                </button>
            </div>
        `;
    } else {
        contentHTML += `
            <div class="form-group" style="margin-top: 15px;">
                <label class="menu-field-label">Respuesta del Bot</label>
                <textarea id="editor-node-response" class="menu-field-input" rows="6" placeholder="Escribe el mensaje que enviará el bot cuando el usuario presione este botón... El texto también puede incluir emojis. (${escapeHtml(title)})">${escapeHtml(response)}</textarea>
            </div>
            
            <div style="margin-top: 30px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 20px;">
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px;"><i class="fas fa-info-circle"></i> ¿Necesitas que este botón despliegue OTRA lista de botones en lugar de texto?</p>
                <button type="button" class="btn btn-secondary" onclick="addSubmenu(${JSON.stringify(path)})" style="font-size: 0.85rem;">
                    <i class="fas fa-folder-plus"></i> Convertir en Sub-menú
                </button>
            </div>
        `;
    }

    contentHTML += `</div>`;
    panel.innerHTML = contentHTML;

    // Listeners
    const titleInput = document.getElementById('editor-node-title');
    if (titleInput) {
        titleInput.oninput = (e) => { // oninput to update tree in real time
            updateMenuValue(path, 'title', e.target.value);
            renderMenuTree();
        };
    }

    const respInput = document.getElementById('editor-node-response');
    if (respInput) {
        respInput.onchange = (e) => {
            updateMenuValue(path, 'response', e.target.value);
        };
    }
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
    const newOpt = { title: 'Nueva Opción', response: '' };
    if (parentPath === null) {
        if (!currentMenu.options) currentMenu.options = [];
        currentMenu.options.push(newOpt);
        currentEditingPath = [currentMenu.options.length - 1];
    } else {
        let target = currentMenu.options;
        for (let i = 0; i < parentPath.length; i++) {
            target = target[parentPath[i]];
        }
        if (!target) target = [];
        target.push(newOpt);
        currentEditingPath = [...parentPath, target.length - 1];
    }
    renderMenuEditor();
}

function removeMenuOption(path) {
    let current = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
    }
    current.splice(path[path.length - 1], 1);

    // Si eliminamos el nodo actual, volvemos a inicio
    if (JSON.stringify(currentEditingPath) === JSON.stringify(path)) {
        currentEditingPath = null;
    } else if (currentEditingPath !== null) {
        // Lógica simplificada: para evitar desajustes de índices si se borra un hermano anterior, reseteamos a inicio.
        // (Opcional, pero previene bugs si no se recalcula bien el path)
        currentEditingPath = null;
    }

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

    // Theme preference check
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
    }
});

// Theme Toggle Function
window.toggleTheme = function () {
    document.body.classList.toggle('light-mode');
    const isLight = document.body.classList.contains('light-mode');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
};
