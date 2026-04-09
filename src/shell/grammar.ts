// GAIA Shell — Canonical Grammar Engine
// Canonical source: C21 §2 (Shell Grammar)

import type { ParsedCommand, PermissionTier, VerbClass, ReversibilityClass } from './types';

// Canonical verb registry — C21 §2.2
const VERB_REGISTRY: Record<string, { verbClass: VerbClass; tierRequired: PermissionTier; reversibilityClass: ReversibilityClass }> = {
  // QUERY — T1
  ask:       { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },
  search:    { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },
  recall:    { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },
  explain:   { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },
  show:      { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },
  list:      { verbClass: 'QUERY',     tierRequired: 'T1', reversibilityClass: 'R0' },

  // COMPOSE — T1
  draft:     { verbClass: 'COMPOSE',   tierRequired: 'T1', reversibilityClass: 'R0' },
  synthesise:{ verbClass: 'COMPOSE',   tierRequired: 'T1', reversibilityClass: 'R0' },
  generate:  { verbClass: 'COMPOSE',   tierRequired: 'T1', reversibilityClass: 'R0' },
  summarise: { verbClass: 'COMPOSE',   tierRequired: 'T1', reversibilityClass: 'R0' },

  // ACT — T2
  send:      { verbClass: 'ACT',       tierRequired: 'T2', reversibilityClass: 'R2' },
  publish:   { verbClass: 'ACT',       tierRequired: 'T2', reversibilityClass: 'R3' },
  execute:   { verbClass: 'ACT',       tierRequired: 'T2', reversibilityClass: 'R2' },
  commit:    { verbClass: 'ACT',       tierRequired: 'T4', reversibilityClass: 'R4' }, // irreversible; requires T4 + ratification

  // CONFIGURE — T2
  set:       { verbClass: 'CONFIGURE', tierRequired: 'T2', reversibilityClass: 'R1' },
  enable:    { verbClass: 'CONFIGURE', tierRequired: 'T2', reversibilityClass: 'R1' },
  disable:   { verbClass: 'CONFIGURE', tierRequired: 'T2', reversibilityClass: 'R1' },
  calibrate: { verbClass: 'CONFIGURE', tierRequired: 'T2', reversibilityClass: 'R1' },

  // GOVERN — T3
  grant:     { verbClass: 'GOVERN',    tierRequired: 'T3', reversibilityClass: 'R2' },
  revoke:    { verbClass: 'GOVERN',    tierRequired: 'T3', reversibilityClass: 'R1' },
  elevate:   { verbClass: 'GOVERN',    tierRequired: 'T3', reversibilityClass: 'R2' },
  audit:     { verbClass: 'GOVERN',    tierRequired: 'T1', reversibilityClass: 'R0' }, // audit is always readable at T1

  // INTERRUPT — T0 always available (Kernel invariant)
  pause:     { verbClass: 'INTERRUPT', tierRequired: 'T0', reversibilityClass: 'R1' },
  stop:      { verbClass: 'INTERRUPT', tierRequired: 'T0', reversibilityClass: 'R1' },
  cancel:    { verbClass: 'INTERRUPT', tierRequired: 'T0', reversibilityClass: 'R1' },
  rollback:  { verbClass: 'INTERRUPT', tierRequired: 'T0', reversibilityClass: 'R1' },
  panic:     { verbClass: 'INTERRUPT', tierRequired: 'T0', reversibilityClass: 'R0' },
};

const TIER_ORDER: PermissionTier[] = ['T0', 'T1', 'T2', 'T3', 'T4'];

export function tierSatisfies(active: PermissionTier, required: PermissionTier): boolean {
  return TIER_ORDER.indexOf(active) >= TIER_ORDER.indexOf(required);
}

export function isIrreversible(rc: ReversibilityClass): boolean {
  return rc === 'R4';
}

export function requiresConfirmation(rc: ReversibilityClass, tier: PermissionTier): boolean {
  if (rc === 'R4') return true;
  if (rc === 'R3') return true;
  if (rc === 'R2') return true;
  if (rc === 'R1' && TIER_ORDER.indexOf(tier) >= TIER_ORDER.indexOf('T3')) return true;
  return false;
}

// Parse raw input into a canonical ParsedCommand — C21 §2.1
export function parse(raw: string): ParsedCommand | { error: string; suggestion?: string } {
  const trimmed = raw.trim();
  if (!trimmed) return { error: 'Empty input.' };

  const tokens = tokenise(trimmed);
  if (tokens.length === 0) return { error: 'Could not tokenise input.' };

  const verb = tokens[0].toLowerCase();
  const verbDef = VERB_REGISTRY[verb];

  if (!verbDef) {
    const suggestion = findClosestVerb(verb);
    return {
      error: `Unknown verb: "${verb}". ${suggestion ? `Did you mean "${suggestion}"?` : 'See available verbs.'}`,
      suggestion,
    };
  }

  const { target, modifiers, flags } = parseRemainder(tokens.slice(1));

  return {
    raw: trimmed,
    verb,
    verbClass: verbDef.verbClass,
    target,
    modifiers,
    flags,
    tierRequired: verbDef.tierRequired,
    reversibilityClass: verbDef.reversibilityClass,
    requiresConfirmation: requiresConfirmation(verbDef.reversibilityClass, verbDef.tierRequired),
    isIrreversible: isIrreversible(verbDef.reversibilityClass),
  };
}

function tokenise(input: string): string[] {
  // Handle quoted strings as single tokens
  const tokens: string[] = [];
  const regex = /"([^"]+)"|'([^']+)'|(\S+)/g;
  let match;
  while ((match = regex.exec(input)) !== null) {
    tokens.push(match[1] ?? match[2] ?? match[3]);
  }
  return tokens;
}

function parseRemainder(tokens: string[]): { target?: string; modifiers: Record<string, string>; flags: string[] } {
  const modifiers: Record<string, string> = {};
  const flags: string[] = [];
  let target: string | undefined;

  for (const token of tokens) {
    if (token.startsWith('--')) {
      flags.push(token.slice(2));
    } else if (token.includes('=')) {
      const [key, ...rest] = token.split('=');
      modifiers[key] = rest.join('=');
    } else if (!target) {
      target = token;
    }
  }

  return { target, modifiers, flags };
}

function findClosestVerb(input: string): string | undefined {
  const verbs = Object.keys(VERB_REGISTRY);
  let best: string | undefined;
  let bestScore = Infinity;
  for (const v of verbs) {
    const dist = levenshtein(input, v);
    if (dist < bestScore && dist <= 3) {
      bestScore = dist;
      best = v;
    }
  }
  return best;
}

function levenshtein(a: string, b: string): number {
  const dp = Array.from({ length: a.length + 1 }, (_, i) =>
    Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
  return dp[a.length][b.length];
}

export { VERB_REGISTRY };
