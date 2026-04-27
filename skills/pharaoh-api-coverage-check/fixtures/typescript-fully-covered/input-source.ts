// TypeScript module demonstrating the public-symbol regex row.

export interface Session {
  token: string;
  user: string;
}

export class SessionManager {
  open(): Session {
    if (!this.ready()) {
      throw new SessionError("not ready");
    }
    return { token: "t", user: "u" };
  }

  private ready(): boolean {
    return true;
  }
}

export function createSession(user: string): Session {
  if (!user) {
    throw new InvalidUserError("user required");
  }
  return { token: "t", user };
}

export const DEFAULT_TIMEOUT = 30_000;

class SessionError extends Error {}
class InvalidUserError extends Error {}

function internalHelper(): void {
  // not exported
}
