export type CapabilityKind = "path" | "command" | "network";

/** A kind-specific pattern: a path glob, a command name, or a host. */
export interface Capability {
  kind: CapabilityKind;
  pattern: string;
}

/**
 * Least-privilege capability scoping for a single session.
 *
 * Scope is computed per task, not granted globally — a session should
 * only ever hold the capabilities it was explicitly granted for its
 * current task, and `check` must deny anything outside that set by
 * default.
 */
export interface ScopeEnforcer {
  grant(capability: Capability): void;
  check(capability: Capability): boolean;
  activeScope(): Capability[];
}
