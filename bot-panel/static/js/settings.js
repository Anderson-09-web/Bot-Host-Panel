/* settings.js — Guardar configuración del panel */

function toggleVis(id, btn) {
    const input = document.getElementById(id);
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fa-solid fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fa-solid fa-eye';
    }
}

async function saveBot() {
    const data = {
        token:    document.getElementById('botToken')?.value,
        prefix:   document.getElementById('botPrefix')?.value,
        timezone: document.getElementById('botTimezone')?.value,
    };
    const r = await api('/api/settings/bot', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

async function saveLava() {
    const data = {
        host:     document.getElementById('lavaHost')?.value,
        port:     parseInt(document.getElementById('lavaPort')?.value || '2333'),
        password: document.getElementById('lavaPassword')?.value,
        ssl:      document.getElementById('lavaSSL')?.checked,
    };
    const r = await api('/api/settings/lavalink', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

async function reconnectLava() {
    const r = await api('/api/settings/lavalink/reconnect', 'POST');
    showToast(r.message || (r.success ? 'Reconectando...' : 'Error.'), r.success ? 'info' : 'error');
}

async function savePanel() {
    const data = { panel_name: document.getElementById('panelName')?.value };
    const r = await api('/api/settings/panel', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}
