// GAIA App — Top-level layout with tab navigation
// Views: SEARCH | GAIAN | CHAT | SHELL | MEMORY | NOOSPHERE | CANON | QUANTUM | DIMENSIONS
// Canon Ref: C42, C43, C44

import './app.css';
import './search/Search.css';
import './shell/Shell.css';
import './chat/Chat.css';
import './memory/Memory.css';
import './noosphere/NoosphereTab.css';
import './canon/CanonTab.css';
import './dimensions/DimensionalMonitor.css';
import { mountSearch }            from './search/Search';
import { mountShell }             from './shell/Shell';
import { mountChat }              from './chat/Chat';
import { mountMemory }            from './memory/Memory';
import { mountGaianChat }         from './gaian/GaianChatView';
import {
  mountNoosphereTab,
  unmountNoosphereTab,
} from './noosphere';
import { mountCanonTab }          from './canon/CanonTab';
import { mountQuantumTab }        from './quantum/QuantumTab';
import { mountDimensionalMonitor } from './dimensions/DimensionalMonitor';
import { appDataDir, join, resolveResource } from '@tauri-apps/api/path';
import { exists, mkdir, copyFile, readDir }  from '@tauri-apps/plugin-fs';
import { listen }                 from '@tauri-apps/api/event';
import { checkForUpdates }        from './updater';
import { logInfo, logWarn, logError } from './diagnostics';
import { API_BASE } from './config';

export { API_BASE };

// ── First-launch: seed %APPDATA%\GAIA\canon\ from bundled resources ────
async function ensureAppDataDirs(): Promise<void> {
  try {
    const appData = await appDataDir();
    const dirs = ['canon', 'logs', 'config'];
    for (const dir of dirs) {
      const dirPath = await join(appData, dir);
      if (!(await exists(dirPath))) {
        await mkdir(dirPath, { recursive: true });
        logInfo('app', `Created AppData dir: ${dir}`);
      }
    }
    const canonDest = await join(appData, 'canon');
    const canonDestEntries = await readDir(canonDest);
    if (canonDestEntries.length === 0) {
      try {
        const canonSrc = await resolveResource('canon');
        const srcEntries = await readDir(canonSrc);
        for (const entry of srcEntries) {
          const srcFile  = await join(canonSrc,  entry.name);
          const destFile = await join(canonDest, entry.name);
          await copyFile(srcFile, destFile);
        }
        logInfo('app', `Seeded ${srcEntries.length} canon docs to AppData`);
      } catch (e) {
        logWarn('app', 'Could not seed canon docs (may not be bundled yet)', e);
      }
    }
  } catch (e) {
    logError('app', 'ensureAppDataDirs failed', e);
  }
}

// ── Updater ─────────────────────────────────────────────────────────────────
async function initUpdater(): Promise<void> {
  const unlisten = await listen('sidecar:ready', async () => {
    unlisten();
    logInfo('updater', 'sidecar:ready received — scheduling update check');
    await new Promise(r => setTimeout(r, 2000));
    await checkForUpdates();
  });
}

export class App {
  constructor() {
    logInfo('app', 'GAIA App initialising');
    this.mount();
    ensureAppDataDirs();
    initUpdater();
  }

  private mount() {
    const root = document.querySelector<HTMLDivElement>('#app')!;
    root.innerHTML = `
<div class="gaia-app">
  <nav class="tab-nav">
    <button class="tab-btn active" data-view="search">&#128269; Search</button>
    <button class="tab-btn"        data-view="gaian">&#9672; GAIAN</button>
    <button class="tab-btn"        data-view="chat">&#9670; Chat</button>
    <button class="tab-btn"        data-view="shell">&gt; Shell</button>
    <button class="tab-btn"        data-view="memory">&#9638; Memory</button>
    <button class="tab-btn"        data-view="noosphere">&#127760; Noosphere</button>
    <button class="tab-btn"        data-view="canon">&#128220; Canon</button>
    <button class="tab-btn"        data-view="quantum">&#10731; Quantum</button>
    <button class="tab-btn"        data-view="dimensions">&#11042; Dimensions</button>
  </nav>
  <div class="view-container">
    <div id="view-search"      class="view active"></div>
    <div id="view-gaian"       class="view"></div>
    <div id="view-chat"        class="view"></div>
    <div id="view-shell"       class="view"></div>
    <div id="view-memory"      class="view"></div>
    <div id="view-noosphere"   class="view"></div>
    <div id="view-canon"       class="view"></div>
    <div id="view-quantum"     class="view"></div>
    <div id="view-dimensions"  class="view"></div>
  </div>
</div>
`;

    mountSearch(document.getElementById('view-search')!);
    mountGaianChat(document.getElementById('view-gaian')!);
    mountChat(document.getElementById('view-chat')!);
    mountShell(document.getElementById('view-shell')!);
    mountMemory(document.getElementById('view-memory')!);
    mountNoosphereTab({ root: document.getElementById('view-noosphere')!, apiBase: API_BASE });

    // Lazy-mount tabs that do async I/O or heavy work on first visit
    let canonMounted      = false;
    let quantumMounted    = false;
    let dimensionsMounted = false;
    let dimensionsTeardown: (() => void) | null = null;
    logInfo('app', 'All views mounted');

    let _activeView = 'search';
    document.querySelectorAll<HTMLButtonElement>('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view!;
        if (view === _activeView) return;
        if (_activeView === 'noosphere') unmountNoosphereTab();
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`view-${view}`)!.classList.add('active');
        logInfo('app', `View switched: ${_activeView} → ${view}`);
        _activeView = view;

        if (view === 'noosphere') {
          mountNoosphereTab({ root: document.getElementById('view-noosphere')!, apiBase: API_BASE });
        }
        if (view === 'canon' && !canonMounted) {
          mountCanonTab(document.getElementById('view-canon')!);
          canonMounted = true;
        }
        if (view === 'quantum' && !quantumMounted) {
          mountQuantumTab(document.getElementById('view-quantum')!);
          quantumMounted = true;
        }
        if (view === 'dimensions' && !dimensionsMounted) {
          dimensionsTeardown = mountDimensionalMonitor(document.getElementById('view-dimensions')!);
          dimensionsMounted = true;
        }
      });
    });
  }
}
