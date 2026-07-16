/* main.js — Scripts globales del panel */

const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';

// ── API helper con CSRF ─────────────────────────
async function api(url, method = 'GET', data = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        credentials: 'same-origin',
    };
    if (data) opts.body = JSON.stringify(data);
    const res = await fetch(url, opts);
    return res.json();
}

// ── Toast ────────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
    toast.className = `toast show ${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i> ${message}`;
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), duration);
}

// ── Sidebar toggle ─────────────────────────────
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');

function openMobileSidebar() {
    sidebar?.classList.add('open');
    sidebarBackdrop?.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeMobileSidebar() {
    sidebar?.classList.remove('open');
    sidebarBackdrop?.classList.remove('active');
    document.body.style.overflow = '';
}

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar?.classList.toggle('collapsed');
    });
}
if (mobileSidebarToggle) {
    mobileSidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar?.classList.contains('open') ? closeMobileSidebar() : openMobileSidebar();
    });
}

// Backdrop toca → cierra
sidebarBackdrop?.addEventListener('click', closeMobileSidebar);

// Nav links dentro del sidebar → navegar y cerrar
sidebar?.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 768) closeMobileSidebar();
    });
});

// ── Auto-refresh bot status in sidebar ─────────
function refreshBotStatusMini() {
    fetch('/api/bot/status', { credentials: 'same-origin' })
        .then(r => r.json())
        .then(data => {
            const dot = document.getElementById('statusDot');
            const label = document.getElementById('statusLabel');
            const name = document.getElementById('statusName');

            if (!dot) return;
            dot.className = `status-dot ${data.status || 'offline'}`;
            if (label) label.textContent = capitalize(data.status || 'Offline');
        })
        .catch(() => {});
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Update sidebar every 10 seconds
if (document.getElementById('statusDot')) {
    refreshBotStatusMini();
    setInterval(refreshBotStatusMini, 10000);
}

// ── Flash auto-dismiss ─────────────────────────
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el?.remove(), 5000);
});
