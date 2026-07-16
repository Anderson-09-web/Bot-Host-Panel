/* settings.js */

/* ── Toggle campo password ── */
function toggleField(id, btn) {
    const inp  = document.getElementById(id);
    const icon = btn.querySelector('i');
    if (!inp) return;
    inp.type = inp.type === 'password' ? 'text' : 'password';
    icon.className = inp.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
}

/* ── Guardar credenciales Discord ── */
async function saveBot() {
    const token  = document.getElementById('botToken')?.value || '';
    const secret = document.getElementById('botClientSecret')?.value || '';
    const data = {
        client_id:    document.getElementById('botClientId')?.value || '',
        description:  document.getElementById('botDescription')?.value || '',
    };
    if (token)  data.token = token;
    if (secret) data.client_secret = secret;

    const r = await api('/api/settings/bot', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

/* ── Guardar comportamiento ── */
async function saveBehavior() {
    const r = await api('/api/settings/bot', 'POST', {
        prefix:                 document.getElementById('botPrefix')?.value || '!',
        timezone:               document.getElementById('botTimezone')?.value || 'UTC',
        intent_members:         document.getElementById('intentMembers')?.checked ?? true,
        intent_message_content: document.getElementById('intentMsgContent')?.checked ?? true,
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

/* ── Guardar presencia ── */
async function savePresence() {
    const r = await api('/api/settings/bot', 'POST', {
        status_type:   document.getElementById('botStatus')?.value || 'online',
        activity_type: document.getElementById('botActivityType')?.value || 'playing',
        activity_text: document.getElementById('botActivityText')?.value || '',
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

/* ── Preview de presencia en tiempo real ── */
const STATUS_ICONS = { online:'🟢', idle:'🌙', dnd:'🔴', invisible:'⚫' };
const ACTIVITY_LABELS = {
    playing:'Jugando a', watching:'Viendo', listening:'Escuchando',
    streaming:'En directo', competing:'Compitiendo en'
};

function updatePresencePreview() {
    const dot      = document.getElementById('presenceDot');
    const activity = document.getElementById('presenceActivity');
    const status   = document.getElementById('botStatus')?.value || 'online';
    const aType    = document.getElementById('botActivityType')?.value || 'playing';
    const aText    = document.getElementById('botActivityText')?.value || '';

    if (dot) {
        dot.className = 'presence-dot';
        dot.classList.add('presence-' + status);
    }
    if (activity) {
        activity.textContent = aText
            ? `${ACTIVITY_LABELS[aType] || aType} ${aText}`
            : '(sin actividad)';
    }
}

['botStatus','botActivityType','botActivityText'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', updatePresencePreview);
    document.getElementById(id)?.addEventListener('change', updatePresencePreview);
});
updatePresencePreview();

/* ── Lavalink ── */
async function saveLava() {
    const r = await api('/api/settings/lavalink', 'POST', {
        host:     document.getElementById('lavaHost')?.value,
        port:     parseInt(document.getElementById('lavaPort')?.value || '2333'),
        password: document.getElementById('lavaPassword')?.value,
        ssl:      document.getElementById('lavaSSL')?.checked,
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

async function reconnectLava() {
    const r = await api('/api/settings/lavalink/reconnect', 'POST');
    showToast(r.message || (r.success ? 'Reconectando...' : 'Error.'), r.success ? 'info' : 'error');
}

/* ── Panel ── */
async function savePanel() {
    const r = await api('/api/settings/panel', 'POST', {
        panel_name: document.getElementById('panelName')?.value,
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}
