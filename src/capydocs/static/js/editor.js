/**
 * CodeMirror 6 editor wrapper.
 * Uses a pre-built local bundle to avoid CDN dependency conflicts.
 */

let EditorView, EditorState, basicSetup, markdown, oneDark;

export async function loadCodeMirror() {
    const cm = await import('./cm-bundle.js');
    EditorView = cm.EditorView;
    EditorState = cm.EditorState;
    basicSetup = cm.basicSetup;
    markdown = cm.markdown;
    oneDark = cm.oneDark;
}

let view = null;
let fallbackTextarea = null;
let onChangeCallback = null;

export function isLoaded() {
    return !!EditorView;
}

export function createEditor(container, content = '', onChange = null) {
    onChangeCallback = onChange;

    // Clean up previous editor
    if (view) { view.destroy(); view = null; }
    if (fallbackTextarea) { fallbackTextarea.remove(); fallbackTextarea = null; }

    const placeholder = container.querySelector('#editor-placeholder');
    if (placeholder) placeholder.remove();

    // If CodeMirror not loaded yet, use a plain textarea as fallback
    if (!EditorView) {
        fallbackTextarea = document.createElement('textarea');
        Object.assign(fallbackTextarea.style, {
            width: '100%', height: '100%', background: 'var(--bg)',
            color: 'var(--text)', border: 'none', padding: '16px',
            fontFamily: 'var(--font-mono)', fontSize: '14px',
            lineHeight: '1.6', resize: 'none', outline: 'none',
        });
        fallbackTextarea.value = content;
        fallbackTextarea.addEventListener('input', () => {
            if (onChangeCallback) onChangeCallback(fallbackTextarea.value);
        });
        container.appendChild(fallbackTextarea);
        return null;
    }

    const extensions = [
        EditorView.updateListener.of((update) => {
            if (update.docChanged && onChangeCallback) {
                onChangeCallback(update.state.doc.toString());
            }
        }),
        EditorView.theme({
            '&': { height: '100%' },
            '.cm-scroller': { overflow: 'auto' },
        }),
    ];

    // basicSetup can be an array of extensions — spread it
    if (basicSetup) {
        const setup = Array.isArray(basicSetup) ? basicSetup : [basicSetup];
        extensions.unshift(...setup);
    }
    if (markdown) extensions.push(markdown());
    if (oneDark) extensions.push(oneDark);

    const state = EditorState.create({ doc: content, extensions });
    view = new EditorView({ state, parent: container });
    return view;
}

export function getContent() {
    if (fallbackTextarea) return fallbackTextarea.value;
    return view ? view.state.doc.toString() : '';
}

export function setContent(content) {
    if (!view) return;
    view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: content },
    });
}

export function getSelection() {
    if (!view) return null;
    const { from, to } = view.state.selection.main;
    if (from === to) return null;
    return {
        from,
        to,
        text: view.state.sliceDoc(from, to),
    };
}

export function replaceSelection(from, to, text) {
    if (!view) return;
    view.dispatch({ changes: { from, to, insert: text } });
}

export function insertAtCursor(text) {
    if (!view) return;
    const pos = view.state.selection.main.head;
    view.dispatch({ changes: { from: pos, insert: text } });
}

export function wrapSelection(before, after) {
    if (!view) return;
    const sel = view.state.selection.main;
    const selected = view.state.sliceDoc(sel.from, sel.to);
    view.dispatch({
        changes: { from: sel.from, to: sel.to, insert: `${before}${selected}${after}` },
    });
}
