const token = localStorage.getItem('zotek_token');
let currentUser = null;

/* Toast Notifications System */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error("Toast failed, container missing:", message);
        alert(message);
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    else if (type === 'error') icon = 'exclamation-triangle';
    else if (type === 'warning') icon = 'exclamation-circle';

    // Use a basic escape function to prevent html injection
    const escapedMsg = message.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
        }[tag] || tag));

    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <div class="toast-message">${escapedMsg}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

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

    // Ocultar/mostrar main-content según si estamos editando un cliente
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        if (sectionId === 'edit-client') {
            mainContent.classList.add('hidden');
        } else {
            mainContent.classList.remove('hidden');
        }
    }

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

    const demoClients = ['demo_clinica', 'demo_restaurante', 'demo_tienda'];

    allClients.forEach(client => {
        // En la tabla general (Admin), mostrar el email de login si existe
        let actionsHtml = `<button class="btn btn-primary" onclick="editClient('${client.id}')">Editar</button>`;

        // Agregar botón especial para clientes de demostración
        // Aseguramos que la comparación sea robusta
        const pId = String(client.phone_number_id || '').trim();
        if (demoClients.includes(pId)) {
            actionsHtml += ` <button class="btn btn-outline-danger" style="margin-left: 5px;" onclick="resetDemoClient('${client.id}')" title="Restaurar a configuración original">Restablecer</button>`;
        }

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
                    ${actionsHtml}
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
    document.getElementById('modalTitle').innerText = isEdit ? 'Editar Cliente' : 'Agregar Nuevo Cliente';
    if (!isEdit) {
        document.getElementById('clientForm').reset();
        document.getElementById('clientId').value = '';
        currentEditingPath = null;
        currentMenu = { options: [] };
        renderMenuEditor();
    }
    showSection('edit-client');
    // Asegurar que el scroll empiece arriba
    const modalGrid = document.querySelector('.modal-grid');
    if (modalGrid) modalGrid.scrollTop = 0;

}

function closeModal() {
    showSection('clients');
    document.getElementById('clientForm').reset();
}

async function resetDemoClient(id) {
    if (!confirm(`¿Estás seguro de que deseas restablecer el cliente de ejemplo '${id}' a su configuración original? Se perderán todos los cambios que hayas hecho en sus menús y respuestas.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/clients/${id}/reset`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            showToast(`Cliente '${id}' restablecido correctamente.`, 'success');
            fetchClients(); // Recargar la tabla para mostrar los datos limpios si fuera necesario
        } else {
            const data = await response.json();
            showToast('Error al restablecer: ' + (data.detail || data.error || 'Desconocido'), 'error');
        }
    } catch (error) {
        console.error("Error reseteando cliente:", error);
        showToast('Error de conexión al restablecer.', 'error');
    }
}

async function editClient(id) {
    try {
        console.log("Edit client called for id:", id);
        const response = await fetch(`/api/clients/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            console.error("HTTP error:", response.status);
            showToast('Error de servidor al cargar cliente', 'error');
            return;
        }

        const client = await response.json();
        console.log("Client loaded:", client);

        document.getElementById('clientId').value = client.id;
        document.getElementById('clientName').value = client.name;
        document.getElementById('whatsappToken').value = client.whatsapp_token || '';
        document.getElementById('phoneNumberId').value = client.phone_number_id || '';
        document.getElementById('verifyToken').value = client.verify_token || '';
        document.getElementById('systemInstruction').value = client.system_instruction || '';

        // SaaS Phase 3 fields
        document.getElementById('clientEmail').value = client.email || '';
        document.getElementById('calendlyUrl').value = client.calendly_url || '';

        // Clean UI state before loading menu
        currentEditingPath = null;

        // Load Menu
        await loadClientMenu(id);

        openModal(true);
    } catch (e) {
        console.error("Error in editClient:", e);
        showToast('Error interno al editar: ' + e.message, 'error');
    }
}

async function saveClient(event) {
    event.preventDefault();

    const nameInput = document.getElementById('clientName');
    if (!nameInput.value.trim()) {
        showToast('El Nombre del Negocio es obligatorio.', 'warning');
        nameInput.focus();
        return;
    }

    const id = document.getElementById('clientId').value;
    const data = {
        name: nameInput.value,
        whatsapp_token: document.getElementById('whatsappToken').value,
        phone_number_id: document.getElementById('phoneNumberId').value,
        verify_token: document.getElementById('verifyToken').value,
        system_instruction: document.getElementById('systemInstruction').value,
        email: document.getElementById('clientEmail').value,
        calendly_url: document.getElementById('calendlyUrl').value,
        menu: {
            ...currentMenu
        }
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/clients/${id}` : '/api/clients';

    try {
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
            showToast('Cambios guardados con éxito', 'success');
        } else {
            showToast('Error al guardar los cambios del cliente', 'error');
        }
    } catch (e) {
        showToast('Error de conexión al guardar', 'error');
    }
}

// Knowledge Base Logic
let currentPdfClientId = null;

// Menu Editor Logic
let currentMenu = { options: [] };

async function loadClientMenu(clientId) {
    console.log("Loading menu for client:", clientId);
    try {
        const res = await fetch(`/api/clients/${clientId}/menu`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            currentMenu = await res.json();
            console.log("Menu loaded successfully:", currentMenu);
        } else {
            const errorText = await res.text();
            console.error("Error response from server:", errorText);
            currentMenu = { options: [] };
        }
    } catch (e) {
        console.error("Exception loading menu:", e);
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

const EMOJI_CATEGORIES = [
    { name: "Caritas", emojis: ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😎", "🤓", "🧐", "😕", "😟", "🙁", "😮", "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀", "💩", "🤡", "👹", "👺", "👻", "👽", "👾", "🤖", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"] },
    { name: "Gestos", emojis: ["👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅", "🤳", "💪"] },
    { name: "Comida", emojis: ["🍏", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈", "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦", "🥬", "🥒", "🌶️", "🌽", "🥕", "🧄", "🧅", "🥔", "🍠", "🥐", "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🧈", "🥞", "🧇", "🥓", "🥩", "🍗", "🍖", "🌭", "🍔", "🍟", "🍕", "🥪", "🥙", "🧆", "🌮", "🌯", "🥗", "🥘", "🥫", "🍝", "🍜", "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤", "🍙", "🍚", "🍘", "🍥", "🥠", "🥮", "🍢", "🍡", "🍧", "🍨", "🍦"] },
    { name: "Tecnología", emojis: ["⌚", "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "🗜️", "💽", "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽️", "🎞️", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎚️", "🎛️", "🧭", "⏱️", "⏲️", "💡", "🔦", "🕯️", "📡", "🔋", "🔌"] },
    { name: "Transporte", emojis: ["🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐", "🚚", "🚛", "🚜", "🛴", "🚲", "🛵", "🏍️", "🛺", "🚨", "🚔", "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋", "🚞", "🚝", "🚄", "🚅", "🚈", "🚂", "🚆", "🚇", "🚊", "🚉", "✈️", "🛫", "🛬", "🛩️", "💺", "🛰️", "🚀", "🛸", "🚁", "🛶", "⛵", "🚤", "🛥️", "🛳️", "⛴️", "🚢", "⚓", "🪝", "⛽", "🚧", "🚦", "🚥", "🛞"] },
    { name: "Edificios", emojis: ["🏠", "🏡", "🏢", "🏣", "🏤", "🏥", "🏦", "🏨", "🏩", "🏪", "🏫", "🏬", "🏭", "🏯", "🏰", "💒", "🗼", "🗽", "⛪", "🕌", "🛕", "🕍", "⛩️", "🕋", "⛲", "⛺", "🌁", "🌃", "🏙️", "🌄", "🌅", "🌆", "🌇", "🌉", "🎠", "🎡", "🎢", "🗺️", "🧭", "🏗️", "🧱", "🪵", "🛖", "🏚️", "🏘️"] },
    { name: "Deportes", emojis: ["⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱", "🪀", "🏓", "🏸", "🏒", "🏑", "🥍", "🏏", "🥅", "⛳", "🪁", "🏹", "🎣", "🤿", "🥊", "🥋", "🎽", "🛹", "🛷", "⛸️", "🥌", "🎿", "⛷️", "🏂", "🪂", "🏋️‍♂️", "🏋️‍♀️", "🤼‍♂️"] },
    { name: "Naturaleza", emojis: ["🌸", "💮", "🏵️", "🌹", "🥀", "🌺", "🌻", "🌼", "🌷", "🌱", "🪴", "🌲", "🌳", "🌴", "🌵", "🌾", "🌿", "☘️", "🍀", "🍁", "🍂", "🍃", "🍄", "🌰", "🐚", "🌍", "🌎", "🌏", "🌑", "🌒", "🌓", "🌔", "🌕", "🌙", "⭐", "🌟", "✨", "⚡", "🔥", "🌈", "☀️", "🌤️", "⛅", "🌧️", "❄️", "💧", "🌊"] },
    { name: "Animales", emojis: ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🪱", "🐛", "🦋", "🐌", "🐞", "🐜", "🪰", "🪲", "🪳", "🦟", "🦗", "🕷️", "🦂", "🐢", "🐍", "🦎", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍", "🦧", "🐘", "🦛", "🦏"] },
    { name: "Objetos", emojis: ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "🎁", "🎀", "🎈", "🎉", "🎊", "🎃", "🎄", "✉️", "📧", "📨", "📩", "📝", "📋", "📌", "📍", "📎", "🔗", "📏", "📐", "✂️", "🗃️", "🗄️", "🗑️", "🔒", "🔓", "🔑", "🗝️", "🔨", "🪓", "⛏️", "🔧", "🔩", "⚙️", "💰", "💳", "💎", "⚖️", "🧲", "🪜", "🧰", "🧪", "🧫", "🧬", "🔬", "🔭", "📡"] },
    { name: "Símbolos", emojis: ["✅", "❌", "❓", "❗", "‼️", "⁉️", "💯", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤", "🔶", "🔷", "🔸", "🔹", "🔺", "🔻", "🔘", "🔲", "🔳", "⬛", "⬜", "◾", "◽", "▪️", "▫️", "♻️", "☮️", "☯️", "⚕️", "🔰", "💠", "Ⓜ️", "🅿️", "🈳", "🆔", "🆕", "🆗", "🆙", "🆚", "🔝", "🔜", "🔛", "🔙", "🔚"] }
];

/* Legacy emoji array removed */


let currentEmojiTargetCallback = null;

function renderIconPicker(currentIcon, onSelect) {
    // Ya no se usa para renderizar grids fijos, sino para preparar el modal global
    return document.createElement('div'); // dummy para mantener compatibilidad con llamadas existentes si las hay
}

window.toggleEmojiPicker = function (callback) {
    currentEmojiTargetCallback = callback;
    const overlay = document.getElementById('emojiPickerOverlay');
    const searchInput = document.getElementById('emojiSearch');

    if (overlay) {
        overlay.classList.remove('hidden');
        searchInput.value = '';
        renderCategories();
        renderEmojis(EMOJI_CATEGORIES[0].emojis); // Cargar primera categoría por defecto
        searchInput.focus();
    }
}

window.closeEmojiPicker = function () {
    const overlay = document.getElementById('emojiPickerOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
    currentEmojiTargetCallback = null;
}

function renderCategories() {
    const container = document.getElementById('emojiCategories');
    if (!container) return;

    container.innerHTML = '';
    EMOJI_CATEGORIES.forEach((cat, idx) => {
        const span = document.createElement('span');
        span.className = `category-tab ${idx === 0 ? 'active' : ''}`;
        span.innerText = cat.name;
        span.onclick = (e) => {
            document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
            span.classList.add('active');
            renderEmojis(cat.emojis);
        };
        container.appendChild(span);
    });
}

function renderEmojis(emojiList) {
    const content = document.getElementById('emojiPickerContent');
    if (!content) return;

    content.innerHTML = '';
    emojiList.forEach(emoji => {
        const div = document.createElement('div');
        div.className = 'emoji-item';
        div.innerText = emoji;
        div.onclick = () => {
            if (currentEmojiTargetCallback) {
                currentEmojiTargetCallback(emoji);
            }
            closeEmojiPicker();
        };
        content.appendChild(div);
    });
}

window.filterEmojis = function (query) {
    if (!query) {
        const activeTab = document.querySelector('.category-tab.active');
        const catIdx = activeTab ? Array.from(document.querySelectorAll('.category-tab')).indexOf(activeTab) : 0;
        renderEmojis(EMOJI_CATEGORIES[catIdx].emojis);
        return;
    }

    const allEmojis = EMOJI_CATEGORIES.flatMap(c => c.emojis);
    const filtered = allEmojis.filter(emoji => emoji.includes(query));
    renderEmojis(filtered);
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
        const icon = isString ? '' : (opt.icon || '');
        const hasSubmenu = !isString && opt.submenu && opt.submenu.options;
        const isActive = JSON.stringify(currentEditingPath) === JSON.stringify(currentPath);

        const li = document.createElement('li');
        li.className = 'tree-node';

        const div = document.createElement('div');
        div.className = `tree-item ${isActive ? 'active' : ''} ${hasSubmenu ? 'expanded' : ''}`;

        // Icono dependiendo de si tiene submenu o icono personalizado
        let iconHtml = '';
        if (icon) {
            iconHtml = `<span class="tree-custom-icon">${icon}</span>`;
        } else {
            const iconClass = hasSubmenu ? 'fas fa-chevron-right' : 'far fa-circle';
            iconHtml = `<i class="${iconClass} tree-icon"></i>`;
        }

        div.innerHTML = `${iconHtml} ${escapeHtml(title)}`;

        const toggleIcon = div.querySelector('.tree-icon, .tree-custom-icon');

        div.onclick = (e) => {
            currentEditingPath = currentPath;
            renderMenuEditor();
        };

        if (hasSubmenu && toggleIcon) {
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
        
        <div class="form-group welcome-msg-box">
            <div class="editor-section-title"><i class="fas fa-comment-dots"></i> Mensaje de Bienvenida</div>
            <textarea id="menuWelcomeText" class="menu-field-input" rows="2" placeholder="Ej: Hola, bienvenido a..." style="margin-top: 5px; width: 100%; font-size: 0.9rem;">${escapeHtml(currentMenu.text || '')}</textarea>
            <div class="editor-help-text">Este es el primer mensaje que envía el bot junto con el menú principal.</div>
        </div>

        <div class="fallback-box">
            <h5><i class="fas fa-redo-alt"></i> Respuesta de Navegación (Fallback)</h5>
            <textarea id="menuFallbackText" class="menu-field-input" rows="2" placeholder="Ej: No entendí eso. Aquí tienes el menú de nuevo:" style="margin-top: 8px; width: 100%; font-size: 0.85rem;">${escapeHtml(currentMenu.fallback_text || '')}</textarea>
            <div class="editor-help-text">Mensaje que se envía cuando el usuario escribe algo que el bot no reconoce, para guiarlo de vuelta al menú.</div>
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
        </div>
    `;

    const welcomeInput = document.getElementById('menuWelcomeText');
    if (welcomeInput) {
        welcomeInput.oninput = (e) => {
            currentMenu.text = e.target.value;
        };
    }

    const fallbackInput = document.getElementById('menuFallbackText');
    if (fallbackInput) {
        fallbackInput.oninput = (e) => {
            currentMenu.fallback_text = e.target.value;
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
    const icon = isString ? '' : (option.icon || '');
    const response = isString ? '' : (option.response || '');
    const hasSubmenu = !isString && option.submenu && option.submenu.options;

    let contentHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
            <h4 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-edit" style="color: var(--primary);"></i> Editando Opción
            </h4>
            <button type="button" class="btn btn-danger btn-sm" id="btn-delete-option" style="padding: 6px 12px; font-size: 0.8rem; background: rgba(255, 107, 107, 0.1); color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.3);">
                <i class="fas fa-trash"></i> Eliminar
            </button>
        </div>

        <div class="menu-node" style="border: none; background: transparent; padding: 0 !important; box-shadow: none;">
            <div class="form-group" style="margin-bottom: 10px;">
                <label class="menu-field-label">Etiqueta del Botón</label>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div id="selected-icon-display" style="font-size: 1.5rem; background: rgba(255,255,255,0.05); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); min-width: 45px; text-align: center; cursor: pointer;" title="Cambiar Emoji">${icon || '—'}</div>
                    <input type="text" id="editor-node-title" class="menu-field-input" value="${escapeHtml(title)}" placeholder="Servicios, FAQ, Contacto..." style="font-size: 1rem; padding: 10px; flex: 1;">
                </div>
                <div class="editor-help-text" style="margin-top:5px;">El icono a la izquierda aparecerá junto al texto. Haz clic sobre él para cambiarlo.</div>
            </div>
    `;

    if (hasSubmenu) {
        contentHTML += `
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 20px; margin-top: 20px;">
                <div class="editor-section-title"><i class="fas fa-sitemap"></i> Configuración de Sub-menú</div>
                <div class="form-group">
                    <label class="menu-field-label">Texto de Encabezado del Sub-menú</label>
                    <input type="text" id="editor-submenu-text" class="menu-field-input" value="${escapeHtml(option.submenu.text || 'Selecciona una opción:')}" placeholder="Ej: Elige una categoría:">
                    <div class="editor-help-text">Este mensaje se enviará antes de mostrar los botones del sub-menú.</div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; padding: 20px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px;">
                     <p style="font-size: 0.9rem; color: var(--text-muted); margin: 0 0 15px 0;">Actualmente contiene ${option.submenu.options.length} opciones hijas.</p>
                    <button type="button" class="btn btn-primary" id="btn-add-child-option">
                        <i class="fas fa-plus"></i> Añadir Opción Hija
                    </button>
                </div>
            </div>
        `;
    } else {
        contentHTML += `
            <div class="form-group" style="margin-top: 15px;">
                <div class="editor-section-title"><i class="fas fa-comment-dots"></i> Respuesta del Bot</div>
                <textarea id="editor-node-response" class="menu-field-input" rows="5" placeholder="Escribe el mensaje que enviará el bot..." style="font-size: 0.9rem;">${escapeHtml(response)}</textarea>
                <div class="editor-help-text">Si este botón NO es un sub-menú, el bot enviará este texto de respuesta.</div>
            </div>
            
            <div style="margin-top: 30px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 20px; text-align: center;">
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px;">¿Quieres que este botón abra otro listado de opciones?</p>
                <button type="button" class="btn btn-secondary" id="btn-convert-submenu" style="font-size: 0.85rem; width: 100%;">
                    <i class="fas fa-folder-plus"></i> Convertir en Sub-menú
                </button>
            </div>
        `;
    }

    contentHTML += `</div>`;
    panel.innerHTML = contentHTML;

    // Ya no renderizamos el picker estático inline
    /*
    const iconPickerContainer = document.getElementById('icon-picker-container');
    if (iconPickerContainer) {
        const picker = renderIconPicker(icon, (newIcon) => {
            updateMenuValue(path, 'icon', newIcon);
            document.getElementById('selected-icon-display').innerText = newIcon;
            renderMenuTree(); 
        });
        iconPickerContainer.appendChild(picker);
    }
    */

    // === Programmatic Event Listeners (avoid inline onclick quoting issues) ===

    // Emoji picker
    const iconDisplay = document.getElementById('selected-icon-display');
    if (iconDisplay) {
        iconDisplay.addEventListener('click', () => {
            toggleEmojiPicker((emoji) => {
                updateMenuValue(path, 'icon', emoji);
                document.getElementById('selected-icon-display').innerText = emoji;
                renderMenuTree();
            });
        });
    }

    // Delete button
    const deleteBtn = document.getElementById('btn-delete-option');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => removeMenuOption(path));
    }

    // Add child option button (submenu)
    const addChildBtn = document.getElementById('btn-add-child-option');
    if (addChildBtn) {
        addChildBtn.addEventListener('click', () => addMenuOption([...path, 'submenu', 'options']));
    }

    // Convert to submenu button
    const convertBtn = document.getElementById('btn-convert-submenu');
    if (convertBtn) {
        convertBtn.addEventListener('click', () => addSubmenu(path));
    }

    // Listeners
    const titleInput = document.getElementById('editor-node-title');
    if (titleInput) {
        titleInput.oninput = (e) => {
            updateMenuValue(path, 'title', e.target.value);
            renderMenuTree();
        };
    }

    const subTextInput = document.getElementById('editor-submenu-text');
    if (subTextInput) {
        subTextInput.oninput = (e) => {
            updateSubmenuValue(path, 'text', e.target.value);
        };
    }

    const respInput = document.getElementById('editor-node-response');
    if (respInput) {
        respInput.oninput = (e) => {
            updateMenuValue(path, 'response', e.target.value);
        };
    }
}

function updateSubmenuValue(path, key, value) {
    let current = currentMenu.options;
    for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
    }
    const idx = path[path.length - 1];
    if (current[idx] && current[idx].submenu) {
        current[idx].submenu[key] = value;
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
    if (parentPath === null) {
        if (!currentMenu.options) currentMenu.options = [];
        const newOpt = { title: `Opción ${currentMenu.options.length + 1}`, response: '' };
        currentMenu.options.push(newOpt);
        currentEditingPath = [currentMenu.options.length - 1];
    } else {
        // parentPath es algo como [...path, 'submenu', 'options']
        // Navegar hasta el array de options destino
        let current = currentMenu.options;
        for (let i = 0; i < parentPath.length; i++) {
            current = current[parentPath[i]];
        }
        // current ahora es el array de options del submenu
        if (!Array.isArray(current)) current = [];
        const newOpt = { title: `Sub-opción ${current.length + 1}`, response: '' };
        current.push(newOpt);
        // El path al nuevo item: parentPath + índice
        currentEditingPath = [...parentPath, current.length - 1];
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
    const option = current[idx];

    if (typeof option === 'object') {
        // Intentar extraer opciones del texto de respuesta
        const responseText = option.response || '';
        const extractedItems = parseResponseToItems(responseText);

        let subOptions;
        if (extractedItems.length > 0) {
            subOptions = extractedItems.map(item => ({
                title: item,
                response: `Información sobre ${item}.`
            }));
        } else {
            subOptions = [
                { title: "Sub-opción 1", response: "Respuesta de ejemplo para la sub-opción 1." }
            ];
        }

        option.submenu = {
            text: "Selecciona una opción:",
            options: subOptions
        };
        delete option.response; // Quitar respuesta si ahora es submenú
    }

    renderMenuTree();
    renderEditorForm(path);
}

/**
 * Analiza el texto de respuesta del bot y extrae elementos como una lista.
 * Soporta: comas, "y", viñetas, números, saltos de línea.
 * Ejemplo: "Contamos con Medicina General, Odontología y Pediatría." → ["Medicina General", "Odontología", "Pediatría"]
 */
function parseResponseToItems(text) {
    if (!text || text.trim().length === 0) return [];

    // Limpiar texto: remover emojis comunes de lista
    let cleaned = text.replace(/[•\-–—]/g, ',').trim();

    // Intentar separar por saltos de línea primero (si hay múltiples líneas)
    let lines = cleaned.split(/\n/).map(l => l.trim()).filter(l => l.length > 0);

    if (lines.length > 1) {
        // Múltiples líneas — cada línea podría ser un item
        // Remover numeración (1. 2. 3. o 1) 2) etc.)
        let items = lines.map(l => l.replace(/^\d+[\.\)\-]\s*/, '').trim()).filter(l => l.length > 2);
        if (items.length >= 2) return items.slice(0, 10);
    }

    // Una sola línea o pocas — buscar patrones de lista
    // Remover prefijos comunes como "Contamos con", "Ofrecemos", "Tenemos", etc.
    const prefixPatterns = /^(?:contamos\s+con|ofrecemos|tenemos|nuestros?\s+\w+\s+(?:son|incluyen)|disponemos\s+de|entre\s+(?:ellos|ellas)|las?\s+opciones\s+(?:son|incluyen)|(?:estos|estas)\s+son)\s*/i;
    cleaned = cleaned.replace(prefixPatterns, '');

    // Remover puntos finales y caracteres sobrantes
    cleaned = cleaned.replace(/\.\s*$/, '').trim();

    // Separar por comas y "y" / "e"
    // Patrón: "A, B, C y D" o "A, B y C"
    let items = cleaned.split(/\s*,\s*/);

    // El último elemento podría tener " y " o " e "
    if (items.length > 0) {
        const lastItem = items[items.length - 1];
        const andSplit = lastItem.split(/\s+(?:y|e)\s+/i);
        if (andSplit.length > 1) {
            items.pop();
            items.push(...andSplit);
        }
    }

    // Limpiar cada item
    items = items.map(item => item.trim()).filter(item => item.length > 1 && item.length < 80);

    // Solo devolver si encontramos al menos 2 items razonables
    if (items.length >= 2) return items.slice(0, 10);

    return [];
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
