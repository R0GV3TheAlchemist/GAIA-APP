// GAIA App — Top-level layout with tab navigation
// Views: SEARCH | CHAT | GAIAN | SHELL | MEMORY

import './app.css';
import './search/Search.css';
import './shell/Shell.css';
import './chat/Chat.css';
import './memory/Memory.css';
import { mountSearch }     from './search/Search';
import { mountShell }      from './shell/Shell';
import { mountChat }       from './chat/Chat';
import { mountMemory }     from './memory/Memory';
import { mountGaianChat }  from './gaian/GaianChatView';

const BASE_URL = (import.meta as Record<string,unknown>).env
  ? ((import.meta as Record<string,unknown>).env as Record<string,string>).VITE_API_BASE ?? 'http://localhost:8008'
  : 'http://localhost:8008';

export const API_BASE = BASE_URL;

const root = document.querySelector<HTMLDivElement>('#app')!;

root.innerHTML = `
<div class="gaia-app">
  <nav class="tab-nav">
    <button class="tab-btn active" data-view="search">&#128269; Search</button>
    <button class="tab-btn"        data-view="gaian">&#9672; GAIAN</button>
    <button class="tab-btn"        data-view="chat">&#9670; Chat</button>
    <button class="tab-btn"        data-view="shell">&gt; Shell</button>
    <button class="tab-btn"        data-view="memory">&#9638; Memory</button>
  </nav>
  <div class="view-container">
    <div id="view-search" class="view active"></div>
    <div id="view-gaian"  class="view"></div>
    <div id="view-chat"   class="view"></div>
    <div id="view-shell"  class="view"></div>
    <div id="view-memory" class="view"></div>
  </div>
</div>
`;

// Mount all views
mountSearch(document.getElementById('view-search')!);
mountGaianChat(document.getElementById('view-gaian')!);
mountChat(document.getElementById('view-chat')!);
mountShell(document.getElementById('view-shell')!);
mountMemory(document.getElementById('view-memory')!);

// Tab switching
document.querySelectorAll<HTMLButtonElement>('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const view = btn.dataset.view!;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`view-${view}`)!.classList.add('active');
  });
});
