/* dashboard.js — Estadísticas en tiempo real + control del bot */

let statsInterval = null;

async function fetchStats() {
    try {
        const data = await api('/api/stats');
        updateStats(data);
        updateBotBanner(data);
    } catch (e) {
        console.warn('Error obteniendo stats:', e);
    }
}

function updateStats(data) {
    // CPU
    const cpu = data.cpu_percent ?? 0;
    setText('statCpu', `${cpu}%`);
    setBarWidth('cpuBar', cpu);

    // RAM
    const ramPct = data.ram_percent ?? 0;
    const ramUsed = data.ram_used_mb ?? 0;
    setText('statRam', `${ramUsed}MB`);
    setBarWidth('ramBar', ramPct);

    // Ping
    setText('statPing', data.ping ? `${data.ping}ms` : '—');

    // Servidores / Usuarios
    setText('statServers', data.guilds ?? '—');
    setText('statUsers', data.users ?? '—');

    // Uptime panel
    setText('statUptime', data.panel_uptime ?? '—');
}

function updateBotBanner(data) {
    const status = data.status || 'offline';

    // Avatar
    const avatarImg = document.getElementById('botAvatar');
    const avatarFallback = document.getElementById('botAvatarFallback');
    if (data.avatar_url && avatarImg) {
        avatarImg.src = data.avatar_url;
        avatarImg.style.display = '';
        if (avatarFallback) avatarFallback.style.display = 'none';
    }

    // Name / ID
    setText('botName', data.name || '—');
    setText('botId', data.bot_id ? `ID: ${data.bot_id}` : 'ID: —');

    // Status indicators
    const bannerDot = document.getElementById('bannerStatusDot');
    if (bannerDot) {
        bannerDot.className = `status-indicator ${status}`;
    }

    const badge = document.getElementById('statusBadgeText');
    if (badge) {
        const badgeClasses = {
            online: 'badge badge-online',
            offline: 'badge badge-offline',
            paused: 'badge badge-paused',
            starting: 'badge badge-starting',
        };
        badge.className = badgeClasses[status] || 'badge badge-offline';
        badge.textContent = capitalize(status);
    }

    // Sidebar mini
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');
    const sName = document.getElementById('statusName');
    if (dot) dot.className = `status-dot ${status}`;
    if (label) label.textContent = capitalize(status);
    if (sName && data.name) sName.textContent = data.name;

    // Update button states
    updateButtonStates(status);
}

function updateButtonStates(status) {
    const isRunning = status === 'online';
    const isPaused = status === 'paused';

    const btnStart   = document.getElementById('btnStart');
    const btnPause   = document.getElementById('btnPause');
    const btnRestart = document.getElementById('btnRestart');
    const btnStop    = document.getElementById('btnStop');
    const btnPauseIcon = btnPause?.querySelector('i');
    const btnPauseLabel = btnPause?.querySelector('span');

    if (btnStart)   btnStart.disabled   = isRunning || isPaused;
    if (btnPause)   btnPause.disabled   = !isRunning && !isPaused;
    if (btnRestart) btnRestart.disabled = !isRunning && !isPaused;
    if (btnStop)    btnStop.disabled    = !isRunning && !isPaused;

    if (isPaused && btnPauseIcon) {
        btnPauseIcon.className = 'fa-solid fa-play';
        if (btnPauseLabel) btnPauseLabel.textContent = 'Reanudar';
    } else if (btnPauseIcon) {
        btnPauseIcon.className = 'fa-solid fa-pause';
        if (btnPauseLabel) btnPauseLabel.textContent = 'Pausar';
    }
}

async function botAction(action) {
    const feedback = document.getElementById('actionFeedback');
    if (feedback) feedback.textContent = `Ejecutando: ${action}...`;

    const endpoints = {
        start:   '/api/bot/start',
        pause:   '/api/bot/pause',
        restart: '/api/bot/restart',
        stop:    '/api/bot/stop',
    };

    try {
        const result = await api(endpoints[action], 'POST');
        const msg = result.message || (result.success ? 'OK' : 'Error');
        if (feedback) feedback.textContent = msg;
        showToast(msg, result.success ? 'success' : 'error');

        // Refresh stats immediately
        setTimeout(fetchStats, 800);
        setTimeout(fetchStats, 2000);
    } catch (e) {
        const msg = `Error: ${e.message}`;
        if (feedback) feedback.textContent = msg;
        showToast(msg, 'error');
    }
}

// ── Helpers ──────────────────────────────────────
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setBarWidth(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${Math.min(pct, 100)}%`;
}

function capitalize(str) {
    return str ? str.charAt(0).toUpperCase() + str.slice(1) : str;
}

// ── Init ─────────────────────────────────────────
fetchStats();
statsInterval = setInterval(fetchStats, 5000);
