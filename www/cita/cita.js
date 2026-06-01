(function () {
    const API = 'https://zotek-ia.web.app';

    const DAYS_ES = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
    const MONTHS_ES = ['enero','febrero','marzo','abril','mayo','junio',
                       'julio','agosto','septiembre','octubre','noviembre','diciembre'];

    const STATUS_LABELS = {
        pending:   { text: 'Pendiente',  cls: 'badge-pending'   },
        confirmed: { text: 'Confirmada', cls: 'badge-confirmed' },
        cancelled: { text: 'Cancelada',  cls: 'badge-cancelled' },
        completed: { text: 'Completada', cls: 'badge-completed' },
    };

    let currentToken = null;

    function getToken() {
        const rawToken = new URLSearchParams(window.location.search).get('t');
        if (!rawToken) return null;
        
        // Si el WABA concatena el sufijo y nos da un parámetro como "{TOKEN}cita?t=UUID"
        if (rawToken.includes('t=')) {
            const parts = rawToken.split('t=');
            return parts[parts.length - 1];
        }
        
        // Remover el literal "{TOKEN}" o "%7BTOKEN%7D" si quedó pegado al inicio
        return rawToken.replace(/^\{TOKEN\}/i, '').replace(/^%7BTOKEN%7D/i, '');
    }

    function formatDate(isoStr) {
        const d = new Date(isoStr);
        const day   = DAYS_ES[d.getDay()];
        const date  = d.getDate();
        const month = MONTHS_ES[d.getMonth()];
        const year  = d.getFullYear();
        return `${day}, ${date} de ${month} de ${year}`;
    }

    function formatTime(isoStr) {
        const d = new Date(isoStr);
        return d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: true });
    }

    function row(icon, label, value) {
        return `
            <div class="detail-row">
                <span class="detail-icon">${icon}</span>
                <div>
                    <div class="detail-label">${label}</div>
                    <div class="detail-value">${value}</div>
                </div>
            </div>`;
    }

    function renderAppointment(apt) {
        const status  = STATUS_LABELS[apt.status] || { text: apt.status, cls: 'badge-pending' };
        const name    = apt.name || '—';
        const phone   = apt.phone || '—';
        const dateStr = formatDate(apt.date_time);
        const timeStr = formatTime(apt.date_time);
        const notes   = apt.notes || '';

        let html = `
            <span class="badge ${status.cls}">${status.text}</span>
            <h1>Detalles de tu Cita</h1>
            <p class="business-name">${apt.business_name || ''}</p>
            ${row('📅', 'Fecha', dateStr)}
            ${row('🕐', 'Hora', timeStr)}
            ${row('👤', 'Nombre', name)}
            ${row('📱', 'Teléfono', phone)}
        `;
        if (notes) html += row('📝', 'Notas', notes);

        document.getElementById('content').innerHTML = html;
        document.title = `Cita — ${apt.business_name || 'Zotek IA'}`;

        // Botón de cancelar solo si la cita está activa
        const actionsEl = document.getElementById('actions');
        if (apt.status === 'pending' || apt.status === 'confirmed') {
            actionsEl.innerHTML = `<button class="btn-cancel" id="btn-cancel">Cancelar esta cita</button>`;
            document.getElementById('btn-cancel').addEventListener('click', openModal);
        } else {
            actionsEl.innerHTML = '';
        }
    }

    function renderError(msg) {
        document.getElementById('content').innerHTML = `
            <div class="error-state">
                <div class="icon">🔍</div>
                <h1 style="font-size:1.2rem;margin-bottom:0.5rem;">Cita no encontrada</h1>
                <p>${msg}</p>
            </div>`;
        document.getElementById('actions').innerHTML = '';
    }

    function openModal() {
        document.getElementById('modal-overlay').classList.add('active');
    }

    function closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    }

    function showToast(msg, isError) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.toggle('error', !!isError);
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    async function confirmCancel() {
        const btn = document.getElementById('modal-confirm');
        btn.disabled = true;
        btn.textContent = 'Cancelando...';
        try {
            const res = await fetch(`${API}/api/appointments/token/${encodeURIComponent(currentToken)}/cancel`, {
                method: 'POST',
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `HTTP ${res.status}`);
            }
            closeModal();
            showToast('Cita cancelada correctamente');
            // Recargar detalles para reflejar el nuevo estado
            await load();
        } catch (e) {
            showToast(e.message || 'Error al cancelar la cita', true);
            btn.disabled = false;
            btn.textContent = 'Sí, cancelar';
            console.error(e);
        }
    }

    async function load() {
        const token = getToken();
        currentToken = token;
        if (!token) {
            renderError('El enlace no contiene un identificador de cita válido.');
            return;
        }

        try {
            const res = await fetch(`${API}/api/appointments/token/${encodeURIComponent(token)}`);
            if (res.status === 404) {
                renderError('No encontramos ninguna cita con este enlace. Es posible que haya sido cancelada o el enlace sea incorrecto.');
                return;
            }
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const apt = await res.json();
            renderAppointment(apt);
        } catch (e) {
            renderError('Ocurrió un error al cargar la información. Intenta de nuevo más tarde.');
            console.error(e);
        }
    }

    // Wire up modal buttons (always present in DOM)
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('modal-cancel').addEventListener('click', closeModal);
        document.getElementById('modal-confirm').addEventListener('click', confirmCancel);
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') closeModal();
        });
        load();
    });
})();
