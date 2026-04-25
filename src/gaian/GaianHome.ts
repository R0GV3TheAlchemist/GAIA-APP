/**
 * GaianHome.ts
 * The primary Home screen — GAIA's living room.
 *
 * Layout:
 *   ┌──────────────────────────────────────────────────┐
 *   │  [parallax room background]                    │
 *   │                                               │
 *   │            [GaianOrb canvas]                  │
 *   │                                               │
 *   │   "Good morning, Kyle. The room feels quiet."  │
 *   │                                               │
 *   │   [ Chat ] [ Memory ] [ Search ] [ Shell ]     │
 *   └──────────────────────────────────────────────────┘
 *
 * The Home screen is NOT a dashboard. It's a room.
 */

import { GaianOrb }       from './GaianOrb';
import { HomeBackground } from './HomeBackground';
import { buildGreeting }  from './GaianGreeting';
import { API_BASE }       from '../config';

export type HomeNavTarget = 'chat' | 'memory' | 'search' | 'shell';

export interface GaianHomeOptions {
  container: HTMLElement;
  onNavigate: (target: HomeNavTarget) => void;
}

export class GaianHome {
  private container:  HTMLElement;
  private orb:        GaianOrb | null = null;
  private bg:         HomeBackground | null = null;
  private onNavigate: (target: HomeNavTarget) => void;
  private _greetingRefresh: number | null = null;

  constructor({ container, onNavigate }: GaianHomeOptions) {
    this.container  = container;
    this.onNavigate = onNavigate;
    this._render();
  }

  private _render(): void {
    this.container.innerHTML = '';
    this.container.className = 'gaian-home';

    // ── Background
    this.bg = new HomeBackground(this.container);

    // ── Orb wrapper + canvas
    const orbWrap = document.createElement('div');
    orbWrap.className = 'home-orb-wrap';

    const canvas = document.createElement('canvas');
    canvas.className = 'home-orb-canvas';
    canvas.setAttribute('aria-label', 'GAIA — Living Earth avatar');
    orbWrap.appendChild(canvas);
    this.container.appendChild(orbWrap);

    // ── Greeting
    const greetingEl = document.createElement('p');
    greetingEl.className = 'home-greeting';
    greetingEl.textContent = buildGreeting(this._recallName());
    this.container.appendChild(greetingEl);

    // Refresh greeting every minute (time-of-day may change)
    this._greetingRefresh = window.setInterval(() => {
      greetingEl.textContent = buildGreeting(this._recallName());
    }, 60_000);

    // ── Bottom dock
    const dock = document.createElement('nav');
    dock.className = 'home-dock';
    dock.setAttribute('aria-label', 'GAIA navigation');

    const dockItems: { id: HomeNavTarget; label: string; icon: string }[] = [
      { id: 'chat',   label: 'Chat',   icon: '◆' },
      { id: 'memory', label: 'Memory', icon: '☆' },
      { id: 'search', label: 'Search', icon: '⌘' },
      { id: 'shell',  label: 'Shell',  icon: '❯' },
    ];

    dockItems.forEach(({ id, label, icon }) => {
      const btn = document.createElement('button');
      btn.className  = 'home-dock-btn';
      btn.dataset.nav = id;
      btn.setAttribute('aria-label', label);
      btn.innerHTML  = `<span class="dock-icon" aria-hidden="true">${icon}</span><span class="dock-label">${label}</span>`;
      btn.addEventListener('click', () => {
        this.onNavigate(id);
        this._setActiveDock(id);
      });
      dock.appendChild(btn);
    });

    this.container.appendChild(dock);

    // ── Sidecar loading indicator (shows until backend ready)
    const loadingBadge = document.createElement('div');
    loadingBadge.className = 'home-loading-badge';
    loadingBadge.textContent = 'Connecting to GAIA…';
    loadingBadge.setAttribute('aria-live', 'polite');
    this.container.appendChild(loadingBadge);

    // Poll /health until model is ready
    this._pollHealth(loadingBadge);

    // ── Init GaianOrb (after DOM is painted)
    requestAnimationFrame(() => {
      this.orb = new GaianOrb(canvas);
      this.orb.start();
    });
  }

  private async _pollHealth(badge: HTMLElement): Promise<void> {
    const MAX_TRIES = 60;
    let tries = 0;
    const check = async () => {
      try {
        const res  = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        if (data.model_ready) {
          badge.textContent = '';
          badge.classList.add('ready');
          badge.remove();
          this.orb?.setMood('calm');
          return;
        }
        badge.textContent = data.error
          ? `⦻ ${data.error}`
          : 'GAIA is waking up…';
      } catch {
        badge.textContent = 'Waiting for backend…';
      }
      tries++;
      if (tries < MAX_TRIES) setTimeout(check, 2000);
      else badge.textContent = 'Backend unavailable — some features offline.';
    };
    check();
  }

  private _recallName(): string | undefined {
    // Will be wired to the memory layer in P2
    // For now, read from a global stub that won't crash
    try { return window.__gaiaUserName || undefined; } catch { return undefined; }
  }

  private _setActiveDock(id: HomeNavTarget): void {
    this.container.querySelectorAll<HTMLButtonElement>('.home-dock-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.nav === id);
    });
  }

  dispose(): void {
    this.orb?.dispose();
    this.bg?.dispose();
    if (this._greetingRefresh !== null) clearInterval(this._greetingRefresh);
  }
}

/** Global name stub — set externally once memory layer is live */
declare global {
  interface Window { __gaiaUserName?: string; }
}

/** Mount helper for use in app.ts */
export function mountGaianHome(
  container: HTMLElement,
  onNavigate: (target: HomeNavTarget) => void,
): GaianHome {
  return new GaianHome({ container, onNavigate });
}
