/* files.js — Explorador de archivos */

let currentPath = '';
let selectedItem = null;
let contextTarget = null;

// ── Navegación ───────────────────────────────────
async function navigate(path) {
    currentPath = path;
    selectedItem = null;
    hideContextMenu();

    const grid = document.getElementById('filesGrid');
    if (grid) grid.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> Cargando...</div>';

    try {
        const data = await api(`/api/files/list?path=${encodeURIComponent(path)}`);
        if (data.error) { showToast(data.error, 'error'); return; }
        renderGrid(data.items || []);
        renderBreadcrumbs(data.breadcrumbs || []);
    } catch (e) {
        showToast('Error cargando directorio.', 'error');
    }
}

function renderGrid(items) {
    const grid = document.getElementById('filesGrid');
    if (!grid) return;

    if (items.length === 0) {
        grid.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-folder-open"></i> Carpeta vacía</div>';
        return;
    }

    grid.innerHTML = '';
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.dataset.name = item.name;
        div.dataset.isDir = item.is_dir;
        div.dataset.path = currentPath ? `${currentPath}/${item.name}` : item.name;

        const iconClass = item.is_dir ? 'fa-solid fa-folder folder' : (item.icon || 'fa-solid fa-file');
        div.innerHTML = `
            <i class="${iconClass} file-icon ${item.is_dir ? 'folder' : ''}"></i>
            <span class="file-name">${escHtml(item.name)}</span>
            <span class="file-size">${item.size || ''}</span>
            <span class="file-date">${item.modified || ''}</span>
        `;
        div.addEventListener('dblclick', () => onItemDblClick(item));
        div.addEventListener('click', (e) => selectItem(div, item));
        div.addEventListener('contextmenu', (e) => showContextMenu(e, div, item));
        grid.appendChild(div);
    });
}

function renderBreadcrumbs(crumbs) {
    const bc = document.getElementById('breadcrumbs');
    if (!bc) return;
    bc.innerHTML = crumbs.map((c, i) => {
        const isLast = i === crumbs.length - 1;
        return `<span class="breadcrumb-item ${isLast ? 'active' : ''}"
                    data-path="${escAttr(c.path)}"
                    onclick="navigate('${escAttr(c.path)}')">${escHtml(c.name)}</span>
                ${!isLast ? '<span class="breadcrumb-sep">/</span>' : ''}`;
    }).join('');
}

function onItemDblClick(item) {
    if (item.is_dir) {
        navigate(currentPath ? `${currentPath}/${item.name}` : item.name);
    } else {
        openFile(currentPath ? `${currentPath}/${item.name}` : item.name, item.name);
    }
}

function selectItem(el, item) {
    document.querySelectorAll('.file-item.selected').forEach(e => e.classList.remove('selected'));
    el.classList.add('selected');
    selectedItem = { el, item, path: el.dataset.path };
}

// ── Context Menu ─────────────────────────────────
function showContextMenu(e, el, item) {
    e.preventDefault();
    selectItem(el, item);
    contextTarget = { el, item, path: el.dataset.path };
    const menu = document.getElementById('contextMenu');
    if (!menu) return;
    menu.classList.remove('hidden');
    menu.style.left = `${Math.min(e.clientX, window.innerWidth - 200)}px`;
    menu.style.top  = `${Math.min(e.clientY, window.innerHeight - 300)}px`;
}

function hideContextMenu() {
    document.getElementById('contextMenu')?.classList.add('hidden');
}

document.addEventListener('click', hideContextMenu);
document.addEventListener('keydown', e => { if (e.key === 'Escape') { hideContextMenu(); closeEditor(); } });

function ctxOpen() {
    if (!contextTarget) return;
    if (contextTarget.item.is_dir) {
        navigate(contextTarget.path);
    } else {
        openFile(contextTarget.path, contextTarget.item.name);
    }
}

function ctxDownload() {
    if (!contextTarget || contextTarget.item.is_dir) return;
    window.location.href = `/api/files/download?path=${encodeURIComponent(contextTarget.path)}`;
}

async function ctxRename() {
    if (!contextTarget) return;
    const newName = prompt('Nuevo nombre:', contextTarget.item.name);
    if (!newName || newName === contextTarget.item.name) return;
    const dir = contextTarget.path.split('/').slice(0, -1).join('/');
    const newPath = dir ? `${dir}/${newName}` : newName;
    const r = await api('/api/files/rename', 'POST', { old_path: contextTarget.path, new_path: newPath });
    showToast(r.success ? 'Renombrado correctamente.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) navigate(currentPath);
}

async function ctxCopy() {
    if (!contextTarget) return;
    const newPath = prompt('Copiar a (ruta destino):', contextTarget.path + '_copia');
    if (!newPath) return;
    const r = await api('/api/files/copy', 'POST', { src: contextTarget.path, dst: newPath });
    showToast(r.success ? 'Copiado.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) navigate(currentPath);
}

async function ctxMove() {
    if (!contextTarget) return;
    const newPath = prompt('Mover a (ruta destino):', contextTarget.path);
    if (!newPath) return;
    const r = await api('/api/files/move', 'POST', { src: contextTarget.path, dst: newPath });
    showToast(r.success ? 'Movido.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) navigate(currentPath);
}

async function ctxCompress() {
    if (!contextTarget || !contextTarget.item.is_dir) {
        showToast('Solo se pueden comprimir carpetas.', 'error'); return;
    }
    const r = await api('/api/files/compress', 'POST', { path: contextTarget.path });
    showToast(r.success ? `Comprimido: ${r.zip}` : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) navigate(currentPath);
}

async function ctxDelete() {
    if (!contextTarget) return;
    if (!confirm(`¿Eliminar "${contextTarget.item.name}"? Esta acción no se puede deshacer.`)) return;
    const r = await api('/api/files/delete', 'POST', { path: contextTarget.path });
    showToast(r.success ? 'Eliminado.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) navigate(currentPath);
}

// ── Editor ───────────────────────────────────────
let editingPath = null;

async function openFile(path, name) {
    const r = await api(`/api/files/read?path=${encodeURIComponent(path)}`);
    if (r.error) { showToast(r.error, 'error'); return; }
    editingPath = path;
    document.getElementById('editorTitle').textContent = name;
    document.getElementById('codeEditor').value = r.content;
    document.getElementById('editorModal').classList.remove('hidden');
}

async function saveFile() {
    const content = document.getElementById('codeEditor').value;
    const r = await api('/api/files/write', 'POST', { path: editingPath, content });
    showToast(r.success ? 'Guardado.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) closeEditor();
}

function closeEditor() {
    document.getElementById('editorModal')?.classList.add('hidden');
    editingPath = null;
}

// ── Create Folder ────────────────────────────────
function showCreateFolderModal() {
    document.getElementById('folderName').value = '';
    document.getElementById('folderModal').classList.remove('hidden');
    document.getElementById('folderName').focus();
}

async function createFolder() {
    const name = document.getElementById('folderName').value.trim();
    if (!name) return;
    const path = currentPath ? `${currentPath}/${name}` : name;
    const r = await api('/api/files/create_folder', 'POST', { path });
    showToast(r.success ? 'Carpeta creada.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) { closeModal('folderModal'); navigate(currentPath); }
}

// ── Create File ──────────────────────────────────
function showCreateFileModal() {
    document.getElementById('newFileName').value = '';
    document.getElementById('fileModal').classList.remove('hidden');
    document.getElementById('newFileName').focus();
}

async function createFile() {
    const name = document.getElementById('newFileName').value.trim();
    if (!name) return;
    const path = currentPath ? `${currentPath}/${name}` : name;
    const r = await api('/api/files/write', 'POST', { path, content: '' });
    showToast(r.success ? 'Archivo creado.' : (r.error || 'Error'), r.success ? 'success' : 'error');
    if (r.success) { closeModal('fileModal'); navigate(currentPath); openFile(path, name); }
}

// ── Upload ───────────────────────────────────────
async function uploadFiles(input) {
    const files = input.files;
    if (!files.length) return;

    const formData = new FormData();
    formData.append('path', currentPath);
    for (const f of files) formData.append('files', f);

    showToast('Subiendo archivos...', 'info');
    try {
        const res = await fetch('/api/files/upload', {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF },
            body: formData,
            credentials: 'same-origin',
        });
        const r = await res.json();
        showToast(r.success ? `Subido: ${r.uploaded?.join(', ')}` : 'Error al subir.', r.success ? 'success' : 'error');
        if (r.success) navigate(currentPath);
    } catch (e) {
        showToast('Error al subir archivos.', 'error');
    }
    input.value = '';
}

// ── Search ───────────────────────────────────────
let searchTimer = null;

async function searchFiles(query) {
    clearTimeout(searchTimer);
    const grid = document.getElementById('filesGrid');
    const resultsEl = document.getElementById('searchResults');

    if (!query.trim()) {
        resultsEl?.classList.add('hidden');
        navigate(currentPath);
        return;
    }

    searchTimer = setTimeout(async () => {
        try {
            const data = await api(`/api/files/search?q=${encodeURIComponent(query)}`);
            if (!resultsEl) return;
            if (!data.results?.length) {
                resultsEl.innerHTML = '<div class="loading-spinner">Sin resultados.</div>';
            } else {
                resultsEl.innerHTML = `<div class="files-grid">${
                    data.results.map(r => `
                        <div class="file-item" ondblclick="openFile('${escAttr(r.path)}', '${escAttr(r.name)}')">
                            <i class="${r.icon} file-icon"></i>
                            <span class="file-name">${escHtml(r.name)}</span>
                            <span class="file-size">${escHtml(r.path)}</span>
                        </div>`
                    ).join('')
                }</div>`;
            }
            grid?.classList.add('hidden');
            resultsEl.classList.remove('hidden');
        } catch (_) {}
    }, 300);
}

// ── Modals ───────────────────────────────────────
function closeModal(id) {
    document.getElementById(id)?.classList.add('hidden');
}

// Keyboard shortcuts dentro de modales
document.getElementById('folderName')?.addEventListener('keydown', e => { if (e.key === 'Enter') createFolder(); });
document.getElementById('newFileName')?.addEventListener('keydown', e => { if (e.key === 'Enter') createFile(); });

// ── Helpers ──────────────────────────────────────
function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(str) {
    return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// ── Init ─────────────────────────────────────────
navigate('');
