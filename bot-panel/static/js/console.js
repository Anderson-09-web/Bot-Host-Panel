/* console.js — Consola en tiempo real con SSE */

let autoScroll = true;
let allLogs = [];
let currentFilter = 'all';
let eventSource = null;

const output = document.getElementById('consoleOutput');

// Inicializar: cargar historial y conectar SSE
async function initConsole() {
    // Cargar logs existentes
    try {
        const data = await api('/api/console/logs');
        if (data.logs) {
            allLogs = data.logs;
            renderAllLogs();
        }
    } catch (e) {}

    // Conectar SSE
    connectSSE();
}

function connectSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource('/api/console/stream');

    eventSource.onmessage = (e) => {
        try {
            const entry = JSON.parse(e.data);
            allLogs.push(entry);
            if (allLogs.length > 500) allLogs.shift();
            if (currentFilter === 'all' || entry.level === currentFilter) {
                appendLog(entry);
            }
        } catch (_) {}
    };

    eventSource.onerror = () => {
        setTimeout(connectSSE, 3000);
    };
}

function renderAllLogs() {
    if (!output) return;
    output.innerHTML = '';
    const filtered = currentFilter === 'all'
        ? allLogs
        : allLogs.filter(l => l.level === currentFilter);

    if (filtered.length === 0) {
        output.innerHTML = '<div class="console-welcome"><i class="fa-solid fa-terminal"></i><span>Sin logs aún...</span></div>';
        return;
    }

    const frag = document.createDocumentFragment();
    filtered.forEach(entry => {
        frag.appendChild(createLogLine(entry));
    });
    output.appendChild(frag);
    if (autoScroll) output.scrollTop = output.scrollHeight;
}

function appendLog(entry) {
    if (!output) return;
    const line = createLogLine(entry);
    output.appendChild(line);
    if (autoScroll) output.scrollTop = output.scrollHeight;

    // Límite visual de 500 líneas
    while (output.children.length > 500) {
        output.removeChild(output.firstChild);
    }
}

function createLogLine(entry) {
    const div = document.createElement('div');
    div.className = 'log-line';

    const ts = document.createElement('span');
    ts.className = 'log-ts';
    ts.textContent = entry.timestamp || '';

    const level = document.createElement('span');
    level.className = `log-level-${entry.level || 'INFO'}`;
    level.textContent = `[${entry.level || 'INFO'}]`;

    const source = document.createElement('span');
    source.className = 'log-source';
    source.textContent = `[${entry.source || 'system'}]`;

    const msg = document.createElement('span');
    msg.className = 'log-msg';
    msg.textContent = entry.message || '';

    div.append(ts, level, source, msg);
    return div;
}

function clearConsole() {
    allLogs = [];
    if (output) output.innerHTML = '<div class="console-welcome"><i class="fa-solid fa-terminal"></i><span>Consola limpiada.</span></div>';
}

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const icon = document.getElementById('autoScrollIcon');
    const label = document.getElementById('autoScrollLabel');
    if (autoScroll) {
        icon.className = 'fa-solid fa-arrow-down';
        label.textContent = 'Auto-scroll ON';
        if (output) output.scrollTop = output.scrollHeight;
    } else {
        icon.className = 'fa-solid fa-arrow-down-up-across-line';
        label.textContent = 'Auto-scroll OFF';
    }
}

function filterLogs() {
    const sel = document.getElementById('logFilter');
    currentFilter = sel?.value || 'all';
    renderAllLogs();
}

// Init
initConsole();
