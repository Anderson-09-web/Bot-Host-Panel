/* variables.js */

const BASE = '/api/variables';
const _revealed = {};

/* ── Toggle valor en modal ── */
function toggleVarVis() {
    const inp  = document.getElementById('varValue');
    const icon = document.getElementById('varValueEyeIcon');
    if (!inp) return;
    inp.type = inp.type === 'password' ? 'text' : 'password';
    icon.className = inp.type === 'password' ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
}

/* ── Modal ── */
function openVarModal(id, key, isSecret, desc) {
    id       = id       ?? '';
    key      = key      ?? '';
    isSecret = isSecret ?? false;
    desc     = desc     ?? '';

    const editing = !!id;
    document.getElementById('varModalTitle').innerHTML = editing
        ? '<i class="fa-solid fa-pen"></i> Editar Variable'
        : '<i class="fa-solid fa-plus"></i> Nueva Variable';

    document.getElementById('varEditId').value      = id;
    document.getElementById('varKey').value         = key;
    document.getElementById('varKey').readOnly      = editing;
    document.getElementById('varKey').style.opacity = editing ? '0.6' : '1';
    document.getElementById('varValue').value       = '';
    document.getElementById('varValue').type        = 'password';
    document.getElementById('varValueEyeIcon').className = 'fa-solid fa-eye';
    document.getElementById('varDesc').value        = desc;
    document.getElementById('varIsSecret').checked  = isSecret;

    const hint = document.getElementById('varValueHint');
    hint.textContent = editing ? 'Deja vacío para no cambiar el valor actual.' : '';

    document.getElementById('varModal').classList.add('active');
    setTimeout(() => {
        document.getElementById(editing ? 'varValue' : 'varKey').focus();
    }, 80);
}

function closeVarModal() {
    document.getElementById('varModal').classList.remove('active');
}

/* ── Guardar ── */
async function saveVar() {
    const btn  = document.getElementById('varSaveBtn');
    const id   = document.getElementById('varEditId').value;
    const key  = document.getElementById('varKey').value.trim();
    const val  = document.getElementById('varValue').value;
    const desc = document.getElementById('varDesc').value.trim();
    const sec  = document.getElementById('varIsSecret').checked;

    if (!key) { showToast('La clave es obligatoria.', 'error'); return; }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Guardando...';

    try {
        const r = await api(BASE, 'POST', { key, value: val, is_secret: sec, description: desc });
        if (r.success) {
            showToast(r.message, 'success');
            closeVarModal();
            _upsertRow(r.var);
            _updateCount();
        } else {
            showToast(r.message || 'Error al guardar.', 'error');
        }
    } catch(e) {
        showToast('Error de conexión.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Guardar';
    }
}

/* ── Eliminar ── */
async function deleteVar(id, key) {
    if (!confirm(`¿Eliminar "${key}"?\nSe quitará de os.environ inmediatamente.`)) return;
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

/* ── Revelar secreto ── */
async function toggleReveal(id) {
    const span = document.getElementById(`varval-${id}`);
    const icon = document.getElementById(`reveal-icon-${id}`);
    if (_revealed[id]) {
        span.textContent = '••••••••';
        icon.className = 'fa-solid fa-eye';
        _revealed[id] = false;
        return;
    }
    try {
        const r = await api(`${BASE}/reveal/${id}`);
        if (r.value !== undefined) {
            span.textContent = r.value || '(vacío)';
            icon.className = 'fa-solid fa-eye-slash';
            _revealed[id] = true;
        }
    } catch(_) {}
}

/* ── Helpers DOM ── */
function _upsertRow(v) {
    const tbody = document.getElementById('varsTableBody');
    const table = document.getElementById('varsTable');
    const empty = document.getElementById('varsEmpty');

    if (!tbody) { location.reload(); return; }

    if (empty) empty.style.display = 'none';
    if (table) table.style.display = '';

    const valueCell = v.is_secret
        ? `<span class="var-secret-mask" id="varval-${v.id}">••••••••</span>
           <button class="btn-icon" onclick="toggleReveal(${v.id})">
             <i class="fa-solid fa-eye" id="reveal-icon-${v.id}"></i>
           </button>`
        : `<span class="var-value" id="varval-${v.id}">${_esc(v.value) || '—'}</span>`;

    const badge = v.is_secret
        ? `<span class="var-badge-secret"><i class="fa-solid fa-lock"></i> Secreto</span>` : '';

    const keyEsc  = JSON.stringify(v.key);
    const descEsc = JSON.stringify(v.description || '');

    const html = `
        <td><code class="var-key">${_esc(v.key)}</code>${badge}</td>
        <td class="var-value-cell">${valueCell}</td>
        <td class="var-desc">${_esc(v.description) || '—'}</td>
        <td class="var-actions">
            <button class="btn-icon" onclick="openVarModal(${v.id},${keyEsc},${v.is_secret},${descEsc})">
                <i class="fa-solid fa-pen"></i>
            </button>
            <button class="btn-icon btn-icon-danger" onclick="deleteVar(${v.id},${keyEsc})">
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
        const rows = [...tbody.querySelectorAll('tr')];
        const after = rows.find(r => {
            const k = r.querySelector('.var-key')?.textContent || '';
            return k > v.key;
        });
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
    const table = document.getElementById('varsTable');
    if (!tbody || tbody.children.length === 0) {
        if (empty) empty.style.display = 'flex';
        if (table) table.style.display = 'none';
    }
}

function _esc(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ── Keyboard ── */
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeVarModal();
    if (e.key === 'Enter' && document.getElementById('varModal')?.classList.contains('active')) {
        saveVar();
    }
});
