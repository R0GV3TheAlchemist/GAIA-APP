/**
 * GAIA Search View — Perplexity-Style Answer Engine UI
 *
 * Layout:
 *   ┌─────────────────────────────────────────────┐
 *   │  [Sidebar: Thread History]  [Main Panel]    │
 *   │                             ┌─────────────┐ │
 *   │  • Past thread 1            │ Search Home │ │
 *   │  • Past thread 2            │  or Answer  │ │
 *   │  + New Search               │    View     │ │
 *   └─────────────────────────────┴─────────────┘ │
 *
 * SSE event pipeline from /query/stream:
 *   citation    → renders T1 canon source card
 *   web_result  → renders T2-T5 web source card
 *   token       → streams answer text word-by-word
 *   suggestions → renders follow-up question chips
 *   done        → finalises answer, re-enables input
 *
 * Canon Ref: C21 (Interface and Shell Grammar Spec)
 */

import './Search.css';

const API_BASE = 'http://127.0.0.1:8008';

// ------------------------------------------------------------------ //
//  Types                                                               //
// ------------------------------------------------------------------ //

interface SearchThread {
  id: string;
  query: string;
  timestamp: number;
  answer: string;
  sources: SourceItem[];
  suggestions: string[];
}

interface SourceItem {
  tier: string;
  title: string;
  url?: string;
  snippet?: string;
  excerpt?: string;
  domain?: string;
  doc_id?: string;
}

// ------------------------------------------------------------------ //
//  State                                                               //
// ------------------------------------------------------------------ //

let threads: SearchThread[] = JSON.parse(localStorage.getItem('gaia_search_threads') || '[]');
let activeThreadId: string | null = null;
let isStreaming = false;

function saveThreads() {
  localStorage.setItem('gaia_search_threads', JSON.stringify(threads.slice(-30)));
}

// ------------------------------------------------------------------ //
//  Mount                                                               //
// ------------------------------------------------------------------ //

export function mountSearch(container: HTMLElement): void {
  container.innerHTML = `
    <div class="search-layout">
      <aside class="search-sidebar">
        <div class="sidebar-header">
          <span class="sidebar-logo">⬡ GAIA</span>
          <button class="new-search-btn" id="newSearchBtn" title="New Search">＋ New</button>
        </div>
        <div class="thread-list" id="threadList"></div>
      </aside>
      <main class="search-main" id="searchMain">
        <!-- SearchHome or AnswerView renders here -->
      </main>
    </div>
  `;

  renderThreadList();
  renderSearchHome();

  document.getElementById('newSearchBtn')!.addEventListener('click', () => {
    activeThreadId = null;
    renderSearchHome();
    highlightActiveThread();
  });
}

// ------------------------------------------------------------------ //
//  Thread Sidebar                                                      //
// ------------------------------------------------------------------ //

function renderThreadList() {
  const list = document.getElementById('threadList')!;
  if (threads.length === 0) {
    list.innerHTML = `<div class="thread-empty">No searches yet</div>`;
    return;
  }
  list.innerHTML = threads
    .slice()
    .reverse()
    .map(t => `
      <div class="thread-item ${t.id === activeThreadId ? 'active' : ''}" data-id="${t.id}">
        <div class="thread-query">${escapeHtml(t.query.slice(0, 52))}${t.query.length > 52 ? '…' : ''}</div>
        <div class="thread-time">${formatTime(t.timestamp)}</div>
        <button class="thread-delete" data-id="${t.id}" title="Delete">✕</button>
      </div>
    `)
    .join('');

  list.querySelectorAll<HTMLElement>('.thread-item').forEach(el => {
    el.addEventListener('click', (e) => {
      if ((e.target as HTMLElement).classList.contains('thread-delete')) return;
      const id = el.dataset.id!;
      const thread = threads.find(t => t.id === id);
      if (thread) {
        activeThreadId = id;
        renderAnswerView(thread.query, thread.sources, thread.answer, thread.suggestions);
        highlightActiveThread();
      }
    });
  });

  list.querySelectorAll<HTMLButtonElement>('.thread-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.id!;
      threads = threads.filter(t => t.id !== id);
      saveThreads();
      if (activeThreadId === id) {
        activeThreadId = null;
        renderSearchHome();
      }
      renderThreadList();
    });
  });
}

function highlightActiveThread() {
  document.querySelectorAll('.thread-item').forEach(el => {
    el.classList.toggle('active', (el as HTMLElement).dataset.id === activeThreadId);
  });
}

// ------------------------------------------------------------------ //
//  Search Home (landing page)                                          //
// ------------------------------------------------------------------ //

function renderSearchHome() {
  const main = document.getElementById('searchMain')!;
  main.innerHTML = `
    <div class="search-home">
      <div class="search-home-logo">⬡</div>
      <h1 class="search-home-title">Ask GAIA</h1>
      <p class="search-home-sub">Canon-first · Web-grounded · Locally sovereign</p>
      <div class="search-input-wrap" id="homeInputWrap">
        <textarea
          class="search-input"
          id="homeInput"
          placeholder="Ask anything…"
          rows="1"
          autofocus
        ></textarea>
        <button class="search-submit" id="homeSubmit" title="Search">&#9654;</button>
      </div>
      <div class="search-suggestions-wrap" id="homeSuggestions">
        ${renderSuggestionChips([
          'What is GAIA\'s constitutional foundation?',
          'How does the consent ledger work?',
          'What canon documents are loaded?',
          'Explain the ActionGate risk tiers',
        ])}
      </div>
    </div>
  `;

  wireSearchInput('homeInput', 'homeSubmit', 'homeSuggestions');
}

// ------------------------------------------------------------------ //
//  Answer View                                                         //
// ------------------------------------------------------------------ //

function renderAnswerView(
  query: string,
  sources: SourceItem[],
  answer: string,
  suggestions: string[],
  streaming = false
) {
  const main = document.getElementById('searchMain')!;
  const canonSources = sources.filter(s => s.tier === 'T1');
  const webSources = sources.filter(s => s.tier !== 'T1');

  main.innerHTML = `
    <div class="answer-view">
      <div class="answer-query">${escapeHtml(query)}</div>

      <div class="sources-section">
        ${canonSources.length > 0 ? `
          <div class="sources-label">&#9670; Canon Sources</div>
          <div class="sources-row" id="canonSourcesRow">
            ${canonSources.map((s, i) => renderSourceCard(s, i + 1)).join('')}
          </div>
        ` : ''}
        ${webSources.length > 0 ? `
          <div class="sources-label" style="margin-top:8px">&#127760; Web Sources</div>
          <div class="sources-row" id="webSourcesRow">
            ${webSources.map((s, i) => renderSourceCard(s, canonSources.length + i + 1)).join('')}
          </div>
        ` : '<div id="webSourcesRow" class="sources-row"></div>'}
      </div>

      <div class="answer-body" id="answerBody">
        ${streaming ? '<span class="cursor-blink">▍</span>' : renderMarkdown(answer)}
      </div>

      <div class="suggestions-section" id="suggestionsSection">
        ${suggestions.length > 0 ? renderSuggestionChips(suggestions) : ''}
      </div>

      <div class="followup-wrap">
        <textarea
          class="search-input followup-input"
          id="followupInput"
          placeholder="Ask a follow-up…"
          rows="1"
          ${isStreaming ? 'disabled' : ''}
        ></textarea>
        <button class="search-submit" id="followupSubmit" ${isStreaming ? 'disabled' : ''} title="Search">&#9654;</button>
      </div>
    </div>
  `;

  wireSearchInput('followupInput', 'followupSubmit', 'suggestionsSection');
}

// ------------------------------------------------------------------ //
//  Source Card                                                         //
// ------------------------------------------------------------------ //

function renderSourceCard(source: SourceItem, index: number): string {
  const isCanon = source.tier === 'T1';
  const tierColor: Record<string, string> = {
    T1: '#4ade80', T2: '#60a5fa', T3: '#a78bfa', T4: '#94a3b8', T5: '#f87171'
  };
  const color = tierColor[source.tier] || '#94a3b8';
  const domain = source.domain || (source.url ? new URL(source.url).hostname.replace('www.', '') : 'canon');
  const snippet = (source.snippet || source.excerpt || '').slice(0, 100);

  return `
    <div class="source-card" data-index="${index}">
      <div class="source-card-header">
        <span class="source-badge" style="background:${color}22;color:${color};border:1px solid ${color}44">${source.tier}</span>
        <span class="source-num">[${index}]</span>
      </div>
      <div class="source-title">${isCanon ? '⬡ ' : ''}${escapeHtml(source.title.slice(0, 50))}${source.title.length > 50 ? '…' : ''}</div>
      <div class="source-domain">${escapeHtml(domain)}</div>
      ${snippet ? `<div class="source-snippet">${escapeHtml(snippet)}…</div>` : ''}
      ${source.url ? `<a class="source-link" href="${source.url}" target="_blank" rel="noopener">Open ↗</a>` : ''}
    </div>
  `;
}

// ------------------------------------------------------------------ //
//  SSE Streaming Query                                                 //
// ------------------------------------------------------------------ //

function runQuery(query: string) {
  if (isStreaming || !query.trim()) return;
  isStreaming = true;

  const sources: SourceItem[] = [];
  let answerText = '';
  const suggestions: string[] = [];
  const threadId = crypto.randomUUID();
  activeThreadId = threadId;

  renderAnswerView(query, sources, '', [], true);
  highlightActiveThread();

  const eventSource = new EventSource(
    `${API_BASE}/query/stream?_dummy=${Date.now()}`
  );

  // Use fetch+ReadableStream for POST (EventSource only supports GET)
  eventSource.close();

  fetch(`${API_BASE}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, enable_web_search: true, enable_scraping: true }),
  }).then(async (response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const answerBody = () => document.getElementById('answerBody');
    const webRow = () => document.getElementById('webSourcesRow');
    const canonRow = () => document.getElementById('canonSourcesRow');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          // handled below with data
        } else if (line.startsWith('data: ')) {
          try {
            const eventLine = lines[lines.indexOf(line) - 1] || '';
            const eventType = eventLine.replace('event: ', '').trim();
            const data = JSON.parse(line.replace('data: ', ''));

            if (eventType === 'citation') {
              sources.push({ tier: 'T1', title: data.title, doc_id: data.doc_id, excerpt: data.excerpt });
              if (!document.getElementById('canonSourcesRow')) {
                const sourcesSection = document.querySelector('.sources-section');
                if (sourcesSection) {
                  sourcesSection.insertAdjacentHTML('afterbegin', `
                    <div class="sources-label">&#9670; Canon Sources</div>
                    <div class="sources-row" id="canonSourcesRow"></div>
                  `);
                }
              }
              canonRow()?.insertAdjacentHTML('beforeend', renderSourceCard(sources[sources.length - 1], sources.length));

            } else if (eventType === 'web_result') {
              sources.push({ tier: data.tier, title: data.title, url: data.url, snippet: data.snippet, domain: data.domain });
              if (!document.getElementById('webSourcesRow')) {
                document.querySelector('.sources-section')?.insertAdjacentHTML('beforeend', `
                  <div class="sources-label" style="margin-top:8px">&#127760; Web Sources</div>
                  <div class="sources-row" id="webSourcesRow"></div>
                `);
              }
              webRow()?.insertAdjacentHTML('beforeend', renderSourceCard(sources[sources.length - 1], sources.length));

            } else if (eventType === 'token') {
              answerText += data.text;
              const body = answerBody();
              if (body) body.innerHTML = renderMarkdown(answerText) + '<span class="cursor-blink">▍</span>';

            } else if (eventType === 'suggestions') {
              suggestions.push(...(data.items || []));
              const sec = document.getElementById('suggestionsSection');
              if (sec) sec.innerHTML = renderSuggestionChips(suggestions);
              wireSuggestionChips('suggestionsSection');

            } else if (eventType === 'done') {
              const body = answerBody();
              if (body) body.innerHTML = renderMarkdown(answerText);
              isStreaming = false;
              const fi = document.getElementById('followupInput') as HTMLTextAreaElement;
              const fs = document.getElementById('followupSubmit') as HTMLButtonElement;
              if (fi) fi.disabled = false;
              if (fs) fs.disabled = false;

              // Save to thread history
              threads = threads.filter(t => t.id !== threadId);
              threads.push({ id: threadId, query, timestamp: Date.now(), answer: answerText, sources, suggestions });
              saveThreads();
              renderThreadList();
              highlightActiveThread();
            }
          } catch (_) { /* ignore parse errors */ }
        }
      }
    }
  }).catch((err) => {
    isStreaming = false;
    const body = document.getElementById('answerBody');
    if (body) body.innerHTML = `<div class="error-msg">⚠ Could not reach GAIA server at ${API_BASE}. Is <code>python core/server.py</code> running?<br><small>${err.message}</small></div>`;
  });
}

// ------------------------------------------------------------------ //
//  Input Wiring                                                        //
// ------------------------------------------------------------------ //

function wireSearchInput(inputId: string, submitId: string, suggestionsId: string) {
  const input = document.getElementById(inputId) as HTMLTextAreaElement;
  const submit = document.getElementById(submitId) as HTMLButtonElement;
  if (!input || !submit) return;

  const doSearch = () => {
    const q = input.value.trim();
    if (q && !isStreaming) runQuery(q);
  };

  submit.addEventListener('click', doSearch);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSearch();
    }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 160) + 'px';
  });

  wireSuggestionChips(suggestionsId);
}

function wireSuggestionChips(containerId: string) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.querySelectorAll<HTMLButtonElement>('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (!isStreaming) runQuery(chip.dataset.query || chip.textContent || '');
    });
  });
}

// ------------------------------------------------------------------ //
//  Helpers                                                             //
// ------------------------------------------------------------------ //

function renderSuggestionChips(items: string[]): string {
  return items.map(q => `
    <button class="suggestion-chip" data-query="${escapeHtml(q)}">${escapeHtml(q)}</button>
  `).join('');
}

function renderMarkdown(text: string): string {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```[\s\S]*?```/g, (m) => `<pre><code>${m.slice(3, -3).replace(/^\w+\n/, '')}</code></pre>`)
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\[(\d+)\]/g, '<cite class="inline-cite">[$1]</cite>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^(.+)$/, '<p>$1</p>');
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const diff = (now.getTime() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}
