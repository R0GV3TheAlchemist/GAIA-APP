// GAIA Dev Suite — Bottom Panel (Terminal | Logs | Tests)

export function mountBottomPanel(root: HTMLElement): void {
  root.innerHTML = `
    <div class="bottom-panel">
      <div class="bottom-tabs">
        <button class="btab active" data-tab="terminal">Terminal</button>
        <button class="btab" data-tab="logs">Logs</button>
        <button class="btab" data-tab="tests">Tests</button>
      </div>
      <div class="bottom-content">
        <div id="btab-terminal" class="btab-pane active">
          <div class="terminal-placeholder">[ xterm.js terminal — Phase 4.4 ]</div>
        </div>
        <div id="btab-logs" class="btab-pane">
          <div class="logs-placeholder">[ Log stream — Phase 4.5 ]</div>
        </div>
        <div id="btab-tests" class="btab-pane">
          <div class="tests-placeholder">[ Test runner — Phase 4.8 ]</div>
        </div>
      </div>
    </div>
  `;

  root.querySelectorAll<HTMLButtonElement>('.btab').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('.btab').forEach(b => b.classList.remove('active'));
      root.querySelectorAll('.btab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`btab-${btn.dataset.tab}`)?.classList.add('active');
    });
  });
}
