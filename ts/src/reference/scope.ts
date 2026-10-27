import type { Capability, ScopeEnforcer } from "../scope.js";

/**
 * Converts a shell-glob pattern (`*`, `?`, `[...]`) to a RegExp, matching
 * Python's `fnmatch.fnmatch` semantics closely enough for the patterns
 * this project actually uses (mostly `*` wildcards in paths/hosts).
 */
function globToRegExp(pattern: string): RegExp {
  let out = "^";
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i];
    if (c === "*") {
      out += ".*";
    } else if (c === "?") {
      out += ".";
    } else if (c === "[") {
      const close = pattern.indexOf("]", i + 1);
      if (close === -1) {
        out += "\\[";
      } else {
        out += `[${pattern.slice(i + 1, close)}]`;
        i = close;
      }
    } else {
      out += c.replace(/[.+^${}()|\\]/g, "\\$&");
    }
  }
  return new RegExp(out + "$");
}

/** In-memory least-privilege scope: deny by default, allow only granted patterns. */
export class TableScopeEnforcer implements ScopeEnforcer {
  private readonly granted: Capability[] = [];

  grant(capability: Capability): void {
    this.granted.push(capability);
  }

  check(capability: Capability): boolean {
    return this.granted.some(
      (g) => g.kind === capability.kind && globToRegExp(g.pattern).test(capability.pattern),
    );
  }

  activeScope(): Capability[] {
    return [...this.granted];
  }

  /**
   * Reconstruct a scope from a previously-exported capability list.
   *
   * `Capability` is already a flat (kind, pattern) record with no enum
   * boxing in TypeScript, so `JSON.parse` of what Python exported is
   * already a valid `Capability[]` — this is just the convenience
   * constructor, not a decode step. See `hcp/interop/` for this used to
   * reconstruct a scope granted by a different language.
   */
  static fromCapabilities(capabilities: Capability[]): TableScopeEnforcer {
    const scope = new TableScopeEnforcer();
    for (const capability of capabilities) {
      scope.grant(capability);
    }
    return scope;
  }
}
