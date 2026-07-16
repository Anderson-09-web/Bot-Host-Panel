/* settings.js */

function toggleVis(id, btn) {
    const input = document.getElementById(id);
    const icon = btn.querySelector('i');
    input.type = input.type === 'password' ? 'text' : 'password';
    icon.className = input.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
}

async function saveBot() {
    const r = await api('/api/settings/bot', 'POST', {
        token:    document.getElementById('botToken')?.value,
        prefix:   document.getElementById('botPrefix')?.value,
        timezone: document.getElementById('botTimezone')?.value,
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

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

async function savePanel() {
    const r = await api('/api/settings/panel', 'POST', {
        panel_name: document.getElementById('panelName')?.value,
    });
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}
