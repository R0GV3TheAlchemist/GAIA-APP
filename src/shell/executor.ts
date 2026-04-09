// GAIA Shell — Command Executor
// Canonical source: C21 §2.4, C24 §6 (Tool Execution Protocol)
// Enforces: grammar validation → tier check → confirmation gate → audit → execute → surface

import { parse, tierSatisfies } from './grammar';
import { openEntry, closeEntry } from './audit';
import { getActiveTier } from './session';
import type { ParsedCommand, ShellOutput } from './types';

export type ExecutionResult =
  | { type: 'output'; output: ShellOutput }
  | { type: 'parse_error'; message: string; suggestion?: string }
  | { type: 'tier_blocked'; required: string; active: string }
  | { type: 'awaiting_confirmation'; parsed: ParsedCommand }
  | { type: 'interrupt'; verb: string };

export function execute(raw: string): ExecutionResult {
  // Step 1: Parse
  const result = parse(raw);
  if ('error' in result) {
    return { type: 'parse_error', message: result.error, suggestion: result.suggestion };
  }
  const parsed = result as ParsedCommand;

  // Step 2: Interrupt verbs bypass all checks — Kernel invariant C14 §4.1
  if (parsed.verbClass === 'INTERRUPT') {
    const auditId = openEntry(parsed);
    closeEntry(auditId, 'SUCCESS', 'Interrupt verb — always permitted');
    return { type: 'interrupt', verb: parsed.verb };
  }

  // Step 3: Permission tier check — C15
  const activeTier = getActiveTier();
  if (!tierSatisfies(activeTier, parsed.tierRequired)) {
    return {
      type: 'tier_blocked',
      required: parsed.tierRequired,
      active: activeTier,
    };
  }

  // Step 4: Confirmation gate for R2/R3/R4 actions — C21 I-6, C24 TR-4
  // The shell surfaces a confirmation request; the UI must call executeConfirmed() to proceed.
  if (parsed.requiresConfirmation) {
    return { type: 'awaiting_confirmation', parsed };
  }

  return executeConfirmed(parsed);
}

export function executeConfirmed(parsed: ParsedCommand): ExecutionResult {
  // Step 5: Open audit entry — Kernel invariant
  const auditId = openEntry(parsed);

  // Step 6: Dispatch to handler
  const output = dispatch(parsed, auditId);

  // Step 7: Close audit entry
  closeEntry(auditId, output.status);

  return { type: 'output', output };
}

// Dispatch layer — in MVP, verbs produce structured shell output.
// In the full system, this routes to registered tools from the Tool Registry (C24).
function dispatch(parsed: ParsedCommand, auditId: string): ShellOutput {
  const base: ShellOutput = {
    status: 'SUCCESS',
    confidence: 'HIGH',
    source: 'T1 — shell grammar engine',
    content: '',
    actions: [],
    auditRef: auditId,
    timestamp: new Date().toISOString(),
    tierActive: getActiveTier(),
  };

  switch (parsed.verbClass) {
    case 'QUERY':
      return {
        ...base,
        content: `[QUERY] ${parsed.verb}${parsed.target ? ` → ${parsed.target}` : ''}\n` +
          `Modifiers: ${JSON.stringify(parsed.modifiers)}\n` +
          `[Note] World Fabric query not yet connected. Shell grammar validated.`,
        actions: ['search with different scope', 'recall from memory'],
        confidence: 'MEDIUM',
        source: 'shell-stub — World Fabric not connected',
      };

    case 'COMPOSE':
      return {
        ...base,
        content: `[COMPOSE] ${parsed.verb}${parsed.target ? ` → ${parsed.target}` : ''}\n` +
          `[Note] Composition engine not yet connected. Shell grammar validated.`,
        actions: ['refine draft', 'save to memory'],
        confidence: 'MEDIUM',
        source: 'shell-stub — Cognition engine not connected',
      };

    case 'ACT':
      return {
        ...base,
        content: `[ACT] ${parsed.verb} confirmed and logged.\n` +
          `Target: ${parsed.target ?? '(none)'}\n` +
          `Reversibility: ${parsed.reversibilityClass}${parsed.isIrreversible ? ' ⚠️  IRREVERSIBLE' : ''}`,
        actions: parsed.isIrreversible ? [] : ['rollback'],
        confidence: 'HIGH',
        source: 'C24 Tool Registry — stub executor',
      };

    case 'CONFIGURE':
      return {
        ...base,
        content: `[CONFIGURE] ${parsed.verb} applied.\nTarget: ${parsed.target ?? '(none)'}`,
        actions: ['verify configuration', 'revert'],
        source: 'session config — in-memory',
      };

    case 'GOVERN':
      return {
        ...base,
        content: `[GOVERN] ${parsed.verb} processed.\n` +
          `[Note] Governance operations require Human Principal ratification in production.`,
        actions: ['audit trail', 'revert'],
        source: 'governance layer — stub',
      };

    default:
      return {
        ...base,
        status: 'FAILED',
        content: `[ERROR] No handler registered for verb class: ${parsed.verbClass}`,
        confidence: 'UNKNOWN',
        source: 'shell',
      };
  }
}
