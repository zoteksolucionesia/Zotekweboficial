/**
 * Zotek Widget v1.0
 * Chat embebible para cualquier landing page.
 *
 * Uso:
 *   <script src="https://zotek-ia.web.app/widget.js?bot=CLIENT_ID&color=%236C63FF"></script>
 */
(function () {
  'use strict';

  // ── Configuración desde query params del script ──────────────────────────
  var scriptTag = document.currentScript ||
    (function () {
      var tags = document.getElementsByTagName('script');
      return tags[tags.length - 1];
    })();

  var src       = scriptTag ? scriptTag.src : '';
  var urlParams = new URL(src, location.href).searchParams;
  var CLIENT_ID  = urlParams.get('bot') || '';
  var ACCENT     = urlParams.get('color') || '#6C63FF';
  var API_BASE   = 'https://api-handler-gfd2ph2qpq-uc.a.run.app';

  if (!CLIENT_ID) {
    console.warn('[Zotek Widget] Falta el parámetro ?bot=CLIENT_ID');
    return;
  }

  // ── Session ID persistente por visitante ─────────────────────────────────
  var SESSION_KEY = 'zotek_session_' + CLIENT_ID;
  var sessionId   = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  // ── Estilos ───────────────────────────────────────────────────────────────
  var style = document.createElement('style');
  style.textContent = [
    '#ztk-btn{position:fixed;bottom:24px;right:24px;width:56px;height:56px;border-radius:50%;background:' + ACCENT + ';border:none;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.25);display:flex;align-items:center;justify-content:center;z-index:999999;transition:transform .2s;}',
    '#ztk-btn:hover{transform:scale(1.08);}',
    '#ztk-btn svg{width:28px;height:28px;fill:#fff;}',
    '#ztk-box{position:fixed;bottom:92px;right:24px;width:360px;max-height:560px;border-radius:16px;background:#fff;box-shadow:0 8px 32px rgba(0,0,0,.18);display:flex;flex-direction:column;z-index:999998;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;transition:opacity .2s,transform .2s;}',
    '#ztk-box.ztk-hidden{opacity:0;pointer-events:none;transform:translateY(12px);}',
    '#ztk-head{background:' + ACCENT + ';padding:14px 16px;color:#fff;display:flex;align-items:center;gap:10px;}',
    '#ztk-head img{width:36px;height:36px;border-radius:50%;object-fit:cover;background:#fff3;}',
    '#ztk-head-info strong{display:block;font-size:15px;}',
    '#ztk-head-info span{font-size:12px;opacity:.85;}',
    '#ztk-close{margin-left:auto;background:none;border:none;cursor:pointer;color:#fff;font-size:20px;line-height:1;padding:0;}',
    '#ztk-msgs{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth;}',
    '.ztk-msg{max-width:80%;padding:10px 14px;border-radius:14px;line-height:1.5;word-break:break-word;white-space:pre-wrap;}',
    '.ztk-msg.bot{background:#f2f2f7;color:#1c1c1e;border-bottom-left-radius:4px;align-self:flex-start;}',
    '.ztk-msg.usr{background:' + ACCENT + ';color:#fff;border-bottom-right-radius:4px;align-self:flex-end;}',
    '.ztk-msg.bot.typing span{display:inline-block;width:7px;height:7px;border-radius:50%;background:#999;animation:ztk-blink 1.2s infinite;}',
    '.ztk-msg.bot.typing span:nth-child(2){animation-delay:.2s;}',
    '.ztk-msg.bot.typing span:nth-child(3){animation-delay:.4s;}',
    '@keyframes ztk-blink{0%,80%,100%{opacity:0;}40%{opacity:1;}}',
    '.ztk-btns{display:flex;flex-wrap:wrap;gap:8px;padding:4px 0 6px;}',
    '.ztk-btn-opt{background:#fff;border:1.5px solid ' + ACCENT + ';color:' + ACCENT + ';border-radius:20px;padding:6px 14px;cursor:pointer;font-size:13px;transition:background .15s,color .15s;}',
    '.ztk-btn-opt:hover{background:' + ACCENT + ';color:#fff;}',
    '.ztk-confirmed{background:#e6f9ed;border-left:4px solid #34c759;border-radius:10px;padding:12px 14px;color:#1c1c1e;}',
    '#ztk-foot{padding:10px 12px;border-top:1px solid #e5e5ea;display:flex;gap:8px;}',
    '#ztk-input{flex:1;border:1.5px solid #e5e5ea;border-radius:22px;padding:9px 14px;font-size:14px;outline:none;resize:none;max-height:100px;line-height:1.4;font-family:inherit;transition:border-color .2s;}',
    '#ztk-input:focus{border-color:' + ACCENT + ';}',
    '#ztk-send{background:' + ACCENT + ';border:none;border-radius:50%;width:40px;height:40px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;}',
    '#ztk-send svg{width:18px;height:18px;fill:#fff;}',
    '@media(max-width:420px){#ztk-box{width:calc(100vw - 24px);right:12px;bottom:80px;}}',
  ].join('');
  document.head.appendChild(style);

  // ── HTML ─────────────────────────────────────────────────────────────────
  var container = document.createElement('div');
  container.innerHTML = [
    '<button id="ztk-btn" aria-label="Abrir chat">',
    '  <svg viewBox="0 0 24 24"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>',
    '</button>',
    '<div id="ztk-box" class="ztk-hidden" role="dialog" aria-label="Chat">',
    '  <div id="ztk-head">',
    '    <img id="ztk-avatar" src="" alt="">',
    '    <div id="ztk-head-info"><strong id="ztk-botname">Asistente</strong><span>En línea</span></div>',
    '    <button id="ztk-close" aria-label="Cerrar">✕</button>',
    '  </div>',
    '  <div id="ztk-msgs"></div>',
    '  <div id="ztk-foot">',
    '    <textarea id="ztk-input" placeholder="Escribe un mensaje..." rows="1"></textarea>',
    '    <button id="ztk-send" aria-label="Enviar">',
    '      <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
    '    </button>',
    '  </div>',
    '</div>',
  ].join('');
  document.body.appendChild(container);

  // ── Referencias DOM ──────────────────────────────────────────────────────
  var btn    = document.getElementById('ztk-btn');
  var box    = document.getElementById('ztk-box');
  var msgs   = document.getElementById('ztk-msgs');
  var input  = document.getElementById('ztk-input');
  var send   = document.getElementById('ztk-send');
  var closeB = document.getElementById('ztk-close');

  // ── Estado ───────────────────────────────────────────────────────────────
  var isOpen    = false;
  var isLoading = false;
  var greeted   = false;

  // ── Toggle ───────────────────────────────────────────────────────────────
  function toggleChat() {
    isOpen = !isOpen;
    box.classList.toggle('ztk-hidden', !isOpen);
    if (isOpen) {
      input.focus();
      if (!greeted) { greet(); }
    }
  }
  btn.addEventListener('click', toggleChat);
  closeB.addEventListener('click', toggleChat);

  // ── Añadir mensaje al chat ───────────────────────────────────────────────
  function addMsg(text, role, type) {
    type = type || 'text';
    var div = document.createElement('div');
    div.className = 'ztk-msg ' + role;

    if (type === 'confirmed') {
      div.className = 'ztk-confirmed';
      div.textContent = text;
    } else {
      div.textContent = text;
    }
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  // ── Typing indicator ─────────────────────────────────────────────────────
  function showTyping() {
    var div = document.createElement('div');
    div.className = 'ztk-msg bot typing';
    div.id = 'ztk-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }
  function hideTyping() {
    var t = document.getElementById('ztk-typing');
    if (t) t.remove();
  }

  // ── Renderizar botones (slots u opciones) ────────────────────────────────
  function renderButtons(items, onSelect) {
    var wrap = document.createElement('div');
    wrap.className = 'ztk-btns';
    items.forEach(function (item) {
      var b = document.createElement('button');
      b.className = 'ztk-btn-opt';
      b.textContent = item.label;
      b.addEventListener('click', function () {
        // Deshabilitar todos los botones del grupo
        wrap.querySelectorAll('.ztk-btn-opt').forEach(function (x) {
          x.disabled = true;
          x.style.opacity = '0.5';
        });
        onSelect(item);
      });
      wrap.appendChild(b);
    });
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
  }

  // ── Llamar a la API ──────────────────────────────────────────────────────
  function sendMessage(text) {
    if (isLoading || !text.trim()) return;
    isLoading = true;
    input.value = '';
    input.style.height = 'auto';

    addMsg(text, 'usr');
    showTyping();

    fetch(API_BASE + '/api/widget/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_id: CLIENT_ID,
        message: text,
        session_id: sessionId,
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        hideTyping();

        if (data.text) {
          addMsg(data.text, 'bot', data.type === 'confirmed' ? 'confirmed' : 'text');
        }

        if (data.type === 'slots' && data.items && data.items.length) {
          renderButtons(data.items, function (item) {
            addMsg(item.label, 'usr');
            sendMessage(item.label);
          });
        } else if (data.type === 'options' && data.items && data.items.length) {
          renderButtons(data.items, function (item) {
            addMsg(item.label, 'usr');
            sendMessage(item.label);
          });
        }
      })
      .catch(function () {
        hideTyping();
        addMsg('Hubo un problema de conexión. Intenta de nuevo.', 'bot');
      })
      .finally(function () {
        isLoading = false;
        msgs.scrollTop = msgs.scrollHeight;
      });
  }

  // ── Saludo inicial ───────────────────────────────────────────────────────
  function greet() {
    greeted = true;
    sendMessage('Hola');
  }

  // ── Eventos de input ─────────────────────────────────────────────────────
  send.addEventListener('click', function () {
    sendMessage(input.value);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input.value);
    }
  });

  // Auto-resize textarea
  input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
  });

  // ── Cargar info del bot (nombre) ─────────────────────────────────────────
  fetch(API_BASE + '/api/widget/info?bot=' + CLIENT_ID)
    .then(function (r) { return r.json(); })
    .then(function (info) {
      if (info.name) document.getElementById('ztk-botname').textContent = info.name;
    })
    .catch(function () {});

})();
