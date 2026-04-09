// GAIA App — Top-level layout with tab navigation
// Views: CHAT | SHELL | MEMORY

import './shell/Shell.css';
import './chat/Chat.css';
import './memory/Memory.css';
import { mountShell }  from './shell/Shell';
import { mountChat }   from './chat/Chat';
import { mountMemory } from './memory/Memory';

const root = document.querySelector<HTMLDivElement>('#app')!;

const appStyle = document.createElement('style');
appStyle.textContent = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; overflow: hidden; background: #0F1117; }

  .gaia-app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  /* Tab bar */
  .tab-nav {
    display: flex;
    background: #1A1D27;
    border-bottom: 1px solid #2A2D3A;
    padding: 0 16px;
    flex-shrink: 0;
    height: 40px;
  }

  .tab-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #6B7280;
    font-family: 'JetBrains Mono', monospace, sans-serif;
    font-size: 12px;
    padding: 0 20px;
    cursor: pointer;
    letter-spacing: 0.05em;
    transition: color 0.15s, border-color 0.15s;
    white-space: nowrap;
  }
  .tab-btn:hover  { color: #fff; }
  .tab-btn.active { color: #2D6A4F; border-bottom-color: #2D6A4F; }

  /* View container fills remaining height */
  .view-container {
    flex: 1;
    min-height: 0;          /* critical: allows flex child to shrink */
    position: relative;
    overflow: hidden;
  }

  /* Every view fills the container absolutely */
  .view {
    position: absolute;
    inset: 0;
    overflow: hidden;
    display: none;
    flex-direction: column;
  }
  .view.active {
    display: flex;
  }
`;
document.head.appendChild(appStyle);

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
