// GAIA Dev Suite — Activity Bar (left rail)

export type DevPanel = 'explorer' | 'git' | 'canon' | 'tests' | 'inspector';

const ICONS: Record<DevPanel, string> = {
  explorer: '📁',
  git:      '⎇',
  canon:    '📜',
  tests:    '✅',
  inspector:'🔬',
};

let _activePanel: DevPanel = 'explorer';
const _listeners: Array<(panel: DevPanel) => void> = [];

export function onPanelChange(fn: (panel: DevPanel) => void): void {
  _listeners.push(fn);
}

export function mountActivityBar(root: HTMLElement): void {
  root.innerHTML = `
    <div class="activity-bar">
      ${(Object.keys(ICONS) as DevPanel[]).map(p => `
        <button class="ab-btn ${p === _activePanel ? 'active' : ''}" data-panel="${p}" title="${p}">
          ${ICONS[p]}
        </button>
      `).join('')}
    </div>
  `;

  root.querySelectorAll<HTMLButtonElement>('.ab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.dataset.panel as DevPanel;
      _activePanel = panel;
      root.querySelectorAll('.ab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _listeners.forEach(fn => fn(panel));
    });
  });
}
