/**
 * AI text refinement UI.
 * Shows a floating menu when text is selected in the editor.
 */

import { getSelection, replaceSelection } from './editor.js';

const API = '/api';

const PRESET_LABELS = {
    concise: '✂️ Concise',
    fix: '🔧 Fix grammar',
    translate_en: '🇺🇸 → English',
    translate_ko: '🇰🇷 → Korean',
    formal: '👔 Formal',
    casual: '😊 Casual',
};

export function setupAI() {
    // Add AI button to toolbar
    const toolbar = document.querySelector('.toolbar-right');
    const sep = document.createElement('span');
    sep.className = 'toolbar-separator';
    toolbar.insertBefore(sep, toolbar.querySelector('#btn-save'));

    const btn = document.createElement('button');
    btn.id = 'btn-ai';
    btn.className = 'btn btn-sm toolbar-btn';
    btn.title = 'AI Refine (select text first)';
    btn.textContent = '✨ AI';
    btn.addEventListener('click', showAIMenu);
    toolbar.insertBefore(btn, toolbar.querySelector('#btn-save'));
}

async function showAIMenu() {
    const sel = getSelection();
    if (!sel) {
        alert('Select some text first to use AI refinement.');
        return;
    }

    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `
        <div class="dialog" style="min-width:400px">
            <h3>✨ AI Refine</h3>
            <div class="ai-selected-text" style="
                background:var(--bg);
                border:1px solid var(--border);
                border-radius:6px;
                padding:8px 10px;
                font-size:13px;
                max-height:120px;
                overflow-y:auto;
                margin-bottom:12px;
                white-space:pre-wrap;
                color:var(--text-muted);
            ">${escHtml(sel.text)}</div>
            <div class="ai-presets" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px"></div>
            <input type="text" id="ai-custom-input" placeholder="Or type custom instruction..." />
            <div id="ai-result" style="display:none;margin-bottom:12px">
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">Result:</div>
                <div id="ai-result-text" style="
                    background:var(--bg);
                    border:1px solid var(--accent);
                    border-radius:6px;
                    padding:8px 10px;
                    font-size:13px;
                    max-height:160px;
                    overflow-y:auto;
                    white-space:pre-wrap;
                "></div>
            </div>
            <div id="ai-loading" style="display:none;color:var(--text-muted);font-size:13px;margin-bottom:12px">
                Processing...
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
    const resultDiv = overlay.querySelector('#ai-result');
    const resultText = overlay.querySelector('#ai-result-text');
    const loadingDiv = overlay.querySelector('#ai-loading');
    const sendBtn = overlay.querySelector('#ai-send');
    const applyBtn = overlay.querySelector('#ai-apply');

    let refinedText = '';

    // Render preset buttons
    for (const [key, label] of Object.entries(PRESET_LABELS)) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm';
        btn.textContent = label;
        btn.addEventListener('click', () => doRefine(sel.text, '', key));
        presetsDiv.appendChild(btn);
    }

    // Custom instruction
    customInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && customInput.value.trim()) {
            doRefine(sel.text, customInput.value.trim(), null);
        }
    });

    // Show send button when typing custom instruction
    customInput.addEventListener('input', () => {
        sendBtn.style.display = customInput.value.trim() ? '' : 'none';
    });
    sendBtn.addEventListener('click', () => {
        if (customInput.value.trim()) {
            doRefine(sel.text, customInput.value.trim(), null);
        }
    });

    async function doRefine(text, instruction, preset) {
        loadingDiv.style.display = '';
        resultDiv.style.display = 'none';
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
            refinedText = data.refined;
            resultText.textContent = refinedText;
            resultDiv.style.display = '';
            applyBtn.style.display = '';
        } catch (err) {
            alert(`AI Error: ${err.message}`);
        } finally {
            loadingDiv.style.display = 'none';
        }
    }

    // Apply
    applyBtn.addEventListener('click', () => {
        replaceSelection(sel.from, sel.to, refinedText);
        overlay.remove();
    });

    // Cancel
    const close = () => overlay.remove();
    overlay.querySelector('#ai-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
