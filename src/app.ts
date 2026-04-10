// GAIA App — Top-level layout with tab navigation
// Views: CHAT | SHELL | MEMORY

import './app.css';
import './shell/Shell.css';
import './chat/Chat.css';
import './memory/Memory.css';
import { mountShell }  from './shell/Shell';
import { mountChat }   from './chat/Chat';
import { mountMemory } from './memory/Memory';

const root = document.querySelector<HTMLDivElement>('#app')!;

root.innerHTML = `
<div class="gaia-app">
  <nav class="tab-nav">
    <button class="tab-btn active" data-view="chat">&#9670; Chat</button>
    <button class="tab-btn"        data-view="shell">❯ Shell</button>
    <button class="tab-btn"        data-view="memory">▦ Memory</button>
  </nav>
  <div class="view-container">
    <div id="view-chat"   class="view active"></div>
    <div id="view-shell"  class="view"></div>
    <div id="view-memory" class="view"></div>
  </div>
</div>
`;

// Mount all three views
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
