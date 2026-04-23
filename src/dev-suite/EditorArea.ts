// GAIA Dev Suite — Editor Area (Monaco tabs)
// Monaco is loaded lazily when first file is opened

interface EditorTab {
  path: string;
  label: string;
  dirty: boolean;
}

const _tabs: EditorTab[] = [];
let _activeTab = -1;

export function mountEditorArea(root: HTMLElement): void {
  root.innerHTML = `
    <div class="editor-area">
      <div class="editor-tabs" id="editor-tabs"></div>
      <div class="editor-content" id="editor-content">
        <div class="editor-welcome">
          <h2>🔵 GAIA Dev Suite</h2>
          <p>Open a file from the Explorer or Canon Browser to begin editing.</p>
          <p class="shortcut-hint">Ctrl+P — Quick Open &nbsp;|&nbsp; Ctrl+Shift+D — Toggle Dev Suite</p>
        </div>
      </div>
    </div>
  `;
}

export function openFile(path: string, label: string): void {
  const existing = _tabs.findIndex(t => t.path === path);
  if (existing >= 0) {
    setActiveTab(existing);
    return;
  }
  _tabs.push({ path, label, dirty: false });
  setActiveTab(_tabs.length - 1);
  renderTabs();
}

function setActiveTab(index: number): void {
  _activeTab = index;
  renderTabs();
}

function renderTabs(): void {
  const tabBar = document.getElementById('editor-tabs');
  if (!tabBar) return;
  tabBar.innerHTML = _tabs.map((t, i) => `
    <div class="editor-tab ${i === _activeTab ? 'active' : ''}" data-index="${i}">
      <span class="tab-label">${t.label}${t.dirty ? ' ●' : ''}</span>
      <button class="tab-close" data-index="${i}">✕</button>
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
      setActiveTab(Math.min(_activeTab, _tabs.length - 1));
      renderTabs();
    });
  });
}
