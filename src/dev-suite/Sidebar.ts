// GAIA Dev Suite — Collapsible Sidebar
// Shows: File Explorer | Git Panel | Canon Browser (switched by ActivityBar)

import { onPanelChange, DevPanel } from './ActivityBar';

export function mountSidebar(root: HTMLElement): void {
  renderPanel(root, 'explorer');
  onPanelChange((panel) => renderPanel(root, panel));
}

function renderPanel(root: HTMLElement, panel: DevPanel): void {
  const titles: Record<DevPanel, string> = {
    explorer: '📁 Explorer',
    git:      '⎇ Source Control',
    canon:    '📜 Canon Browser',
    tests:    '✅ Test Runner',
    inspector:'🔬 Engine Inspector',
  };
  root.innerHTML = `
    <div class="sidebar-panel">
      <div class="sidebar-header">${titles[panel]}</div>
      <div class="sidebar-content" id="sidebar-content-${panel}">
        <span class="sidebar-placeholder">Loading ${panel}...</span>
      </div>
    </div>
  `;
}
