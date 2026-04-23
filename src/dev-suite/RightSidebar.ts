// GAIA Dev Suite — Right Sidebar (Engine State Inspector)
// Full implementation in Phase 4.6; shell mounted here

export function mountRightSidebar(root: HTMLElement): void {
  root.innerHTML = `
    <div class="right-sidebar">
      <div class="rs-header">🔬 Engine Inspector</div>
      <div class="rs-content" id="rs-content">
        <div class="rs-placeholder">[ Engine state inspector — Phase 4.6 ]</div>
      </div>
    </div>
  `;
}
