/**
 * Main application logic for capydocs.
 */

import { renderTree, setActiveFile } from './tree.js';
import { loadCodeMirror, createEditor, getContent, wrapSelection, insertAtCursor } from './editor.js';
import { setupAI } from './ai.js';

const API = '/api';
let currentFile = null;
let isDirty = false;

// --- API helpers ---
async function api(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// --- File tree ---
async function loadTree() {
    const tree = await api('/tree');
    const container = document.getElementById('file-tree');
    renderTree(container, tree, openFile);
}

async function openFile(path) {
    if (isDirty && !confirm('Unsaved changes will be lost. Continue?')) return;
    try {
        const data = await api(`/files/${path}`);
        currentFile = path;
        isDirty = false;

        const editorContainer = document.getElementById('editor-container');
        createEditor(editorContainer, data.content, () => {
            isDirty = true;
            updateStatus('unsaved');
        });

        document.getElementById('current-file').textContent = path;
        setActiveFile(document.getElementById('file-tree'), path);
        updateStatus('');
    } catch (err) {
        console.error('Failed to open file:', err);
        updateStatus('open failed: ' + err.message);
    }
}

// --- Save ---
async function saveFile() {
    if (!currentFile) return;
    try {
        updateStatus('saving...', 'pending');
        await api(`/files/${currentFile}`, {
            method: 'PUT',
            body: JSON.stringify({ content: getContent() }),
        });
        isDirty = false;
        updateStatus('✓ Saved', 'success');
        showToast('File saved successfully');
        setTimeout(() => { if (!isDirty) updateStatus(''); }, 3000);
    } catch (err) {
        updateStatus('✗ Save failed', 'error');
        showToast('Failed to save: ' + err.message, 'error');
        console.error('Failed to save:', err);
    }
}

// --- Create ---
async function createFile() {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `
        <div class="dialog">
            <h3>New Markdown File</h3>
            <input type="text" id="new-file-input" placeholder="path/to/file.md" autofocus />
            <div class="dialog-actions">
                <button class="btn btn-sm" id="dialog-cancel">Cancel</button>
                <button class="btn btn-primary btn-sm" id="dialog-create">Create</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const input = overlay.querySelector('#new-file-input');
    input.focus();

    return new Promise((resolve) => {
        const close = () => { overlay.remove(); resolve(); };

        overlay.querySelector('#dialog-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        const doCreate = async () => {
            const path = input.value.trim();
            if (!path) return;
            try {
                await api(`/files/${path}`, {
                    method: 'POST',
                    body: JSON.stringify({ content: '' }),
                });
                await loadTree();
                await openFile(path.endsWith('.md') ? path : path + '.md');
            } catch (err) {
                console.error('Failed to create:', err);
            }
            close();
        };

        overlay.querySelector('#dialog-create').addEventListener('click', doCreate);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doCreate(); });
    });
}

// --- Rename/Move ---
async function renameFile() {
    if (!currentFile) return;
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `
        <div class="dialog">
            <h3>Rename / Move File</h3>
            <input type="text" id="rename-file-input" value="${esc(currentFile)}" autofocus />
            <div class="dialog-actions">
                <button class="btn btn-sm" id="dialog-cancel">Cancel</button>
                <button class="btn btn-primary btn-sm" id="dialog-rename">Rename</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const input = overlay.querySelector('#rename-file-input');
    input.focus();
    input.select();

    return new Promise((resolve) => {
        const close = () => { overlay.remove(); resolve(); };

        overlay.querySelector('#dialog-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        const doRename = async () => {
            const dest = input.value.trim();
            if (!dest || dest === currentFile) { close(); return; }
            try {
                const result = await api(`/files/${currentFile}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ destination: dest }),
                });
                await loadTree();
                await openFile(result.path);
                showToast('File renamed successfully');
            } catch (err) {
                showToast('Failed to rename: ' + err.message, 'error');
            }
            close();
        };

        overlay.querySelector('#dialog-rename').addEventListener('click', doRename);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doRename(); });
    });
}

// --- Delete ---
async function deleteFile() {
    if (!currentFile) return;
    if (!confirm(`Delete "${currentFile}"?`)) return;
    try {
        await api(`/files/${currentFile}`, { method: 'DELETE' });
        currentFile = null;
        isDirty = false;
        document.getElementById('current-file').textContent = 'No file selected';
        document.getElementById('editor-container').innerHTML =
            '<div id="editor-placeholder" class="editor-placeholder">Select a file from the sidebar to start editing</div>';
        await loadTree();
    } catch (err) {
        console.error('Failed to delete:', err);
    }
}

// --- Toolbar ---
function updateStatus(text, type = '') {
    const el = document.getElementById('save-status');
    el.textContent = text;
    el.className = 'save-status';
    if (type === 'success') el.classList.add('status-success');
    else if (type === 'error') el.classList.add('status-error');
    else if (type === 'pending') el.classList.add('status-pending');
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-visible'));
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

function setupToolbar() {
    document.getElementById('btn-save').addEventListener('click', saveFile);
    document.getElementById('btn-delete').addEventListener('click', deleteFile);
    document.getElementById('btn-rename').addEventListener('click', renameFile);
    document.getElementById('btn-new').addEventListener('click', createFile);

    document.getElementById('btn-bold').addEventListener('click', () => wrapSelection('**', '**'));
    document.getElementById('btn-italic').addEventListener('click', () => wrapSelection('*', '*'));
    document.getElementById('btn-heading').addEventListener('click', () => insertAtCursor('## '));
    document.getElementById('btn-link').addEventListener('click', () => wrapSelection('[', '](url)'));
    document.getElementById('btn-list').addEventListener('click', () => insertAtCursor('- '));

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            saveFile();
        }
    });
}

// --- Search (server-side) ---
let searchTimeout = null;

function setupSearch() {
    const input = document.getElementById('search-input');
    const treeContainer = document.getElementById('file-tree');

    input.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const query = input.value.trim();

        if (!query) {
            // Restore tree view
            loadTree();
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const results = await api(`/search?q=${encodeURIComponent(query)}`);
                renderSearchResults(treeContainer, results);
            } catch {
                // Fallback to showing full tree
            }
        }, 300);
    });
}

function renderSearchResults(container, results) {
    container.innerHTML = '';
    if (results.length === 0) {
        container.innerHTML = '<div class="tree-item" style="color:var(--text-muted)">No results found</div>';
        return;
    }
    const fragment = document.createDocumentFragment();
    for (const r of results) {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `<div>${esc(r.name)}</div>` +
            (r.context ? `<div class="match-context">${esc(r.context)}</div>` : '');
        item.addEventListener('click', () => openFile(r.path));
        fragment.appendChild(item);
    }
    container.appendChild(fragment);
}

function esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// --- Init ---
async function init() {
    // Load tree and toolbar first (no CDN dependency)
    await loadTree();
    setupToolbar();
    setupSearch();

    // Load CodeMirror in parallel — don't block UI if CDN is slow
    loadCodeMirror()
        .then(() => {
            setupAI();
            console.log('capydocs: CodeMirror loaded');
        })
        .catch(err => console.error('capydocs: CodeMirror load failed:', err));
}

init().catch(err => console.error('capydocs init failed:', err));
