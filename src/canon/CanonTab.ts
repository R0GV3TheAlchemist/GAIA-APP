// Canon Tab — in-app reader for GAIA doctrine documents
// Reads from %APPDATA%/GAIA/canon/ (seeded on first launch by app.ts)
// Phase 7, task 7.7

import { appDataDir, join } from '@tauri-apps/api/path';
import { readTextFile, readDir } from '@tauri-apps/plugin-fs';
import { marked } from 'marked';
import { logInfo, logError } from '../diagnostics';

marked.setOptions({ gfm: true, breaks: true });

interface CanonDoc {
  filename: string;
  title: string;
  content: string;
}

const DOC_ORDER = [
  'C42-inter-dimensional-ai.md',
  'C43-sovereign-distribution-amendment.md',
  'C44-archetypes.md',
];

function extractTitle(markdown: string, filename: string): string {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match ? match[1].replace(/^C\d+\s*[—-]\s*/, '').trim() : filename.replace('.md', '');
}

export async function mountCanonTab(container: HTMLElement): Promise<void> {
  container.innerHTML = `
    <div class="canon-tab">
      <div class="canon-sidebar">
        <div class="canon-sidebar-header">
          <span class="canon-sigil">📜</span>
          <span class="canon-sidebar-title">GAIA Canon</span>
        </div>
        <nav class="canon-nav" id="canon-nav"></nav>
        <div class="canon-sidebar-footer">Phase 7 · Doctrine</div>
      </div>
      <div class="canon-body">
        <div class="canon-loading" id="canon-loading">
          <div class="canon-loading-orb"></div>
          <p>Loading doctrine…</p>
        </div>
        <article class="canon-article" id="canon-article" style="display:none"></article>
      </div>
    </div>
  `;

  const nav     = container.querySelector<HTMLElement>('#canon-nav')!;
  const article = container.querySelector<HTMLElement>('#canon-article')!;
  const loading = container.querySelector<HTMLElement>('#canon-loading')!;

  let docs: CanonDoc[] = [];

  try {
    const appData  = await appDataDir();
    const canonDir = await join(appData, 'canon');
    const entries  = await readDir(canonDir);

    const mdFiles = entries
      .map(e => e.name)
      .filter(n => n.endsWith('.md') && n !== 'README.md')
      .sort((a, b) => {
        const ai = DOC_ORDER.indexOf(a);
        const bi = DOC_ORDER.indexOf(b);
        if (ai === -1 && bi === -1) return a.localeCompare(b);
        if (ai === -1) return 1;
        if (bi === -1) return -1;
        return ai - bi;
      });

    for (const filename of mdFiles) {
      const path    = await join(canonDir, filename);
      const content = await readTextFile(path);
      docs.push({ filename, title: extractTitle(content, filename), content });
    }

    logInfo('canon', `Loaded ${docs.length} canon docs`);
  } catch (e) {
    logError('canon', 'Failed to load canon docs', e);
    loading.innerHTML = `<p class="canon-error">⚠ Could not load canon documents.<br><small>They will appear after first launch seeds AppData.</small></p>`;
    return;
  }

  // Build nav
  docs.forEach((doc, i) => {
    const btn = document.createElement('button');
    btn.className = 'canon-nav-btn' + (i === 0 ? ' active' : '');
    btn.dataset.index = String(i);
    const label = doc.filename.replace('.md', '').replace('-', ' — ').split('-').join(' ');
    btn.innerHTML = `<span class="canon-doc-id">${doc.filename.match(/^(C\d+)/)?.[1] ?? '📄'}</span><span class="canon-doc-title">${doc.title}</span>`;
    nav.appendChild(btn);
  });

  function renderDoc(index: number) {
    const doc = docs[index];
    if (!doc) return;
    article.style.display = 'block';
    loading.style.display = 'none';
    article.innerHTML = marked.parse(doc.content) as string;
    // Scroll to top
    article.scrollTop = 0;
    container.querySelectorAll<HTMLButtonElement>('.canon-nav-btn').forEach((b, i) => {
      b.classList.toggle('active', i === index);
    });
    logInfo('canon', `Rendered: ${doc.filename}`);
  }

  nav.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('.canon-nav-btn');
    if (!btn) return;
    renderDoc(Number(btn.dataset.index));
  });

  if (docs.length > 0) {
    renderDoc(0);
  } else {
    loading.innerHTML = `<p class="canon-error">No canon documents found.</p>`;
  }
}
