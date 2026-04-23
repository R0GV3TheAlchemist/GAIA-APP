// GAIA Dev Suite — Main orchestrator
// Phase 4.1 — Shell & Layout
// Ctrl+Shift+D toggles the overlay

import './DevSuite.css';
import { mountActivityBar }   from './ActivityBar';
import { mountSidebar }       from './Sidebar';
import { mountEditorArea }    from './EditorArea';
import { mountBottomPanel }   from './BottomPanel';
import { mountRightSidebar }  from './RightSidebar';
import { mountStatusBar }     from './StatusBar';

let _mounted = false;
let _visible = false;
let _container: HTMLElement | null = null;

export function initDevSuite(): void {
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
      e.preventDefault();
      toggleDevSuite();
    }
  });
}

export function toggleDevSuite(): void {
  if (!_mounted) {
    mountDevSuite();
  } else {
    _visible = !_visible;
    if (_container) {
      _container.style.display = _visible ? 'grid' : 'none';
    }
  }
}

function mountDevSuite(): void {
  _container = document.createElement('div');
  _container.id = 'gaia-dev-suite';
  _container.className = 'dev-suite';
  _container.innerHTML = `
    <div class="ds-activity-bar"  id="ds-activity-bar"></div>
    <div class="ds-sidebar"       id="ds-sidebar"></div>
    <div class="ds-editor-area"   id="ds-editor-area"></div>
    <div class="ds-right-sidebar" id="ds-right-sidebar"></div>
    <div class="ds-bottom-panel"  id="ds-bottom-panel"></div>
    <div class="ds-status-bar"    id="ds-status-bar"></div>
  `;
  document.body.appendChild(_container);

  mountActivityBar(document.getElementById('ds-activity-bar')!);
  mountSidebar(document.getElementById('ds-sidebar')!);
  mountEditorArea(document.getElementById('ds-editor-area')!);
  mountRightSidebar(document.getElementById('ds-right-sidebar')!);
  mountBottomPanel(document.getElementById('ds-bottom-panel')!);
  mountStatusBar(document.getElementById('ds-status-bar')!);

  _mounted = true;
  _visible = true;
}
