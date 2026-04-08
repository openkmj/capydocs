/**
 * AI text refinement UI.
 * Side-by-side before/after comparison dialog.
 */

import { getSelection, getContent, replaceSelection, setContent } from './editor.js';

const API = '/api';

const PRESET_LABELS = {
    compact: '📦 Compact',
    fix: '🔧 Fix',
    translate_en: '🇺🇸 English',
    translate_ko: '🇰🇷 Korean',
};

export function setupAI() {
    const toolbar = document.querySelector('.toolbar-right');
    const sep = document.createElement('span');
    sep.className = 'toolbar-separator';
    toolbar.insertBefore(sep, toolbar.querySelector('#btn-save'));

    const btn = document.createElement('button');
    btn.id = 'btn-ai';
    btn.className = 'btn btn-sm toolbar-btn';
    btn.title = 'Capy Groom';
    btn.textContent = '🦫 Groom';
    btn.addEventListener('click', showAIMenu);
    toolbar.insertBefore(btn, toolbar.querySelector('#btn-save'));
}

async function showAIMenu() {
    const sel = getSelection();
    const isFullDoc = !sel;
    const originalText = isFullDoc ? getContent() : sel.text;

    if (!originalText.trim()) {
        alert('No content to refine.');
        return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `
        <div class="dialog ai-dialog">
            <h3>🦫 Capy Groom</h3>
            <div class="ai-presets"></div>
            <input type="text" id="ai-custom-input" placeholder="Or type custom instruction..." />
            <div class="ai-diff" style="display:grid">
                <div class="ai-diff-pane">
                    <div class="ai-diff-label">Before</div>
                    <div class="ai-diff-content" id="ai-before"></div>
                </div>
                <div class="ai-diff-pane">
                    <div class="ai-diff-label">After</div>
                    <textarea class="ai-diff-content ai-diff-after" id="ai-after" placeholder="Select a preset or type an instruction" readonly></textarea>
                </div>
            </div>
            <div class="dialog-actions">
                <button class="btn btn-sm" id="ai-cancel">Cancel</button>
                <button class="btn btn-sm" id="ai-send" style="display:none">Send</button>
                <button class="btn btn-primary btn-sm" id="ai-apply" style="display:none">Apply</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const presetsDiv = overlay.querySelector('.ai-presets');
    const customInput = overlay.querySelector('#ai-custom-input');
    const beforeDiv = overlay.querySelector('#ai-before');
    const afterDiv = overlay.querySelector('#ai-after');
    const sendBtn = overlay.querySelector('#ai-send');
    const applyBtn = overlay.querySelector('#ai-apply');

    beforeDiv.textContent = originalText;

    for (const [key, label] of Object.entries(PRESET_LABELS)) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm';
        btn.textContent = label;
        btn.addEventListener('click', () => doRefine(originalText, '', key));
        presetsDiv.appendChild(btn);
    }

    customInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && customInput.value.trim()) {
            doRefine(originalText, customInput.value.trim(), null);
        }
    });
    customInput.addEventListener('input', () => {
        sendBtn.style.display = customInput.value.trim() ? '' : 'none';
    });
    sendBtn.addEventListener('click', () => {
        if (customInput.value.trim()) {
            doRefine(originalText, customInput.value.trim(), null);
        }
    });

    async function doRefine(text, instruction, preset) {
        afterDiv.value = 'Processing...';
        afterDiv.readOnly = true;
        afterDiv.classList.add('ai-processing');
        applyBtn.style.display = 'none';

        try {
            const body = { text };
            if (preset) body.preset = preset;
            if (instruction) body.instruction = instruction;

            const res = await fetch(`${API}/ai/refine`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'AI request failed');
            }

            const data = await res.json();
            afterDiv.value = data.refined;
            afterDiv.readOnly = false;
            afterDiv.classList.remove('ai-processing');
            applyBtn.style.display = '';
        } catch (err) {
            afterDiv.value = `Error: ${err.message}`;
            afterDiv.classList.remove('ai-processing');
        }
    }

    applyBtn.addEventListener('click', () => {
        const result = afterDiv.value;
        if (isFullDoc) {
            setContent(result);
        } else {
            replaceSelection(sel.from, sel.to, result);
        }
        overlay.remove();
    });

    const close = () => overlay.remove();
    overlay.querySelector('#ai-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
}
