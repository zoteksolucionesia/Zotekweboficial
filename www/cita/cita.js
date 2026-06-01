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

    function formatShortDate(isoStr) {
        const d = new Date(isoStr);
        const monthsEs = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
        const date = d.getDate();
        const month = monthsEs[d.getMonth()];
        const year = d.getFullYear();
        const time = d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: false });
        return `${date} ${month} ${year} • ${time}`;
    }

    function formatLongDate(isoStr) {
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

    function formatUTCForCalendar(date) {
        return date.toISOString().replace(/-|:|\.\d\d\d/g, "");
    }

    function renderAppointment(apt) {
        const status  = STATUS_LABELS[apt.status] || { text: apt.status, cls: 'badge-pending' };
        const clientName = apt.name || '';
        const firstName = clientName.split(' ')[0];
        
        // 1. Welcome Title
        if (firstName) {
            document.getElementById('welcome-title').textContent = `Hola ${firstName}, estos son los detalles de tu cita`;
        } else {
            document.getElementById('welcome-title').textContent = `Estos son los detalles de tu cita`;
        }
        
        // 2. Reservation Header
        document.getElementById('apt-reserva-id').textContent = `RESERVA ${apt.id || ''}`;
        document.getElementById('apt-datetime-main').textContent = formatShortDate(apt.date_time);
        
        // 3. Action Buttons in Banner
        const startDate = new Date(apt.date_time);
        const endDate = new Date(startDate.getTime() + 50 * 60 * 1000); // Duración por defecto: 50 mins
        const startCalStr = formatUTCForCalendar(startDate);
        const endCalStr = formatUTCForCalendar(endDate);
        const calendarTitle = `Cita con ${apt.business_name || 'Zotek IA'}`;
        const calendarDetails = `Cita de seguimiento agendada en Zotek IA.`;
        const calendarLocation = apt.business_address || '';
        
        const gCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(calendarTitle)}&dates=${startCalStr}/${endCalStr}&details=${encodeURIComponent(calendarDetails)}&location=${encodeURIComponent(calendarLocation)}`;
        
        const rescheduleUrl = apt.calendly_url || apt.business_whatsapp || "#";
        
        document.getElementById('apt-banner-actions').innerHTML = `
            <a href="${gCalUrl}" target="_blank" class="btn-banner-link">
                <svg viewBox="0 0 24 24"><path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z"/></svg>
                Agregar a Google Calendar
            </a>
            <a href="${rescheduleUrl}" target="_blank" class="btn-banner-link">
                <svg viewBox="0 0 24 24"><path d="M19 4H5c-1.11 0-2 .9-2 2v12c0 1.1.89 2 2 2h4v-2H5V8h14v10h-4v2h4c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-7 6l-4 4h3v6h2v-6h3l-4-4z"/></svg>
                Reagendar
            </a>
        `;

        // 4. Cancel Button in Body (only if active)
        const cancelWrapper = document.getElementById('btn-cancel-wrapper');
        if (apt.status === 'pending' || apt.status === 'confirmed') {
            cancelWrapper.innerHTML = `
                <button class="btn-cancel" id="btn-cancel">
                    <svg style="width: 14px; height: 14px; fill: currentColor;" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    Cancelar Cita
                </button>`;
            document.getElementById('btn-cancel').addEventListener('click', openModal);
        } else {
            cancelWrapper.innerHTML = `<span class="badge ${status.cls}">${status.text}</span>`;
        }

        // 5. Service Details Row
        const serviceName = (apt.notes && apt.notes.length < 40) ? apt.notes : 'Consulta General';
        document.getElementById('service-title').textContent = serviceName;
        document.getElementById('service-meta').textContent = `${formatTime(apt.date_time)} • 50 min`;
        document.getElementById('service-provider').textContent = apt.business_name || '';
        document.getElementById('service-price').textContent = '$700.00 MXN';

        // 6. Payment Summary
        document.getElementById('total-amount').textContent = '$700.00 MXN';
        const paymentBadge = document.getElementById('payment-status');
        if (apt.status === 'cancelled') {
            paymentBadge.textContent = 'CITA CANCELADA';
            paymentBadge.style.color = '#ef4444';
        } else if (apt.status === 'completed') {
            paymentBadge.textContent = 'CITA REALIZADA Y PAGADA';
            paymentBadge.style.color = '#10b981';
        } else {
            paymentBadge.textContent = 'PAGO TOTAL PENDIENTE';
            paymentBadge.style.color = '#ef4444';
        }

        // 7. Right Column: Business Profile
        const names = (apt.business_name || 'Zotek IA').split(' ');
        const initials = names.map(n => n[0]).join('').slice(0, 2).toUpperCase();
        document.getElementById('biz-avatar').textContent = initials;
        document.getElementById('biz-name').textContent = apt.business_name || '';
        document.getElementById('biz-subtitle').textContent = apt.business_subtitle || 'Profesional';

        // 8. Contact email
        const emailEl = document.getElementById('biz-email');
        if (apt.business_email) {
            emailEl.innerHTML = `<a href="mailto:${apt.business_email}">${apt.business_email}</a>`;
            document.getElementById('biz-email-item').style.display = 'flex';
        } else {
            document.getElementById('biz-email-item').style.display = 'none';
        }

        // 9. Address & Maps
        const addressEl = document.getElementById('biz-address');
        const mapWrapper = document.getElementById('map-wrapper');
        const mapLinkWrapper = document.getElementById('biz-map-link-wrapper');
        
        if (apt.business_address) {
            addressEl.textContent = apt.business_address;
            document.getElementById('biz-address-item').style.display = 'flex';
            
            // Render Map Iframe
            const encodedAddress = encodeURIComponent(apt.business_address);
            mapWrapper.style.display = 'block';
            mapWrapper.innerHTML = `<iframe src="https://maps.google.com/maps?q=${encodedAddress}&t=&z=15&ie=UTF8&iwloc=&output=embed" allowfullscreen="" loading="lazy"></iframe>`;
            
            // "Ver la ubicación" link
            mapLinkWrapper.innerHTML = `
                <a href="https://maps.google.com/?q=${encodedAddress}" target="_blank" style="display:inline-flex;align-items:center;gap:0.25rem;">
                    <svg style="width:14px;height:14px;fill:currentColor;" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                    Ver la ubicación
                </a>
            `;
        } else {
            document.getElementById('biz-address-item').style.display = 'none';
            mapWrapper.style.display = 'none';
            mapLinkWrapper.innerHTML = '';
        }

        // 10. WhatsApp Button
        const waWrapper = document.getElementById('biz-whatsapp-wrapper');
        if (apt.business_whatsapp) {
            waWrapper.innerHTML = `
                <a href="${apt.business_whatsapp}" target="_blank" class="btn-whatsapp-block">
                    <svg viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.062 5.296 5.358 0 11.871 0c3.156.001 6.123 1.23 8.354 3.463 2.23 2.233 3.456 5.203 3.456 8.361 0 6.574-5.298 11.87-11.81 11.87-2.002-.001-3.969-.51-5.753-1.48L0 24zm6.59-4.846c1.7.994 3.39 1.517 5.275 1.518 5.43 0 9.85-4.398 9.85-9.805a9.71 9.71 0 0 0-2.88-6.932 9.68 9.68 0 0 0-6.963-2.88c-5.433 0-9.855 4.398-9.855 9.806 0 1.936.518 3.513 1.5 5.23L2.457 21.05l4.19-1.896zm12.338-7.558c-.3-.15-1.782-.88-2.062-.982-.28-.102-.483-.153-.687.153-.203.305-.788.982-.966 1.186-.178.204-.356.229-.657.079-.3-.15-1.266-.467-2.41-1.485-.89-.795-1.492-1.775-1.668-2.079-.177-.305-.019-.47.132-.62.136-.134.3-.35.45-.524.152-.175.203-.3.305-.5.102-.2.05-.375-.025-.526-.075-.15-.687-1.657-.942-2.272-.247-.6-.5-.519-.687-.529-.177-.008-.38-.01-.584-.01-.203 0-.534.077-.814.381-.28.305-1.067 1.042-1.067 2.54 0 1.498 1.092 2.946 1.244 3.15.153.204 2.148 3.28 5.206 4.6.727.313 1.294.5 1.737.64.73.232 1.396.199 1.922.12.586-.087 1.782-.728 2.036-1.43.254-.702.254-1.303.178-1.43-.077-.127-.28-.203-.58-.353z"/></svg>
                    Contactar por WhatsApp
                </a>
            `;
        } else {
            waWrapper.innerHTML = '';
        }

        document.title = `Cita — ${apt.business_name || 'Zotek IA'}`;
    }

    function renderError(msg) {
        document.getElementById('welcome-title').textContent = "Error";
        
        // Hide standard grid and display detailed error message
        const grid = document.querySelector('.appointment-grid');
        if (grid) grid.style.display = 'none';
        
        let errContainer = document.getElementById('error-container');
        errContainer.innerHTML = `
            <div class="card error-state">
                <div class="error-icon">🔍</div>
                <h2>Cita no encontrada</h2>
                <p>${msg}</p>
                <a href="https://zotek-ia.web.app" class="btn-retry">Ir al portal</a>
            </div>
        `;
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
            
            // Make sure layout grid is visible if it was hidden by previous errors
            const grid = document.querySelector('.appointment-grid');
            if (grid) grid.style.display = 'grid';
            document.getElementById('error-container').innerHTML = '';
            
            renderAppointment(apt);
        } catch (e) {
            renderError('Ocurrió un error al cargar la información. Intenta de nuevo más tarde.');
            console.error(e);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('modal-cancel').addEventListener('click', closeModal);
        document.getElementById('modal-confirm').addEventListener('click', confirmCancel);
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') closeModal();
        });
        load();
    });
})();
