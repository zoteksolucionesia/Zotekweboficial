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

    function getToken() {
        return new URLSearchParams(window.location.search).get('t');
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
    }

    function renderError(msg) {
        document.getElementById('content').innerHTML = `
            <div class="error-state">
                <div class="icon">🔍</div>
                <h1 style="font-size:1.2rem;margin-bottom:0.5rem;">Cita no encontrada</h1>
                <p>${msg}</p>
            </div>`;
    }

    async function load() {
        const token = getToken();
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

    load();
})();
