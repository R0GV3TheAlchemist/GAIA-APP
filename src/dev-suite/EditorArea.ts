// GAIA Dev Suite — Editor Area (Monaco tabs)
// Phase 4.2 — Monaco integrated with file open/save

import { mountMonacoEditor, openInEditor } from './MonacoEditor';
import { readTextFile, writeTextFile } from '@tauri-apps/plugin-fs';

interface EditorTab {
  path: string;
  label: string;
  dirty: boolean;
}

const _tabs: EditorTab[] = [];
let _activeTab = -1;
let _editorMounted = false;

export function mountEditorArea(root: HTMLElement): void {
  root.innerHTML = `
    <div class="editor-area">
      <div class="editor-tabs" id="editor-tabs"></div>
      <div class="editor-content" id="editor-content">
        <div class="editor-welcome" id="editor-welcome">
          <h2>&#128309; GAIA Dev Suite</h2>
          <p>Open a file from the Explorer or Canon Browser to begin editing.</p>
          <p class="shortcut-hint">Ctrl+P &mdash; Quick Open &nbsp;|&nbsp; Ctrl+Shift+D &mdash; Toggle Dev Suite</p>
        </div>
        <div id="monaco-container" style="width:100%;height:100%;display:none;"></div>
      </div>
    </div>
  `;
}

export async function openFile(path: string, label: string): Promise<void> {
  const existing = _tabs.findIndex(t => t.path === path);
  if (existing >= 0) {
    await setActiveTab(existing);
    return;
  }
  _tabs.push({ path, label, dirty: false });
  await setActiveTab(_tabs.length - 1);
}

async function setActiveTab(index: number): Promise<void> {
  _activeTab = index;
  renderTabs();
  await loadFileIntoEditor(_tabs[index].path);
}

async function loadFileIntoEditor(path: string): Promise<void> {
  const welcome = document.getElementById('editor-welcome');
  const container = document.getElementById('monaco-container');
  if (!container) return;

  if (welcome) welcome.style.display = 'none';
  container.style.display = 'block';

  if (!_editorMounted) {
    await mountMonacoEditor(container, { onSave: saveFile });
    _editorMounted = true;
  }

  try {
    const content = await readTextFile(path);
    openInEditor(path, content);
  } catch (e) {
    openInEditor(path, `// Could not read file: ${path}\n// ${e}`);
  }
}

async function saveFile(path: string, content: string): Promise<void> {
  try {
    await writeTextFile(path, content);
    const tab = _tabs.find(t => t.path === path);
    if (tab) { tab.dirty = false; renderTabs(); }
  } catch (e) {
    console.error('[GAIA] Save failed:', e);
  }
}

function renderTabs(): void {
  const tabBar = document.getElementById('editor-tabs');
  if (!tabBar) return;
  tabBar.innerHTML = _tabs.map((t, i) => `
    <div class="editor-tab ${i === _activeTab ? 'active' : ''}" data-index="${i}">
      <span class="tab-label">${t.label}${t.dirty ? ' &#9679;' : ''}</span>
      <button class="tab-close" data-index="${i}">&#x2715;</button>
    </div>
  `).join('');

  tabBar.querySelectorAll<HTMLElement>('.editor-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      if ((e.target as HTMLElement).classList.contains('tab-close')) return;
      setActiveTab(Number(tab.dataset.index));
    });
  });

  tabBar.querySelectorAll<HTMLButtonElement>('.tab-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = Number(btn.dataset.index);
      _tabs.splice(idx, 1);
      const next = Math.min(_activeTab, _tabs.length - 1);
      if (_tabs.length === 0) {
        const welcome = document.getElementById('editor-welcome');
        const container = document.getElementById('monaco-container');
        if (welcome) welcome.style.display = 'flex';
        if (container) container.style.display = 'none';
        _activeTab = -1;
      } else {
        setActiveTab(next);
      }
      renderTabs();
    });
  });
}
