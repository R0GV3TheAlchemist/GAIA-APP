// GAIA Shell — Audit Trail
// Canonical source: C21 §3.6, C14 §4.1 (Kernel invariant: audit always runs)
// All consequential actions must generate pre- and post-audit entries.
// The audit trail is append-only. Nothing is ever deleted from it.

import type { AuditEntry, ParsedCommand, StatusCode } from './types';

let _auditLog: AuditEntry[] = [];

export function openEntry(cmd: ParsedCommand): string {
  const id = `AUDIT-${Date.now()}-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;
  const entry: AuditEntry = {
    id,
    timestamp: new Date().toISOString(),
    verb: cmd.verb,
    target: cmd.target,
    tierActive: cmd.tierRequired, // will be updated on close with actual active tier
    reversibilityClass: cmd.reversibilityClass,
    status: 'PENDING',
    irreversible: cmd.isIrreversible,
  };
  _auditLog.push(entry);
  return id;
}

export function closeEntry(id: string, status: StatusCode, notes?: string): void {
  const entry = _auditLog.find(e => e.id === id);
  if (!entry) return;
  entry.status = status;
  if (notes) entry.notes = notes;
}

export function getLog(): Readonly<AuditEntry[]> {
  return _auditLog;
}

export function getLastN(n: number): AuditEntry[] {
  return _auditLog.slice(-n);
}

export function exportLog(): string {
  return JSON.stringify(_auditLog, null, 2);
}
