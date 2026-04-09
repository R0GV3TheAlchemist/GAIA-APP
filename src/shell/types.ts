// GAIA Shell — Type Definitions
// Canonical source: C21 (Interface and Shell Grammar), C15 (Runtime and Permissions)

export type PermissionTier = 'T0' | 'T1' | 'T2' | 'T3' | 'T4';

export type VerbClass =
  | 'QUERY'     // ask, search, recall, explain — T1
  | 'COMPOSE'   // draft, synthesise, generate, summarise — T1
  | 'ACT'       // send, publish, execute, commit — T2
  | 'CONFIGURE' // set, enable, disable, calibrate — T2
  | 'GOVERN'    // grant, revoke, elevate, audit — T3
  | 'INTERRUPT'; // pause, stop, cancel, rollback — T0 always

export type StatusCode = 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'PENDING' | 'BLOCKED';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
export type ReversibilityClass = 'R0' | 'R1' | 'R2' | 'R3' | 'R4';

export interface ParsedCommand {
  raw: string;
  verb: string;
  verbClass: VerbClass;
  target?: string;
  modifiers: Record<string, string>;
  flags: string[];
  tierRequired: PermissionTier;
  reversibilityClass: ReversibilityClass;
  requiresConfirmation: boolean;
  isIrreversible: boolean;
}

export interface ShellOutput {
  status: StatusCode;
  confidence: ConfidenceLevel;
  source: string;
  content: string;
  actions: string[];
  auditRef: string;
  timestamp: string;
  tierActive: PermissionTier;
}

export interface SessionState {
  gaianId: string;
  principal: string;
  startedAt: string;
  tierActive: PermissionTier;
  scope: string;
  online: boolean;
}

export interface PermissionState {
  baseTier: PermissionTier;
  activeTier: PermissionTier;
  elevationExpiry?: string;
  pendingRequests: string[];
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  verb: string;
  target?: string;
  tierActive: PermissionTier;
  reversibilityClass: ReversibilityClass;
  status: StatusCode;
  irreversible: boolean;
  notes?: string;
}

export interface MemoryWrite {
  timestamp: string;
  key: string;
  summary: string;
  layer: 'M0' | 'M1' | 'M2' | 'M3' | 'M4';
}

export interface ConsequentialAction {
  timestamp: string;
  verb: string;
  target: string;
  outcome: StatusCode;
  reversibilityClass: ReversibilityClass;
  auditRef: string;
}

export interface ShellState {
  session: SessionState;
  permissions: PermissionState;
  parseState: { raw: string; parsed: ParsedCommand | null; awaitingConfirmation: boolean };
  recentAudit: AuditEntry[];
  recentMemoryWrites: MemoryWrite[];
  recentConsequentialActions: ConsequentialAction[];
  interruptAvailable: boolean; // Kernel invariant: always true
}
