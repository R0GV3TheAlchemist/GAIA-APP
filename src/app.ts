// GAIA App — Top-level layout with tab navigation
// Views: SEARCH | CHAT | GAIAN | SHELL | MEMORY | NOOSPHERE
// Canon Ref: C43, C44

import './app.css';
import './search/Search.css';
import './shell/Shell.css';
import './chat/Chat.css';
import './memory/Memory.css';
import './noosphere/NoosphereTab.css';
import { mountSearch }     from './search/Search';
import { mountShell }      from './shell/Shell';
import { mountChat }       from './chat/Chat';
import { mountMemory }     from './memory/Memory';
import { mountGaianChat }  from './gaian/GaianChatView';
import {
  mountNoosphereTab,
  unmountNoosphereTab,
} from './noosphere';
import { appDataDir, join, resolveResource } from '@tauri-apps/api/path';
import { exists, mkdir, copyFile, readDir } from '@tauri-apps/plugin-fs';

const metaEnv = ((import.meta as unknown as { env?: Record<string, string> }).env) ?? {};
const BASE_URL = metaEnv.VITE_API_BASE ?? 'http://localhost:8008';
export const API_BASE = BASE_URL;

// ── First-launch: seed %APPDATA%\GAIA\canon\ from bundled resources ────
async function ensureAppDataDirs(): Promise<void> {
  try {
    const appData = await appDataDir();
    const dirs = ['canon', 'logs', 'config'];
    for (const dir of dirs) {
      const dirPath = await join(appData, dir);
      if (!(await exists(dirPath))) {
        await mkdir(dirPath, { recursive: true });
        console.log(`[GAIA] Created ${dirPath}`);
      }
    }

    // Seed canon docs from bundled resources on first launch
    const canonDest = await join(appData, 'canon');
    const canonDestEntries = await readDir(canonDest);
    if (canonDestEntries.length === 0) {
      try {
        const canonSrc = await resolveResource('canon');
        const srcEntries = await readDir(canonSrc);
        for (const entry of srcEntries) {
          const srcFile  = await join(canonSrc,   entry.name);
          const destFile = await join(canonDest, entry.name);
          await copyFile(srcFile, destFile);
        }
        console.log(`[GAIA] Seeded ${srcEntries.length} canon docs to AppData`);
      } catch (e) {
        console.warn('[GAIA] Could not seed canon docs (may not be bundled yet):', e);
      }
    }
  } catch (e) {
    console.warn('[GAIA] ensureAppDataDirs failed:', e);
  }
}

export class App {
  constructor() {
    this.mount();
    ensureAppDataDirs();
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
  </nav>
  <div class="view-container">
    <div id="view-search"     class="view active"></div>
    <div id="view-gaian"      class="view"></div>
    <div id="view-chat"       class="view"></div>
    <div id="view-shell"      class="view"></div>
    <div id="view-memory"     class="view"></div>
    <div id="view-noosphere"  class="view"></div>
  </div>
</div>
`;

    mountSearch(document.getElementById('view-search')!);
    mountGaianChat(document.getElementById('view-gaian')!);
    mountChat(document.getElementById('view-chat')!);
    mountShell(document.getElementById('view-shell')!);
    mountMemory(document.getElementById('view-memory')!);
    mountNoosphereTab({ root: document.getElementById('view-noosphere')!, apiBase: API_BASE });

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
        _activeView = view;
        if (view === 'noosphere') {
          mountNoosphereTab({ root: document.getElementById('view-noosphere')!, apiBase: API_BASE });
        }
      });
    });
  }
}
