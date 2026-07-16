/* console.js — Consola en tiempo real con SSE */

let autoScroll = true;
let allLogs = [];
let currentFilter = 'all';
let eventSource = null;

const output   = document.getElementById('consoleOutput');
const logCount = document.getElementById('logCount');

function _updateCount() {
    if (logCount) logCount.textContent = `${allLogs.length} línea${allLogs.length !== 1 ? 's' : ''}`;
}

async function initConsole() {
    try {
        const data = await api('/api/console/logs');
        if (data.logs) { allLogs = data.logs; renderAllLogs(); }
    } catch (_) {}
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
            _updateCount();
            if (currentFilter === 'all' || entry.level === currentFilter) appendLog(entry);
        } catch (_) {}
    };

    eventSource.onerror = () => { setTimeout(connectSSE, 3000); };
}

function renderAllLogs() {
    if (!output) return;
    output.innerHTML = '';
    const filtered = currentFilter === 'all' ? allLogs : allLogs.filter(l => l.level === currentFilter);
    if (filtered.length === 0) {
        output.innerHTML = '<div class="console-welcome"><i class="fa-solid fa-terminal"></i><span>Sin logs aún...</span></div>';
        _updateCount();
        return;
    }
    const frag = document.createDocumentFragment();
    filtered.forEach(e => frag.appendChild(createLogLine(e)));
    output.appendChild(frag);
    _updateCount();
    if (autoScroll) output.scrollTop = output.scrollHeight;
}

function appendLog(entry) {
    if (!output) return;
    // quitar welcome message si existe
    const welcome = output.querySelector('.console-welcome');
    if (welcome) welcome.remove();

    output.appendChild(createLogLine(entry));
    while (output.children.length > 500) output.removeChild(output.firstChild);
    if (autoScroll) output.scrollTop = output.scrollHeight;
}

function createLogLine(entry) {
    const div = document.createElement('div');
    div.className = `log-line log-line-${entry.level || 'INFO'}`;

    const ts  = document.createElement('span');
    ts.className = 'log-ts';
    ts.textContent = (entry.timestamp || '').slice(11, 19); // solo HH:MM:SS

    const lvl = document.createElement('span');
    lvl.className = `log-level log-level-${entry.level || 'INFO'}`;
    lvl.textContent = (entry.level || 'INFO').padEnd(7);

    const src = document.createElement('span');
    src.className = 'log-source';
    src.textContent = `[${entry.source || 'sys'}]`;

    const msg = document.createElement('span');
    msg.className = 'log-msg';
    msg.textContent = entry.message || '';

    div.append(ts, lvl, src, msg);
    return div;
}

function clearConsole() {
    allLogs = [];
    _updateCount();
    if (output) output.innerHTML = '<div class="console-welcome"><i class="fa-solid fa-terminal"></i><span>Consola limpiada.</span></div>';
}

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const icon = document.getElementById('autoScrollIcon');
    if (!icon) return;
    if (autoScroll) {
        icon.className = 'fa-solid fa-arrow-down';
        if (output) output.scrollTop = output.scrollHeight;
    } else {
        icon.className = 'fa-solid fa-arrow-down-up-across-line';
    }
}

function scrollBottom() {
    if (output) { output.scrollTop = output.scrollHeight; autoScroll = true; }
    const icon = document.getElementById('autoScrollIcon');
    if (icon) icon.className = 'fa-solid fa-arrow-down';
}

function filterLogs() {
    currentFilter = document.getElementById('logFilter')?.value || 'all';
    renderAllLogs();
}

initConsole();
