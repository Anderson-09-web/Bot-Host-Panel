/* variables.js — Gestión de Variables de Entorno */

const BASE = '/api/variables';
const _revealed = {};

function toggleVis(id, btn) {
    const input = document.getElementById(id);
    const icon = btn.querySelector('i');
    input.type = input.type === 'password' ? 'text' : 'password';
    icon.className = input.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
}

/* ── Modal ── */
function openVarModal(id = '', key = '', isSecret = false, desc = '') {
    document.getElementById('varModalTitle').innerHTML = id
        ? '<i class="fa-solid fa-pen"></i> Editar Variable'
        : '<i class="fa-solid fa-plus"></i> Nueva Variable';
    document.getElementById('varEditId').value  = id;
    document.getElementById('varKey').value     = key;
    document.getElementById('varKey').readOnly  = !!id;
    document.getElementById('varKey').style.opacity = id ? '0.5' : '1';
    document.getElementById('varValue').value   = '';
    document.getElementById('varValue').type    = 'password';
    document.getElementById('varDesc').value    = desc;
    document.getElementById('varIsSecret').checked = isSecret;
    const eye = document.querySelector('#varModal .toggle-password i');
    if (eye) eye.className = 'fa-solid fa-eye';
    document.getElementById('varModal').classList.add('active');
    setTimeout(() => document.getElementById(id ? 'varValue' : 'varKey').focus(), 80);
}

function closeVarModal() {
    document.getElementById('varModal').classList.remove('active');
}

/* ── CRUD ── */
async function saveVar() {
    const id       = document.getElementById('varEditId').value;
    const key      = document.getElementById('varKey').value.trim();
    const value    = document.getElementById('varValue').value;
    const desc     = document.getElementById('varDesc').value.trim();
    const isSecret = document.getElementById('varIsSecret').checked;

    if (!key) { showToast('La clave no puede estar vacía.', 'error'); return; }

    const r = await api(BASE, 'POST', { key, value, is_secret: isSecret, description: desc });
    if (r.success) {
        showToast(r.message, 'success');
        closeVarModal();
        _upsertRow(r.var);
        _updateCount();
    } else {
        showToast(r.message || 'Error al guardar.', 'error');
    }
}

async function deleteVar(id, key) {
    if (!confirm(`¿Eliminar "${key}"?\nEsto la quitará del proceso inmediatamente.`)) return;
    const r = await api(`${BASE}/${id}`, 'DELETE');
    if (r.success) {
        showToast(r.message, 'success');
        document.getElementById(`var-row-${id}`)?.remove();
        _updateCount();
        _checkEmpty();
    } else {
        showToast(r.message || 'Error.', 'error');
    }
}

async function toggleReveal(id) {
    const span = document.getElementById(`varval-${id}`);
    const icon = document.getElementById(`reveal-icon-${id}`);
    if (_revealed[id]) {
        span.textContent = '••••••••';
        icon.className = 'fa-solid fa-eye';
        _revealed[id] = false;
        return;
    }
    const r = await api(`${BASE}/reveal/${id}`);
    if (r.value !== undefined) {
        span.textContent = r.value || '(vacío)';
        icon.className = 'fa-solid fa-eye-slash';
        _revealed[id] = true;
    }
}

/* ── UI helpers ── */
function _upsertRow(v) {
    const tbody = document.getElementById('varsTableBody');
    const empty = document.getElementById('varsEmpty');
    if (empty) empty.style.display = 'none';

    if (!tbody) { location.reload(); return; }

    const valueCell = v.is_secret
        ? `<span class="var-secret-mask" id="varval-${v.id}">••••••••</span>
           <button class="btn-icon" title="Revelar" onclick="toggleReveal(${v.id})">
             <i class="fa-solid fa-eye" id="reveal-icon-${v.id}"></i>
           </button>`
        : `<span class="var-value" id="varval-${v.id}">${v.value || '—'}</span>`;

    const secretBadge = v.is_secret
        ? `<span class="var-badge-secret"><i class="fa-solid fa-lock"></i> Secreto</span>` : '';

    const html = `
        <td><code class="var-key">${v.key}</code>${secretBadge}</td>
        <td class="var-value-cell">${valueCell}</td>
        <td class="var-desc">${v.description || '—'}</td>
        <td class="var-date">${v.updated_at || '—'}</td>
        <td class="var-actions">
            <button class="btn-icon" title="Editar"
                    onclick="openVarModal(${v.id},'${v.key}',${v.is_secret},'${(v.description||'').replace(/'/g,"\\'")}')">
                <i class="fa-solid fa-pen"></i>
            </button>
            <button class="btn-icon btn-icon-danger" title="Eliminar"
                    onclick="deleteVar(${v.id},'${v.key}')">
                <i class="fa-solid fa-trash"></i>
            </button>
        </td>`;

    let row = document.getElementById(`var-row-${v.id}`);
    if (row) {
        row.innerHTML = html;
    } else {
        row = document.createElement('tr');
        row.id = `var-row-${v.id}`;
        row.innerHTML = html;
        // Insertar en orden alfabético
        const rows = [...tbody.querySelectorAll('tr')];
        const after = rows.find(r => r.querySelector('.var-key')?.textContent > v.key);
        tbody.insertBefore(row, after || null);
    }
}

function _updateCount() {
    const badge = document.getElementById('varCount');
    if (badge) badge.textContent = document.getElementById('varsTableBody')?.children.length ?? 0;
}

function _checkEmpty() {
    const tbody = document.getElementById('varsTableBody');
    const empty = document.getElementById('varsEmpty');
    if (tbody && tbody.children.length === 0 && empty) empty.style.display = 'flex';
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeVarModal();
});
