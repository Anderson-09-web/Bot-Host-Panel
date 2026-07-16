/* settings.js — Configuración del panel + Variables de entorno */

/* ── Helpers ── */
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

/* ── Bot ── */
async function saveBot() {
    const data = {
        token:    document.getElementById('botToken')?.value,
        prefix:   document.getElementById('botPrefix')?.value,
        timezone: document.getElementById('botTimezone')?.value,
    };
    const r = await api('/api/settings/bot', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

/* ── Lavalink ── */
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

/* ── Panel ── */
async function savePanel() {
    const data = { panel_name: document.getElementById('panelName')?.value };
    const r = await api('/api/settings/panel', 'POST', data);
    showToast(r.message || (r.success ? 'Guardado.' : 'Error.'), r.success ? 'success' : 'error');
}

/* ══════════════════════════════════════
   VARIABLES DE ENTORNO
══════════════════════════════════════ */

function openVarModal(id = '', key = '', isSecret = false, desc = '') {
    document.getElementById('varModalTitle').innerHTML =
        id ? '<i class="fa-solid fa-pen"></i> Editar Variable'
           : '<i class="fa-solid fa-plus"></i> Nueva Variable';
    document.getElementById('varEditId').value  = id;
    document.getElementById('varKey').value     = key;
    document.getElementById('varKey').readOnly  = !!id; // no cambiar clave al editar
    document.getElementById('varValue').value   = '';
    document.getElementById('varValue').type    = 'password';
    document.getElementById('varDesc').value    = desc;
    document.getElementById('varIsSecret').checked = isSecret;

    const eyeBtn = document.querySelector('#varModal .toggle-password');
    if (eyeBtn) eyeBtn.querySelector('i').className = 'fa-solid fa-eye';

    document.getElementById('varModal').classList.add('active');
    setTimeout(() => document.getElementById('varKey').focus(), 100);
}

function closeVarModal(e) {
    if (e && e.target !== document.getElementById('varModal')) return;
    document.getElementById('varModal').classList.remove('active');
}

async function saveVar() {
    const id       = document.getElementById('varEditId').value;
    const key      = document.getElementById('varKey').value.trim();
    const value    = document.getElementById('varValue').value;
    const desc     = document.getElementById('varDesc').value.trim();
    const isSecret = document.getElementById('varIsSecret').checked;

    if (!key) { showToast('La clave no puede estar vacía.', 'error'); return; }

    const r = await api('/api/settings/vars', 'POST', { key, value, is_secret: isSecret, description: desc });
    if (r.success) {
        showToast(r.message, 'success');
        document.getElementById('varModal').classList.remove('active');
        // Actualizar o insertar fila en la tabla sin recargar
        _upsertVarRow(r.var);
    } else {
        showToast(r.message || 'Error al guardar.', 'error');
    }
}

async function deleteVar(id, key) {
    if (!confirm(`¿Eliminar la variable "${key}"? Esto la quitará del proceso inmediatamente.`)) return;
    const r = await api(`/api/settings/vars/${id}`, 'DELETE');
    if (r.success) {
        showToast(r.message, 'success');
        document.getElementById(`var-row-${id}`)?.remove();
        _checkEmpty();
    } else {
        showToast(r.message || 'Error al eliminar.', 'error');
    }
}

/* Revelar valor de una variable secreta desde la API */
const _revealed = {};
async function toggleReveal(id, key) {
    const span = document.getElementById(`varval-${id}`);
    const icon = document.getElementById(`reveal-icon-${id}`);
    if (_revealed[id]) {
        span.textContent = '••••••••';
        icon.className = 'fa-solid fa-eye';
        _revealed[id] = false;
        return;
    }
    // Pedir el valor real — GET vars y buscar por id
    const r = await api('/api/settings/vars');
    const found = r.vars?.find(v => v.id === id);
    if (found) {
        // Cargar valor real temporalmente
        const realR = await api('/api/settings/vars/reveal/' + id);
        if (realR?.value !== undefined) {
            span.textContent = realR.value || '(vacío)';
            icon.className = 'fa-solid fa-eye-slash';
            _revealed[id] = true;
        }
    }
}

/* Insertar o actualizar fila en la tabla */
function _upsertVarRow(v) {
    const tbody = document.getElementById('varsTableBody');
    const empty = document.getElementById('varsEmpty');

    // Ocultar empty state si existía
    if (empty) empty.style.display = 'none';
    if (!tbody) { location.reload(); return; }

    let row = document.getElementById(`var-row-${v.id}`);
    const valueCell = v.is_secret
        ? `<span class="var-secret-mask" id="varval-${v.id}">••••••••</span>
           <button class="btn-icon" title="Revelar" onclick="toggleReveal(${v.id}, '${v.key}')">
             <i class="fa-solid fa-eye" id="reveal-icon-${v.id}"></i>
           </button>`
        : `<span class="var-value" id="varval-${v.id}">${v.value || '—'}</span>`;

    const html = `
        <td><code class="var-key">${v.key}</code>${v.is_secret ? '<span class="var-badge-secret"><i class="fa-solid fa-lock"></i> Secreto</span>' : ''}</td>
        <td class="var-value-cell">${valueCell}</td>
        <td class="var-desc">${v.description || '—'}</td>
        <td class="var-date">${v.updated_at || '—'}</td>
        <td class="var-actions">
            <button class="btn-icon" title="Editar"
                    onclick="openVarModal(${v.id}, '${v.key}', ${v.is_secret}, '${v.description || ''}')">
                <i class="fa-solid fa-pen"></i>
            </button>
            <button class="btn-icon btn-icon-danger" title="Eliminar"
                    onclick="deleteVar(${v.id}, '${v.key}')">
                <i class="fa-solid fa-trash"></i>
            </button>
        </td>`;

    if (row) {
        row.innerHTML = html;
    } else {
        row = document.createElement('tr');
        row.id = `var-row-${v.id}`;
        row.innerHTML = html;
        // Si no hay tbody aún, crear la tabla completa
        if (!tbody.closest('table')) { location.reload(); return; }
        tbody.appendChild(row);
    }
}

function _checkEmpty() {
    const tbody = document.getElementById('varsTableBody');
    const empty = document.getElementById('varsEmpty');
    if (tbody && tbody.children.length === 0 && empty) {
        empty.style.display = 'flex';
    }
}

// Cerrar modal con Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') document.getElementById('varModal')?.classList.remove('active');
});
