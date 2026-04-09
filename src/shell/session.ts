// GAIA Shell — Session Manager
// Canonical source: C21 §3.2, C15 (Runtime and Permissions), C17 (Identity)

import type { SessionState, PermissionState, PermissionTier } from './types';
import { TIER_ORDER } from './grammar';

// Re-export for use by other modules
export { TIER_ORDER };

let _session: SessionState = {
  gaianId: 'gn-aether-dev',
  principal: 'Kyle Steen',
  startedAt: new Date().toISOString(),
  tierActive: 'T1',
  scope: 'local-shell',
  online: true,
};

let _permissions: PermissionState = {
  baseTier: 'T1',
  activeTier: 'T1',
  pendingRequests: [],
};

export function getSession(): Readonly<SessionState> {
  return { ..._session };
}

export function getPermissions(): Readonly<PermissionState> {
  return { ..._permissions };
}

// Elevation requires explicit HP consent — C15 §Permission Grant Rules
// In the shell MVP, consent is modelled as an explicit call from a UI confirmation action.
export function elevatePermission(target: PermissionTier, expiryISO?: string): void {
  const currentIdx = TIER_ORDER.indexOf(_permissions.activeTier);
  const targetIdx = TIER_ORDER.indexOf(target);
  if (targetIdx <= currentIdx) return; // already at or above requested tier
  _permissions.activeTier = target;
  _session.tierActive = target;
  if (expiryISO) _permissions.elevationExpiry = expiryISO;
}

export function restrictPermission(target: PermissionTier): void {
  // Restriction takes effect immediately — C15
  _permissions.activeTier = target;
  _session.tierActive = target;
  delete _permissions.elevationExpiry;
}

export function setOnline(online: boolean): void {
  _session.online = online;
}

export function getActiveTier(): PermissionTier {
  return _permissions.activeTier;
}
