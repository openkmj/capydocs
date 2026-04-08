/**
 * File tree component — renders a recursive file tree in the sidebar.
 */

export function renderTree(container, tree, onFileClick) {
    container.innerHTML = '';
    const fragment = document.createDocumentFragment();
    buildNodes(fragment, tree, onFileClick);
    container.appendChild(fragment);
}

function buildNodes(parent, items, onFileClick) {
    for (const item of items) {
        if (item.type === 'directory') {
            const wrapper = document.createElement('div');

            const dirItem = document.createElement('div');
            dirItem.className = 'tree-item';
            dirItem.innerHTML = `<span class="icon">📂</span><span class="name">${esc(item.name)}</span>`;

            const children = document.createElement('div');
            children.className = 'tree-children';
            buildNodes(children, item.children || [], onFileClick);

            dirItem.addEventListener('click', () => {
                children.classList.toggle('collapsed');
                dirItem.querySelector('.icon').textContent = children.classList.contains('collapsed') ? '📁' : '📂';
            });

            wrapper.appendChild(dirItem);
            wrapper.appendChild(children);
            parent.appendChild(wrapper);
        } else {
            const fileItem = document.createElement('div');
            fileItem.className = 'tree-item';
            fileItem.dataset.path = item.path;
            fileItem.innerHTML = `<span class="icon">📄</span><span class="name">${esc(item.name)}</span>`;
            fileItem.addEventListener('click', () => onFileClick(item.path));
            parent.appendChild(fileItem);
        }
    }
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
