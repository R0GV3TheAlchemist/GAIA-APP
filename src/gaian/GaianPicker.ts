/**
 * GaianPicker.ts
 * 
 * A UI component that:
 * 1. Fetches available Base Forms from GET /gaians/base-forms
 * 2. Fetches the user's existing GAIANs from GET /gaians
 * 3. Renders a picker panel with Base Form cards and a "spawn" flow
 * 4. Handles GAIA's special "digital earth" avatar as a CSS globe animation
 * 
 * Usage: import { GaianPicker } from '../gaian/GaianPicker'
 */

import { API_BASE } from '../app';

export interface BaseFormInfo {
  id: string;
  name: string;
  role: string;
  avatar_color: string;
  avatar_style: string;
  capabilities: string[];
  is_default: boolean;
}

export interface GaianInfo {
  id: string;
  name: string;
  slug: string;
  base_form_id: string;
  avatar_color: string;
  avatar_style: string;
  relationship_depth: number;
  total_exchanges: number;
  last_active: number;
}

// ------------------------------------------------------------------ //
//  API Calls                                                           //
// ------------------------------------------------------------------ //

export async function fetchBaseForms(): Promise<BaseFormInfo[]> {
  const res = await fetch(`${API_BASE}/gaians/base-forms`);
  if (!res.ok) throw new Error('Failed to fetch base forms');
  const data = await res.json();
  return data.base_forms;
}

export async function fetchGaians(): Promise<GaianInfo[]> {
  const res = await fetch(`${API_BASE}/gaians`);
  if (!res.ok) throw new Error('Failed to fetch GAIANs');
  const data = await res.json();
  return data.gaians;
}

export async function spawnGaian(
  name: string,
  baseFormId: string,
  userName?: string
): Promise<GaianInfo> {
  const res = await fetch(`${API_BASE}/gaians`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, base_form: baseFormId, user_name: userName }),
  });
  if (!res.ok) throw new Error('Failed to spawn GAIAN');
  return res.json();
}

export async function setActiveGaian(
  sessionId: string,
  gaianSlug: string
): Promise<void> {
  await fetch(`${API_BASE}/session/${sessionId}/gaian`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gaian_slug: gaianSlug }),
  });
}

// ------------------------------------------------------------------ //
//  Avatar Renderer                                                     //
//  Injects a <div> with CSS class based on avatar_style.              //
//  GAIA gets the 'digital_earth' treatment — a CSS animated globe.   //
// ------------------------------------------------------------------ //

export function renderAvatarHTML(form: BaseFormInfo | GaianInfo, size = 64): string {
  const style = form.avatar_style;
  const color = form.avatar_color;
  const s = `${size}px`;

  if (style === 'digital_earth') {
    return `
      <div class="gaian-avatar gaian-avatar--earth" style="width:${s};height:${s};">
        <div class="earth-globe" style="--earth-color:${color};">
          <div class="earth-land"></div>
          <div class="earth-clouds"></div>
          <div class="earth-glow"></div>
        </div>
      </div>`;
  }

  // All other forms: colored circle with initials
  const initials = ('name' in form ? form.name : 'G').slice(0, 2).toUpperCase();
  return `
    <div class="gaian-avatar gaian-avatar--${style}"
         style="width:${s};height:${s};background:${color};">
      <span class="gaian-avatar__initials">${initials}</span>
    </div>`;
}

// ------------------------------------------------------------------ //
//  Picker Panel Builder                                                //
// ------------------------------------------------------------------ //

export async function buildGaianPickerHTML(sessionId: string): Promise<string> {
  const [baseForms, myGaians] = await Promise.all([fetchBaseForms(), fetchGaians()]);

  const baseFormCards = baseForms.map(f => `
    <div class="base-form-card" data-form-id="${f.id}"
         style="--form-color:${f.avatar_color};">
      ${renderAvatarHTML(f, 48)}
      <div class="base-form-card__info">
        <span class="base-form-card__name">${f.name}</span>
        <span class="base-form-card__role">${f.role}</span>
        <div class="base-form-card__caps">
          ${f.capabilities.map(c => `<span class="cap-tag">${c}</span>`).join('')}
        </div>
      </div>
      ${f.is_default ? '<span class="base-form-card__default-badge">Default</span>' : ''}
    </div>
  `).join('');

  const myGaianCards = myGaians.length > 0
    ? myGaians.map(g => `
      <div class="gaian-card" data-gaian-slug="${g.slug}"
           style="--gaian-color:${g.avatar_color};">
        ${renderAvatarHTML(g, 40)}
        <div class="gaian-card__info">
          <span class="gaian-card__name">${g.name}</span>
          <span class="gaian-card__depth">Depth ${g.relationship_depth}/100</span>
        </div>
      </div>
    `).join('')
    : '<p class="gaian-picker__empty">No GAIANs yet. Spawn your first below.</p>';

  return `
    <div class="gaian-picker" id="gaian-picker">
      <section class="gaian-picker__section">
        <h2 class="gaian-picker__heading">Your GAIANs</h2>
        <div class="gaian-cards">${myGaianCards}</div>
      </section>

      <section class="gaian-picker__section">
        <h2 class="gaian-picker__heading">Base Forms</h2>
        <div class="base-form-cards">${baseFormCards}</div>
      </section>

      <section class="gaian-picker__section gaian-picker__spawn">
        <h2 class="gaian-picker__heading">Spawn a New GAIAN</h2>
        <form id="spawn-gaian-form">
          <input type="text" id="spawn-name" placeholder="Name your GAIAN" required />
          <input type="text" id="spawn-username" placeholder="Your name (optional)" />
          <div class="spawn-form__base-select" id="spawn-base-select">
            ${baseForms.map(f => `
              <label class="spawn-base-option ${f.is_default ? 'selected' : ''}">
                <input type="radio" name="base_form" value="${f.id}" ${f.is_default ? 'checked' : ''} />
                <span style="color:${f.avatar_color}">${f.name}</span>
              </label>
            `).join('')}
          </div>
          <button type="submit" class="spawn-btn">Spawn GAIAN</button>
        </form>
      </section>
    </div>
  `;
}
