/**
 * Main application logic for capydocs.
 */

import { renderTree, setActiveFile, enableRootDrop } from './tree.js';
import { loadCodeMirror, createEditor, getContent } from './editor.js';
import { setupAI } from './ai.js';

const API = '/api';
let currentFile = null;
let isDirty = false;
let previewVisible = false;
let previewTimeout = null;

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
    renderTree(container, tree, openFile, {
        onFileDrop: handleFileDrop,
        onDirAction: handleDirAction,
    });
    enableRootDrop(container);
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
            if (previewVisible) updatePreview();
        });

        document.getElementById('current-file').textContent = path;
        setActiveFile(document.getElementById('file-tree'), path);
        if (previewVisible) updatePreview();
    } catch (err) {
        console.error('Failed to open file:', err);
        showToast('Failed to open: ' + err.message, 'error');
    }
}

// --- Save ---
async function saveFile() {
    if (!currentFile) return;
    try {
        await api(`/files/${currentFile}`, {
            method: 'PUT',
            body: JSON.stringify({ content: getContent() }),
        });
        isDirty = false;
        showToast('File saved successfully');
    } catch (err) {
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

// --- Create Folder ---
async function createFolder() {
    const name = prompt('Folder name:');
    if (!name) return;
    try {
        await api(`/dirs/${name}`, { method: 'POST' });
        await loadTree();
        showToast('Folder created');
    } catch (err) {
        showToast('Failed to create folder: ' + err.message, 'error');
    }
}

// --- Rename/Move (inline edit) ---
function renameFile() {
    if (!currentFile) return;
    const fileSpan = document.getElementById('current-file');
    const original = fileSpan.textContent;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = original;
    input.className = 'inline-rename';
    fileSpan.replaceWith(input);
    input.focus();
    input.select();

    let done = false;
    const finish = async (save) => {
        if (done) return;
        done = true;
        const dest = input.value.trim();
        const span = document.createElement('span');
        span.id = 'current-file';
        span.className = 'current-file';

        if (save && dest && dest !== original) {
            try {
                const result = await api(`/files/${original}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ destination: dest }),
                });
                span.textContent = result.path;
                currentFile = result.path;
                await loadTree();
                setActiveFile(document.getElementById('file-tree'), result.path);
                showToast('File renamed');
            } catch (err) {
                span.textContent = original;
                showToast('Failed to rename: ' + err.message, 'error');
            }
        } else {
            span.textContent = original;
        }
        input.replaceWith(span);
    };

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); finish(true); }
        if (e.key === 'Escape') finish(false);
    });
    input.addEventListener('blur', () => finish(false));
}

// --- Drag and Drop ---
async function handleFileDrop(srcPath, destPath) {
    if (srcPath === destPath) return;
    try {
        const result = await api(`/files/${srcPath}`, {
            method: 'PATCH',
            body: JSON.stringify({ destination: destPath }),
        });
        await loadTree();
        if (currentFile === srcPath) {
            currentFile = result.path;
            document.getElementById('current-file').textContent = result.path;
            setActiveFile(document.getElementById('file-tree'), result.path);
        }
        showToast('File moved successfully');
    } catch (err) {
        showToast('Failed to move: ' + err.message, 'error');
    }
}

// --- Directory Actions ---
async function handleDirAction(action, dirPath) {
    if (action === 'new-file') {
        const name = prompt('File name:', 'untitled.md');
        if (!name) return;
        try {
            const path = `${dirPath}/${name}`;
            await api(`/files/${path}`, {
                method: 'POST',
                body: JSON.stringify({ content: '' }),
            });
            await loadTree();
            await openFile(path.endsWith('.md') ? path : path + '.md');
        } catch (err) {
            showToast('Failed to create file: ' + err.message, 'error');
        }
    } else if (action === 'new-folder') {
        const name = prompt('Folder name:');
        if (!name) return;
        try {
            await api(`/dirs/${dirPath}/${name}`, { method: 'POST' });
            await loadTree();
            showToast('Folder created');
        } catch (err) {
            showToast('Failed to create folder: ' + err.message, 'error');
        }
    } else if (action === 'delete-folder') {
        if (!confirm(`Delete folder "${dirPath}"?`)) return;
        try {
            await api(`/dirs/${dirPath}`, { method: 'DELETE' });
            await loadTree();
            showToast('Folder deleted');
        } catch (err) {
            showToast('Failed to delete: ' + err.message, 'error');
        }
    }
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

// --- Preview ---
function togglePreview() {
    const wrapper = document.querySelector('.editor-wrapper');
    const btn = document.getElementById('btn-preview');
    previewVisible = !previewVisible;

    if (previewVisible) {
        wrapper.classList.add('split');
        btn.classList.add('btn-primary');
        updatePreview();
    } else {
        wrapper.classList.remove('split');
        btn.classList.remove('btn-primary');
    }
}

function updatePreview() {
    clearTimeout(previewTimeout);
    previewTimeout = setTimeout(() => {
        const container = document.getElementById('preview-container');
        const content = getContent();
        if (typeof marked !== 'undefined') {
            container.innerHTML = marked.parse(content);
        }
    }, 150);
}

// --- Toolbar ---
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
    document.getElementById('btn-preview').addEventListener('click', togglePreview);
    document.getElementById('btn-new').addEventListener('click', createFile);
    document.getElementById('btn-new-folder').addEventListener('click', createFolder);

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
