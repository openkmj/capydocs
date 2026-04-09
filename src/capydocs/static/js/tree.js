/**
 * File tree component — renders a recursive file tree in the sidebar
 * with drag-and-drop support for moving files between folders.
 */

let _onFileClick = null;
let _onFileDrop = null;
let _onDirAction = null;

export function renderTree(container, tree, onFileClick, { onFileDrop, onDirAction } = {}) {
    container.innerHTML = '';
    _onFileClick = onFileClick;
    if (onFileDrop) _onFileDrop = onFileDrop;
    if (onDirAction) _onDirAction = onDirAction;
    const fragment = document.createDocumentFragment();
    buildNodes(fragment, tree);
    container.appendChild(fragment);
}

function buildNodes(parent, items) {
    for (const item of items) {
        if (item.type === 'directory') {
            const wrapper = document.createElement('div');

            const dirItem = document.createElement('div');
            dirItem.className = 'tree-item tree-dir';
            dirItem.dataset.path = item.path;
            dirItem.innerHTML = `<span class="icon">📂</span><span class="name">${esc(item.name)}</span><span class="dir-actions"><span class="dir-btn dir-btn-delete" title="Delete folder">✕</span></span>`;

            const children = document.createElement('div');
            children.className = 'tree-children collapsed';
            buildNodes(children, item.children || []);

            dirItem.querySelector('.icon').textContent = '📁';

            dirItem.addEventListener('click', (e) => {
                if (e.target.closest('.dir-btn')) return;
                children.classList.toggle('collapsed');
                dirItem.querySelector('.icon').textContent = children.classList.contains('collapsed') ? '📁' : '📂';
            });

            // Delete button on folder
            dirItem.querySelector('.dir-btn-delete').addEventListener('click', (e) => {
                e.stopPropagation();
                if (_onDirAction) _onDirAction('delete-folder', item.path);
            });

            // Context menu for directories
            dirItem.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                if (_onDirAction) showDirContextMenu(e, item.path);
            });

            // Drop target for directories
            dirItem.addEventListener('dragover', (e) => {
                e.preventDefault();
                dirItem.classList.add('drag-over');
            });
            dirItem.addEventListener('dragleave', () => {
                dirItem.classList.remove('drag-over');
            });
            dirItem.addEventListener('drop', (e) => {
                e.preventDefault();
                dirItem.classList.remove('drag-over');
                const srcPath = e.dataTransfer.getData('text/plain');
                if (srcPath && _onFileDrop) {
                    const fileName = srcPath.split('/').pop();
                    _onFileDrop(srcPath, `${item.path}/${fileName}`);
                }
            });

            wrapper.appendChild(dirItem);
            wrapper.appendChild(children);
            parent.appendChild(wrapper);
        } else {
            const fileItem = document.createElement('div');
            fileItem.className = 'tree-item';
            fileItem.dataset.path = item.path;
            fileItem.draggable = true;
            fileItem.innerHTML = `<span class="icon">📄</span><span class="name">${esc(item.name)}</span>`;
            fileItem.addEventListener('click', () => _onFileClick(item.path));

            // Drag source for files
            fileItem.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.path);
                fileItem.classList.add('dragging');
            });
            fileItem.addEventListener('dragend', () => {
                fileItem.classList.remove('dragging');
            });

            parent.appendChild(fileItem);
        }
    }
}

// Also allow drop on root (file-tree container itself)
export function enableRootDrop(container) {
    container.addEventListener('dragover', (e) => {
        if (e.target === container) {
            e.preventDefault();
            container.classList.add('drag-over');
        }
    });
    container.addEventListener('dragleave', (e) => {
        if (e.target === container) {
            container.classList.remove('drag-over');
        }
    });
    container.addEventListener('drop', (e) => {
        if (e.target === container || !e.target.closest('.tree-dir')) {
            e.preventDefault();
            container.classList.remove('drag-over');
            const srcPath = e.dataTransfer.getData('text/plain');
            if (srcPath && _onFileDrop) {
                const fileName = srcPath.split('/').pop();
                _onFileDrop(srcPath, fileName);
            }
        }
    });
}

function showDirContextMenu(e, dirPath) {
    // Remove any existing context menu
    document.querySelectorAll('.ctx-menu').forEach(m => m.remove());

    const menu = document.createElement('div');
    menu.className = 'ctx-menu';
    menu.innerHTML = `
        <div class="ctx-item" data-action="new-file">New File Here</div>
        <div class="ctx-item" data-action="new-folder">New Folder Here</div>
        <div class="ctx-item ctx-danger" data-action="delete-folder">Delete Folder</div>
    `;
    menu.style.left = `${e.clientX}px`;
    menu.style.top = `${e.clientY}px`;
    document.body.appendChild(menu);

    menu.addEventListener('click', (ev) => {
        const action = ev.target.dataset.action;
        if (action && _onDirAction) _onDirAction(action, dirPath);
        menu.remove();
    });

    // Close on click outside
    const closeMenu = (ev) => {
        if (!menu.contains(ev.target)) {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        }
    };
    setTimeout(() => document.addEventListener('click', closeMenu), 0);
}

function esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

export function setActiveFile(container, path) {
    container.querySelectorAll('.tree-item.active').forEach(el => el.classList.remove('active'));
    const target = container.querySelector(`.tree-item[data-path="${CSS.escape(path)}"]`);
    if (target) target.classList.add('active');
}
