import { describe, it, expect } from "vitest";
import { createMemoryRouter } from "react-router";
import {
  createAuthenticatedRoutes,
  createUnauthenticatedRoutes,
} from "./Router";

describe("Router", () => {
  it("is ready on launch for a logged-in user without waiting on a loader", () => {
    const router = createMemoryRouter(createAuthenticatedRoutes(), {
      initialEntries: ["/"],
    });
    expect(router.state.initialized).toBe(true);
    router.dispose();
  });

  it("is ready on launch for a logged-out user without waiting on a loader", () => {
    const router = createMemoryRouter(createUnauthenticatedRoutes(), {
      initialEntries: ["/"],
    });
    expect(router.state.initialized).toBe(true);
    router.dispose();
  });
});
