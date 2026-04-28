'use strict';

const API        = '';
const TOKEN_KEY  = 'zotek_portal_token';
const CLIENT_KEY = 'zotek_portal_client';
const THEME_KEY  = 'zotek_portal_theme';

// ——— Estado global ————————————————————————————————————————————————
let authToken  = localStorage.getItem(TOKEN_KEY)  || null;
let clientData = JSON.parse(localStorage.getItem(CLIENT_KEY) || 'null');
let allCitas   = [];
let allLeads   = [];

let chatSessionId = newUUID();
let chatLoading   = false;
let chatGreeted   = false;

// Estado de cambios en "Probar Agente"
let originalInstruction = '';
let pendingChanges      = false;

// ===========================================
// UTILS
// ===========================================
function newUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

function authHeader() {
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` };
}

function showToast(msg, type = 'info') {
  const t = document.getElementById('portal-toast');
  t.textContent = msg;
  t.className = `portal-toast toast-${type}`;
  t.style.display = 'block';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = 'none'; }, 3500);
}

function setLoading(btnId, spinId, loading) {
  const btn  = document.getElementById(btnId);
  const spin = document.getElementById(spinId);
  if (btn)  btn.disabled = loading;
  if (spin) spin.style.display = loading ? 'inline-block' : 'none';
}

// ===========================================
// TEMA CLARO / OSCURO
// ===========================================
const THEME_ICONS = { dark: 'fa-sun', light: 'fa-moon' };

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
  ['login', 'sidebar', 'mobile'].forEach(id => {
    const el = document.getElementById(`theme-icon-${id}`);
    if (!el) return;
    el.className = `fas ${THEME_ICONS[theme]}`;
  });
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// Inicializar tema desde localStorage
applyTheme(localStorage.getItem(THEME_KEY) || 'dark');

document.getElementById('btn-theme-login')?.addEventListener('click', toggleTheme);
document.getElementById('btn-theme-sidebar')?.addEventListener('click', toggleTheme);
document.getElementById('btn-theme-mobile')?.addEventListener('click', toggleTheme);

// ===========================================
// AUTH — LOGIN
// ===========================================
const stepEmail = document.getElementById('step-email');
const stepCode  = document.getElementById('step-code');

document.getElementById('btn-send-code').addEventListener('click', requestCode);
document.getElementById('inp-email').addEventListener('keydown', e => { if (e.key === 'Enter') requestCode(); });
document.getElementById('btn-verify-code').addEventListener('click', verifyCode);
document.getElementById('inp-code').addEventListener('keydown', e => { if (e.key === 'Enter') verifyCode(); });
document.getElementById('btn-resend').addEventListener('click', () => {
  stepCode.style.display = 'none';
  stepEmail.style.display = '';
  requestCode();
});

async function requestCode() {
  const email = document.getElementById('inp-email').value.trim();
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';
  if (!email) { errEl.textContent = 'Ingresa tu email.'; errEl.style.display = 'block'; return; }

  setLoading('btn-send-code', 'btn-send-spin', true);
  document.getElementById('btn-send-text').textContent = 'Enviando...';

  try {
    const res  = await fetch(`${API}/api/auth/request-code`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }),
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || 'Error enviando código.'; errEl.style.display = 'block';
    } else {
      document.getElementById('sent-to-email').textContent = email;
      stepEmail.style.display = 'none';
      stepCode.style.display  = '';
      setTimeout(() => document.getElementById('inp-code').focus(), 100);
    }
  } catch {
    errEl.textContent = 'Error de conexión. Intenta de nuevo.'; errEl.style.display = 'block';
  } finally {
    setLoading('btn-send-code', 'btn-send-spin', false);
    document.getElementById('btn-send-text').textContent = 'Enviar código';
  }
}

async function verifyCode() {
  const email = document.getElementById('inp-email').value.trim();
  const code  = document.getElementById('inp-code').value.trim();
  const errEl = document.getElementById('code-error');
  errEl.style.display = 'none';
  if (!code || code.length < 6) { errEl.textContent = 'Ingresa el código de 6 dígitos.'; errEl.style.display = 'block'; return; }

  setLoading('btn-verify-code', 'btn-verify-spin', true);
  document.getElementById('btn-verify-text').textContent = 'Verificando...';

  try {
    const res  = await fetch(`${API}/api/auth/verify-code`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code }),
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || 'Código incorrecto.'; errEl.style.display = 'block';
    } else {
      authToken  = data.access_token;
      clientData = { id: data.client_id, name: data.client_name, email };
      localStorage.setItem(TOKEN_KEY,  authToken);
      localStorage.setItem(CLIENT_KEY, JSON.stringify(clientData));
      showDashboard();
    }
  } catch {
    errEl.textContent = 'Error de conexión. Intenta de nuevo.'; errEl.style.display = 'block';
  } finally {
    setLoading('btn-verify-code', 'btn-verify-spin', false);
    document.getElementById('btn-verify-text').textContent = 'Ingresar';
  }
}

// ===========================================
// LOGOUT
// ===========================================
function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(CLIENT_KEY);
  authToken = null; clientData = null;
  document.getElementById('screen-dashboard').style.display = 'none';
  document.getElementById('screen-login').style.display     = '';
  stepCode.style.display  = 'none';
  stepEmail.style.display = '';
  document.getElementById('inp-email').value = '';
  document.getElementById('inp-code').value  = '';
}
document.getElementById('btn-logout').addEventListener('click', logout);
document.getElementById('btn-logout-mobile').addEventListener('click', logout);

// ===========================================
// NAVEGACI├ôN
// ===========================================
const SECTION_TITLES = { resumen: 'Resumen', citas: 'Citas', leads: 'Leads', horarios: 'Horarios', probar: 'Probar Agente' };

document.querySelectorAll('.nav-item').forEach(link => {
  link.addEventListener('click', e => { e.preventDefault(); switchSection(link.dataset.section); });
});
document.querySelectorAll('a.btn-link[data-section]').forEach(el => {
  el.addEventListener('click', e => { e.preventDefault(); switchSection(el.dataset.section); });
});

function switchSection(name) {
  document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
  const sec = document.getElementById(`section-${name}`);
  if (sec) sec.style.display = '';
  const navItem = document.querySelector(`.nav-item[data-section="${name}"]`);
  if (navItem) navItem.classList.add('active');
  document.getElementById('mobile-section-title').textContent = SECTION_TITLES[name] || name;
  document.querySelector('.sidebar')?.classList.remove('open');

  if (name === 'citas')    renderCitasTable();
  if (name === 'leads')    renderLeadsTable();
  if (name === 'horarios') initHorariosSection();
  if (name === 'probar')   initProbarSection();
}

document.getElementById('btn-menu-toggle').addEventListener('click', () => {
  document.querySelector('.sidebar').classList.toggle('open');
});

// ===========================================
// DASHBOARD
// ===========================================
async function showDashboard() {
  document.getElementById('screen-login').style.display     = 'none';
  document.getElementById('screen-dashboard').style.display = '';

  const name  = clientData?.name  || '—';
  const email = clientData?.email || '—';
  document.getElementById('sidebar-client-name').textContent  = name;
  document.getElementById('sidebar-client-email').textContent = email;
  document.getElementById('user-avatar-initial').textContent  = name.charAt(0).toUpperCase();
  document.getElementById('chat-avatar-initial').textContent  = name.charAt(0).toUpperCase();
  document.getElementById('chat-bot-name').textContent        = name;

  const hour     = new Date().getHours();
  const greeting = hour < 12 ? 'Buenos días' : hour < 19 ? 'Buenas tardes' : 'Buenas noches';
  document.getElementById('resumen-greeting').textContent = `${greeting}, ${name.split(' ')[0]}`;

  await loadDashboardData();
}

async function loadDashboardData() {
  if (!clientData?.id) return;
  const cid = clientData.id;
  try {
    const [citasRes, leadsRes] = await Promise.all([
      fetch(`${API}/api/clients/${cid}/appointments`, { headers: authHeader() }),
      fetch(`${API}/api/clients/${cid}/leads?limit=200`,  { headers: authHeader() }),
    ]);
    console.log('[PORTAL] citasRes status:', citasRes.status, 'leadsRes status:', leadsRes.status);
    if (citasRes.ok) {
      const data = await citasRes.json();
      console.log('[PORTAL] citas raw:', JSON.stringify(data).substring(0, 300));
      allCitas = Array.isArray(data) ? data : (data.appointments || data.citas || []);
      console.log('[PORTAL] allCitas count:', allCitas.length);
      updateCitasKPIs(); renderProximasCitas();
    } else {
      console.error('[PORTAL] citas error:', await citasRes.text());
    }
    if (leadsRes.ok) {
      const data = await leadsRes.json();
      console.log('[PORTAL] leads raw:', JSON.stringify(data).substring(0, 300));
      allLeads = data.leads || [];
      console.log('[PORTAL] allLeads count:', allLeads.length);
      updateLeadsKPIs(); renderLeadsRecientes();
    } else {
      console.error('[PORTAL] leads error:', await leadsRes.text());
    }
  } catch (e) { console.error('Error cargando dashboard:', e); }
}

// ===========================================
// KPIs
// ===========================================
function updateCitasKPIs() {
  const today = new Date().toISOString().slice(0, 10);
  const wStart = getWeekStart();
  const wEnd   = new Date(wStart); wEnd.setDate(wEnd.getDate() + 7);
  const hoy    = allCitas.filter(c => (c.fecha_hora || c.appointment_date || '').startsWith(today)).length;
  const semana = allCitas.filter(c => { const d = new Date(c.fecha_hora || c.appointment_date || ''); return d >= wStart && d < wEnd; }).length;
  document.getElementById('kpi-hoy').textContent    = hoy;
  document.getElementById('kpi-semana').textContent = semana;
}

function updateLeadsKPIs() {
  document.getElementById('kpi-leads-total').textContent  = allLeads.length;
  document.getElementById('kpi-leads-nuevos').textContent = allLeads.filter(l => l.status === 'nuevo' || l.status === 'new').length;
}

function getWeekStart() {
  const d = new Date(); d.setHours(0,0,0,0);
  const day = d.getDay();
  d.setDate(d.getDate() - (day === 0 ? 6 : day - 1));
  return d;
}

// ===========================================
// TABLAS — RESUMEN
// ===========================================
function renderProximasCitas() {
  const container = document.getElementById('proximas-citas-list');
  // fecha_hora se guarda como texto ("Jue 9 Abr 10:00"), ordenar por created_at
  const proximas = [...allCitas]
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    .slice(0, 5);

  if (!proximas.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-xmark"></i><p>No hay citas registradas</p></div>'; return;
  }
  container.innerHTML = `<table class="data-table"><thead><tr><th>Paciente</th><th>Fecha y hora</th><th>Estado</th></tr></thead><tbody>
    ${proximas.map(c => `<tr>
      <td>${escHtml(c.paciente_nombre || c.customer_name || '—')}</td>
      <td>${escHtml(c.fecha_hora || c.appointment_date || '—')}</td>
      <td>${statusBadge(c.status || 'pendiente')}</td>
    </tr>`).join('')}</tbody></table>`;
}

function renderLeadsRecientes() {
  const container = document.getElementById('leads-recientes-list');
  const recientes = [...allLeads]
    .sort((a, b) => new Date(b.last_interaction || b.created_at) - new Date(a.last_interaction || a.created_at))
    .slice(0, 5);

  if (!recientes.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-users"></i><p>Aún no hay leads registrados</p></div>'; return;
  }
  container.innerHTML = `<table class="data-table"><thead><tr><th>Nombre / Teléfono</th><th>Fuente</th><th>Estado</th><th>Última interacción</th></tr></thead><tbody>
    ${recientes.map(l => `<tr>
      <td><div>${escHtml(l.customer_name || l.phone_number || '—')}</div><div class="text-muted text-sm">${escHtml(l.phone_number || '')}</div></td>
      <td>${sourceBadge(l.source)}</td>
      <td>${leadStatusBadge(l.status)}</td>
      <td class="text-muted text-sm">${formatDateTime(l.last_interaction || l.created_at)}</td>
    </tr>`).join('')}</tbody></table>`;
}

// ===========================================
// TABLA CITAS
// ===========================================
function renderCitasTable() {
  const container    = document.getElementById('citas-table-wrap');
  const filterStatus = document.getElementById('filter-citas-status').value;
  let citas = [...allCitas];
  if (filterStatus) citas = citas.filter(c => (c.status || 'pendiente') === filterStatus);
  citas.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

  if (!citas.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-xmark"></i><p>No hay citas</p></div>'; return;
  }
  container.innerHTML = `<table class="data-table"><thead><tr><th>Paciente</th><th>Teléfono</th><th>Fecha y hora</th><th>Motivo</th><th>Estado</th></tr></thead><tbody>
    ${citas.map(c => `<tr>
      <td>${escHtml(c.paciente_nombre || c.customer_name || '—')}</td>
      <td class="text-muted">${escHtml(c.cliente_telefono || c.phone_number || '—')}</td>
      <td>${escHtml(c.fecha_hora || c.appointment_date || '—')}</td>
      <td class="text-muted">${escHtml(c.motivo || c.notes || '—')}</td>
      <td>${statusBadge(c.status || 'pendiente')}</td>
    </tr>`).join('')}</tbody></table>`;
}
document.getElementById('filter-citas-status').addEventListener('change', renderCitasTable);

// ===========================================
// TABLA LEADS
// ===========================================
function renderLeadsTable() {
  const container    = document.getElementById('leads-table-wrap');
  const filterSource = document.getElementById('filter-leads-source').value;
  const filterStatus = document.getElementById('filter-leads-status').value;
  let leads = [...allLeads];
  if (filterSource) leads = leads.filter(l => l.source === filterSource);
  if (filterStatus) leads = leads.filter(l => l.status === filterStatus);
  leads.sort((a, b) => new Date(b.last_interaction || b.created_at) - new Date(a.last_interaction || a.created_at));

  if (!leads.length) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-users"></i><p>No hay leads con ese filtro</p></div>'; return;
  }
  container.innerHTML = `<table class="data-table"><thead><tr><th>Nombre</th><th>Teléfono</th><th>Email</th><th>Fuente</th><th>Estado</th><th>Última interacción</th></tr></thead><tbody>
    ${leads.map(l => `<tr>
      <td>${escHtml(l.customer_name || '—')}</td>
      <td class="text-muted">${escHtml(l.phone_number || '—')}</td>
      <td class="text-muted">${escHtml(l.customer_email || '—')}</td>
      <td>${sourceBadge(l.source)}</td>
      <td>${leadStatusBadge(l.status)}</td>
      <td class="text-muted text-sm">${formatDateTime(l.last_interaction || l.created_at)}</td>
    </tr>`).join('')}</tbody></table>`;
}
document.getElementById('filter-leads-source').addEventListener('change', renderLeadsTable);
document.getElementById('filter-leads-status').addEventListener('change', renderLeadsTable);

// ===========================================
// PROBAR AGENTE — Configuración del agente
// ===========================================
let agentConfigLoaded = false;

async function initProbarSection() {
  if (!agentConfigLoaded) await loadAgentConfig();
  if (!chatGreeted) initChat();
}

async function loadAgentConfig() {
  if (!clientData?.id) return;
  try {
    const [clientRes, docsRes] = await Promise.all([
      fetch(`${API}/api/clients/${clientData.id}`, { headers: authHeader() }),
      fetch(`${API}/api/clients/${clientData.id}/documents`, { headers: authHeader() }),
    ]);

    if (clientRes.ok) {
      const client = await clientRes.json();
      const sysInst = client.system_instruction || '';
      document.getElementById('agent-system-instruction').value = sysInst;
      originalInstruction = sysInst;
    }

    if (docsRes.ok) {
      const docsData = await docsRes.json();
      renderDocsList(Array.isArray(docsData) ? docsData : (docsData.documents || []));
    }

    agentConfigLoaded = true;
  } catch (e) { console.error('Error cargando config del agente:', e); }
}

function renderDocsList(docs) {
  const container = document.getElementById('docs-list');
  if (!docs.length) {
    container.innerHTML = '<div class="empty-state-sm"><i class="fas fa-file-circle-xmark" style="color:var(--text-muted)"></i> Sin documentos. Sube un PDF para mejorar las respuestas del bot.</div>';
    return;
  }
  container.innerHTML = docs.map(d => `
    <div class="doc-item">
      <i class="fas fa-file-pdf doc-item-icon"></i>
      <span class="doc-item-name" title="${escHtml(d.source_file || d.id)}">${escHtml(d.source_file || `Documento ${d.id}`)}</span>
      <button class="doc-item-del" data-id="${d.id}" title="Eliminar documento">
        <i class="fas fa-trash-can"></i>
      </button>
    </div>`).join('');

  container.querySelectorAll('.doc-item-del').forEach(btn => {
    btn.addEventListener('click', () => deleteDoc(parseInt(btn.dataset.id)));
  });
}

// Track cambios en system instruction
document.getElementById('agent-system-instruction').addEventListener('input', function () {
  const changed = this.value !== originalInstruction;
  setPendingChanges(changed);
});

// Guardar instrucción
document.getElementById('btn-save-instruction').addEventListener('click', async () => {
  if (!clientData?.id) return;
  const text = document.getElementById('agent-system-instruction').value;
  const btn  = document.getElementById('btn-save-instruction');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}`, {
      method: 'PUT',
      headers: authHeader(),
      body: JSON.stringify({ system_instruction: text }),
    });
    if (res.ok) {
      originalInstruction = text;
      setPendingChanges(false);
      showToast('Instrucción guardada', 'success');
    } else {
      showToast('Error al guardar', 'error');
    }
  } catch { showToast('Error de conexión', 'error'); }
  finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-floppy-disk"></i> Guardar instrucción';
  }
});

// Upload PDF
document.getElementById('btn-upload-trigger').addEventListener('click', () => {
  document.getElementById('doc-file-input').click();
});

document.getElementById('doc-file-input').addEventListener('change', async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = '';

  const btn      = document.getElementById('btn-upload-trigger');
  const btnText  = document.getElementById('upload-btn-text');
  btn.disabled   = true;
  btnText.textContent = 'Subiendo...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}/upload-pdf`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${authToken}` },
      body: formData,
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`PDF subido: ${data.pages} páginas`, 'success');
      setPendingChanges(true);
      // Recargar lista de docs
      const docsRes = await fetch(`${API}/api/clients/${clientData.id}/documents`, { headers: authHeader() });
      if (docsRes.ok) {
        const docsData = await docsRes.json();
        renderDocsList(Array.isArray(docsData) ? docsData : (docsData.documents || []));
      }
    } else {
      showToast(data.detail || 'Error al subir PDF', 'error');
    }
  } catch { showToast('Error de conexión', 'error'); }
  finally {
    btn.disabled  = false;
    btnText.textContent = 'Subir PDF';
  }
});

async function deleteDoc(docId) {
  if (!confirm('¿Eliminar este documento del bot?')) return;
  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}/documents/${docId}`, {
      method: 'DELETE', headers: authHeader(),
    });
    if (res.ok) {
      showToast('Documento eliminado', 'success');
      setPendingChanges(true);
      const docsRes = await fetch(`${API}/api/clients/${clientData.id}/documents`, { headers: authHeader() });
      if (docsRes.ok) {
        const docsData = await docsRes.json();
        renderDocsList(Array.isArray(docsData) ? docsData : (docsData.documents || []));
      }
    } else { showToast('Error al eliminar', 'error'); }
  } catch { showToast('Error de conexión', 'error'); }
}

// Banner de cambios pendientes
function setPendingChanges(hasChanges) {
  pendingChanges = hasChanges;
  document.getElementById('reset-bot-banner').style.display = hasChanges ? 'flex' : 'none';
}

// Reiniciar bot (nueva sesión de chat)
document.getElementById('btn-reset-bot').addEventListener('click', resetChat);

// ===========================================
// CHAT (Probar Agente)
// ===========================================
function initChat() {
  chatGreeted = true;
  // El usuario inicia la conversación libremente
}

function scrollChatBottom() {
  const msgs = document.getElementById('chat-msgs');
  requestAnimationFrame(() => { msgs.scrollTop = msgs.scrollHeight; });
}

function addChatMsg(text, role, type) {
  const msgs = document.getElementById('chat-msgs');
  const div  = document.createElement('div');
  div.className   = type === 'confirmed' ? 'chat-msg confirmed' : `chat-msg ${role}`;
  div.textContent = text;
  msgs.appendChild(div);
  scrollChatBottom();
  return div;
}

function showChatTyping() {
  const msgs = document.getElementById('chat-msgs');
  const div  = document.createElement('div');
  div.id = 'chat-typing'; div.className = 'chat-msg bot typing';
  div.innerHTML = '<span></span><span></span><span></span>';
  msgs.appendChild(div); scrollChatBottom();
}
function hideChatTyping() { document.getElementById('chat-typing')?.remove(); }

function renderChatButtons(items, onSelect, grouped) {
  const msgs = document.getElementById('chat-msgs');
  const wrap = document.createElement('div');
  wrap.className = 'chat-btns';
  let lastDay = '';
  items.forEach(item => {
    if (grouped && item.label) {
      const dayPart = item.label.replace(/\s+\d{1,2}:\d{2}$/, '');
      if (dayPart !== lastDay) {
        const lbl = document.createElement('div');
        lbl.className = 'chat-day-label'; lbl.textContent = '📅 ' + dayPart;
        wrap.appendChild(lbl); lastDay = dayPart;
      }
    }
    const b = document.createElement('button');
    b.className   = 'chat-btn-opt';
    b.textContent = grouped ? item.label.replace(/.*\s(\d{1,2}:\d{2})$/, '$1') : item.label;
    b.addEventListener('click', () => {
      wrap.querySelectorAll('.chat-btn-opt').forEach(x => { x.disabled = true; x.style.opacity = '0.5'; });
      onSelect(item);
    });
    wrap.appendChild(b);
  });
  msgs.appendChild(wrap); scrollChatBottom();
}

async function sendChatMessage(text) {
  if (chatLoading || !text.trim()) return;
  chatLoading = true;
  const input = document.getElementById('chat-input');
  input.value = ''; input.style.height = 'auto';
  addChatMsg(text, 'user');
  showChatTyping();
  try {
    const res = await fetch(`${API}/api/widget/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: clientData.id, message: text, session_id: chatSessionId }),
    });
    const data = await res.json();
    hideChatTyping();
    if (data.type === 'slots' && data.items?.length) {
      // Mostrar slots como texto plano agrupado por día
      let slotText = data.text ? data.text + '\n\n' : '📅 Horarios disponibles:\n\n';
      let lastDay = '';
      data.items.forEach(item => {
        const dayPart = item.label.replace(/\s+\d{1,2}:\d{2}$/, '');
        const timePart = item.label.replace(/.*\s(\d{1,2}:\d{2})$/, '$1');
        if (dayPart !== lastDay) {
          if (lastDay) slotText += '\n';
          slotText += `📆 ${dayPart}\n`;
          lastDay = dayPart;
        }
        slotText += `  ÔÇó ${timePart}\n`;
      });
      slotText += '\nEscribe el día y hora que prefieras.';
      addChatMsg(slotText, 'bot');
    } else {
      if (data.text) addChatMsg(data.text, 'bot', data.type === 'confirmed' ? 'confirmed' : 'text');
      if (data.type === 'options' && data.items?.length) {
        renderChatButtons(data.items, item => { addChatMsg(item.label, 'user'); sendChatMessage(item.label); }, false);
      }
    }
  } catch(err) { console.error('[CHAT ERROR]', err); hideChatTyping(); addChatMsg('Error de conexión. Intenta de nuevo.', 'bot'); }
  finally { chatLoading = false; scrollChatBottom(); }
}

function resetChat() {
  document.getElementById('chat-msgs').innerHTML = '';
  chatSessionId = newUUID();
  chatGreeted   = false;
  setPendingChanges(false);
  initChat();
}

document.getElementById('chat-send').addEventListener('click', () => sendChatMessage(document.getElementById('chat-input').value));
document.getElementById('chat-input').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(e.target.value); } });
document.getElementById('chat-input').addEventListener('input', function () { this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 80) + 'px'; });
document.getElementById('btn-reset-chat').addEventListener('click', resetChat);

// ===========================================
// HELPERS DE FORMATO
// ===========================================
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function formatDateTime(str) {
  if (!str) return '—';
  try {
    const d = new Date(str);
    return d.toLocaleDateString('es-MX', {day:'2-digit',month:'short',year:'numeric'}) + ' ' +
           d.toLocaleTimeString('es-MX', {hour:'2-digit',minute:'2-digit'});
  } catch { return String(str); }
}
function statusBadge(s) {
  const m = { pendiente:['badge-yellow','Pendiente'], confirmed:['badge-green','Confirmada'], cancelled:['badge-red','Cancelada'], completed:['badge-blue','Completada'] };
  const [cls, lbl] = m[s] || ['badge-gray', s];
  return `<span class="badge ${cls}">${lbl}</span>`;
}
function leadStatusBadge(s) {
  const m = { nuevo:['badge-blue','Nuevo'], new:['badge-blue','Nuevo'], interesado:['badge-green','Interesado'], contacted:['badge-yellow','Contactado'], cold:['badge-gray','Frío'], converted:['badge-purple','Convertido'] };
  const [cls, lbl] = m[s] || ['badge-gray', s];
  return `<span class="badge ${cls}">${lbl}</span>`;
}
function sourceBadge(source) {
  if (source === 'widget') return '<span class="badge badge-purple"><i class="fas fa-globe" style="font-size:10px"></i> Widget</span>';
  return '<span class="badge badge-green"><i class="fab fa-whatsapp" style="font-size:10px"></i> WhatsApp</span>';
}

// ===========================================
// HORARIOS — Editor de franjas por semana
// ===========================================
let scheduleState = {};
let currentWeekStart = null;
let horariosLoaded = false;

function toLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

function getMonday(dateStr) {
  const date = new Date(dateStr + 'T12:00:00');
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);
  return toLocalDateStr(date);
}

function getWeekDates(mondayStr) {
  const days = [];
  const dayLabels = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
  const monthNames = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  for (let i = 0; i < 7; i++) {
    const d = new Date(mondayStr + 'T12:00:00');
    d.setDate(d.getDate() + i);
    const dateStr = toLocalDateStr(d);
    days.push({ date: dateStr, label: `${dayLabels[i]} ${d.getDate()} ${monthNames[d.getMonth()]}` });
  }
  return days;
}

async function initHorariosSection() {
  if (!currentWeekStart) currentWeekStart = getMonday(toLocalDateStr(new Date()));
  await loadSchedules();
}

async function loadSchedules() {
  if (!clientData?.id) return;
  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}/schedules?week_start=${currentWeekStart}`, {
      headers: authHeader()
    });
    const data = await res.json();
    scheduleState = {};
    const list = Array.isArray(data) ? data : (data.schedules || []);
    list.forEach(s => {
      const key = s.schedule_date;
      if (!scheduleState[key]) scheduleState[key] = [];
      scheduleState[key].push({ start: s.start_time, end: s.end_time });
    });
    renderScheduleEditor();
  } catch (e) {
    console.error('Error cargando horarios:', e);
    scheduleState = {};
    renderScheduleEditor();
  }
}

function renderWeekSelector() {
  const container = document.getElementById('weekSelector');
  if (!container) return;
  const weekDates = getWeekDates(currentWeekStart);
  container.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
      <button class="btn-secondary" style="padding:6px 14px;" onclick="changeScheduleWeek(-1)">← Anterior</button>
      <span style="font-weight:600;color:var(--accent,#6C63FF);">${weekDates[0].label} — ${weekDates[6].label}</span>
      <button class="btn-secondary" style="padding:6px 14px;" onclick="changeScheduleWeek(1)">Siguiente →</button>
    </div>
    <div style="margin-top:8px;">
      <button class="btn-secondary" style="padding:4px 10px;font-size:0.8rem;" onclick="copyWeekSchedule()">📋 Copiar semana</button>
    </div>
  `;
}

function changeScheduleWeek(offset) {
  const d = new Date(currentWeekStart + 'T12:00:00');
  d.setDate(d.getDate() + (offset * 7));
  currentWeekStart = toLocalDateStr(d);
  loadSchedules();
}

function renderScheduleEditor() {
  const container = document.getElementById('scheduleEditor');
  if (!container) return;
  renderWeekSelector();

  const weekDates = getWeekDates(currentWeekStart);
  const inputStyle = 'padding:6px 8px;border-radius:6px;border:1px solid var(--border,rgba(255,255,255,0.15));background:var(--input-bg,rgba(0,0,0,0.2));color:var(--text,#fff);font-size:0.85rem;';

  let html = weekDates.map(day => {
    const franjas = scheduleState[day.date] || [];
    const isActive = franjas.length > 0;

    const franjasHtml = franjas.map((f, fi) => `
      <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
        <input type="time" value="${f.start}" style="${inputStyle}width:110px;"
          onchange="updateScheduleFranja('${day.date}',${fi},'start',this.value)">
        <span style="color:var(--text-muted,#888)">→</span>
        <input type="time" value="${f.end}" style="${inputStyle}width:110px;"
          onchange="updateScheduleFranja('${day.date}',${fi},'end',this.value)">
        <button onclick="removeScheduleFranja('${day.date}',${fi})"
          style="background:rgba(255,80,80,0.15);border:none;color:#ff5050;border-radius:6px;padding:4px 8px;cursor:pointer;">✖</button>
      </div>
    `).join('');

    return `
    <div style="background:var(--card-bg,rgba(255,255,255,0.04));border-radius:10px;padding:10px 14px;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:600;">
          <input type="checkbox" ${isActive ? 'checked' : ''}
            onchange="toggleScheduleDay('${day.date}',this.checked)"
            style="width:16px;height:16px;accent-color:var(--accent,#6C63FF);">
          ${day.label}
        </label>
        ${isActive ? `
          <div style="display:flex;gap:6px;">
            <button onclick="addScheduleFranja('${day.date}')"
              style="background:rgba(108,99,255,0.15);border:1px solid rgba(108,99,255,0.3);color:var(--accent,#6C63FF);border-radius:6px;padding:3px 10px;cursor:pointer;font-size:0.8rem;">
              + Franja</button>
            <button onclick="copyDaySchedule('${day.date}')"
              title="Copiar este día a otro"
              style="background:rgba(108,99,255,0.1);border:1px solid rgba(108,99,255,0.25);color:var(--accent,#6C63FF);border-radius:6px;padding:3px 8px;cursor:pointer;font-size:0.8rem;">
              📋</button>
          </div>` : ''}
      </div>
      ${isActive ? franjasHtml : '<span style="color:var(--text-muted,#888);font-size:0.8rem;margin-left:24px;">Día no laborable</span>'}
    </div>`;
  }).join('');

  container.innerHTML = html;
}

function toggleScheduleDay(dateKey, active) {
  if (active) {
    scheduleState[dateKey] = [{ start: '09:00', end: '18:00' }];
  } else {
    delete scheduleState[dateKey];
  }
  renderScheduleEditor();
}

function addScheduleFranja(dateKey) {
  if (!scheduleState[dateKey]) scheduleState[dateKey] = [];
  const last = scheduleState[dateKey].slice(-1)[0];
  scheduleState[dateKey].push({ start: last ? last.end : '09:00', end: '20:00' });
  renderScheduleEditor();
}

function removeScheduleFranja(dateKey, fi) {
  scheduleState[dateKey].splice(fi, 1);
  if (scheduleState[dateKey].length === 0) delete scheduleState[dateKey];
  renderScheduleEditor();
}

function updateScheduleFranja(dateKey, fi, field, value) {
  if (scheduleState[dateKey] && scheduleState[dateKey][fi]) {
    scheduleState[dateKey][fi][field] = value;
  }
}

function copyDaySchedule(sourceDateKey) {
  const weekDates = getWeekDates(currentWeekStart);
  const otherDays = weekDates.filter(d => d.date !== sourceDateKey);

  const optionsHtml = otherDays.map(d =>
    `<label style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:8px;cursor:pointer;border:1px solid var(--border,rgba(255,255,255,0.1));">
      <input type="checkbox" value="${d.date}" style="accent-color:var(--accent,#6C63FF);">
      <span style="font-size:0.9rem;">${d.label}</span>
    </label>`
  ).join('');

  const modal = document.createElement('div');
  modal.id = 'copyDayModal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background:var(--card-bg,#1a1a2e);border:1px solid var(--border,rgba(255,255,255,0.1));border-radius:16px;padding:24px;width:300px;">
      <h4 style="margin:0 0 4px;color:var(--accent,#6C63FF);">Copiar día</h4>
      <p style="color:var(--text-muted,#888);font-size:0.8rem;margin-bottom:12px;">Selecciona los días destino:</p>
      <div style="display:flex;flex-direction:column;gap:6px;">${optionsHtml}</div>
      <div style="display:flex;gap:8px;margin-top:16px;">
        <button onclick="document.getElementById('copyDayModal').remove()" class="btn-secondary" style="flex:1;padding:8px;">Cancelar</button>
        <button onclick="applyCopyDaySchedule('${sourceDateKey}')" class="btn-primary" style="flex:1;padding:8px;">Copiar</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
}

function applyCopyDaySchedule(sourceDateKey) {
  const franjas = scheduleState[sourceDateKey];
  if (!franjas || franjas.length === 0) {
    document.getElementById('copyDayModal')?.remove();
    return showToast('El día origen no tiene franjas', 'error');
  }
  const checked = [...document.querySelectorAll('#copyDayModal input[type=checkbox]:checked')].map(el => el.value);
  if (checked.length === 0) {
    return showToast('Selecciona al menos un día destino', 'error');
  }
  checked.forEach(targetDate => {
    scheduleState[targetDate] = franjas.map(f => ({ start: f.start, end: f.end }));
  });
  document.getElementById('copyDayModal')?.remove();
  renderScheduleEditor();
  showToast(`Horario copiado a ${checked.length} día(s)`, 'success');
}

function copyWeekSchedule() {
  const nextMonday = new Date(currentWeekStart + 'T12:00:00');
  nextMonday.setDate(nextMonday.getDate() + 7);
  const defaultTarget = toLocalDateStr(nextMonday);

  const modal = document.createElement('div');
  modal.id = 'copyWeekModal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background:var(--card-bg,#1a1a2e);border:1px solid var(--border,rgba(255,255,255,0.1));border-radius:16px;padding:24px;width:320px;">
      <h4 style="margin:0 0 12px;color:var(--accent,#6C63FF);">Copiar semana completa</h4>
      <p style="color:var(--text-muted,#888);font-size:0.85rem;margin-bottom:12px;">Selecciona el lunes de la semana destino:</p>
      <input type="date" id="copyWeekTarget" value="${defaultTarget}"
        style="width:100%;padding:8px;border-radius:8px;border:1px solid var(--border,rgba(255,255,255,0.15));background:var(--input-bg,rgba(0,0,0,0.3));color:var(--text,#fff);font-size:0.9rem;">
      <div style="display:flex;gap:8px;margin-top:16px;">
        <button onclick="document.getElementById('copyWeekModal').remove()" class="btn-secondary" style="flex:1;padding:8px;">Cancelar</button>
        <button onclick="applyCopyWeekSchedule()" class="btn-primary" style="flex:1;padding:8px;">Copiar</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
}

async function applyCopyWeekSchedule() {
  const targetDate = document.getElementById('copyWeekTarget').value;
  if (!targetDate) return showToast('Selecciona una fecha', 'error');
  const targetMonday = getMonday(targetDate);

  const sourceDates = getWeekDates(currentWeekStart);
  const targetDates = getWeekDates(targetMonday);
  const newSchedules = [];

  sourceDates.forEach((src, i) => {
    const franjas = scheduleState[src.date];
    if (franjas) {
      franjas.forEach(f => {
        newSchedules.push({ schedule_date: targetDates[i].date, start_time: f.start, end_time: f.end });
      });
    }
  });

  if (newSchedules.length === 0) {
    document.getElementById('copyWeekModal')?.remove();
    return showToast('No hay horarios en esta semana para copiar', 'error');
  }

  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}/schedules`, {
      method: 'POST', headers: authHeader(),
      body: JSON.stringify({ schedules: newSchedules, week_start: targetMonday })
    });
    document.getElementById('copyWeekModal')?.remove();
    if (res.ok) {
      showToast(`Semana copiada a ${targetDates[0].label} — ${targetDates[6].label}`, 'success');
    } else { showToast('Error copiando semana', 'error'); }
  } catch { document.getElementById('copyWeekModal')?.remove(); showToast('Error de conexión', 'error'); }
}

document.getElementById('btn-save-schedule')?.addEventListener('click', async () => {
  if (!clientData?.id) return;
  const btn = document.getElementById('btn-save-schedule');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

  const schedules = [];
  Object.entries(scheduleState).forEach(([dateKey, franjas]) => {
    franjas.forEach(f => {
      schedules.push({ schedule_date: dateKey, start_time: f.start, end_time: f.end });
    });
  });

  try {
    const res = await fetch(`${API}/api/clients/${clientData.id}/schedules`, {
      method: 'POST', headers: authHeader(),
      body: JSON.stringify({ schedules, week_start: currentWeekStart })
    });
    if (res.ok) {
      showToast('Horarios guardados', 'success');
    } else { showToast('Error guardando horarios', 'error'); }
  } catch { showToast('Error de conexión', 'error'); }
  finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-floppy-disk"></i> Guardar Horarios';
  }
});

// ===========================================
// INIT
// ===========================================
(function init() {
  if (authToken && clientData) showDashboard();
})();
