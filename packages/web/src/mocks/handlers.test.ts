import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { setupServer } from "msw/node";

import type { Channel } from "@/api/generated/endpoints";
import { fixtureByGameId } from "./fixtures";
import { handlers } from "./handlers";

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());

describe("mock channel workflow", () => {
  it("returns created channels in subsequent channel lists", async () => {
    const fixture = fixtureByGameId["active-draw-proposal"];
    const originalChannels = fixture.channels;
    const currentMember = fixture.game.members.find(member => member.isCurrentUser);
    const targetMember = fixture.game.members.find(
      member => !member.isCurrentUser && member.nation === "Austria"
    );

    expect(currentMember).toBeDefined();
    expect(targetMember).toBeDefined();

    try {
      const createResponse = await fetch(
        "http://localhost/games/active-draw-proposal/channels/create/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ memberIds: [targetMember!.id] }),
        }
      );
      const createdChannel = (await createResponse.json()) as Channel;

      expect(createResponse.status).toBe(201);
      expect(createdChannel.name).toBe("England, Austria");
      expect(createdChannel.memberIds).toEqual([
        currentMember!.id,
        targetMember!.id,
      ]);

      const listResponse = await fetch(
        "http://localhost/games/active-draw-proposal/channels/"
      );
      const channels = (await listResponse.json()) as Channel[];

      expect(channels).toContainEqual(createdChannel);
    } finally {
      fixture.channels = originalChannels;
    }
  });
});
