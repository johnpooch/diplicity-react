import { describe, it, expect } from "vitest";
import type { Channel, ChannelMember, Member } from "@/api/generated/endpoints";
import { getChannelFlagUrls, getMessageSenderLabel } from "./channelUtils";

const member = (id: number, nation: string, overrides: Partial<Member> = {}) =>
  ({
    id,
    userId: id,
    name: `Player ${id}`,
    picture: null,
    isCurrentUser: false,
    isBot: false,
    commitment: null,
    nation,
    eliminated: false,
    kicked: false,
    isGameCreator: false,
    nmrExtensionsRemaining: 0,
    civilDisorder: false,
    seekingReplacement: false,
    replaceable: false,
    ...overrides,
  }) as Member;

const publicChannel = { id: 1, name: "Public Press", private: false } as Channel;

const variantNations = [
  { name: "England", flagUrl: "england.svg", color: "#ff0000" },
  { name: "Italy", flagUrl: "italy.svg", color: "#00ff00" },
];

describe("getChannelFlagUrls", () => {
  it("shows one flag per seat when a replaced member still sits in the channel", () => {
    const members = [
      member(1, "England"),
      member(2, "Italy", { kicked: true }),
      member(3, "Italy"),
    ];

    expect(
      getChannelFlagUrls(publicChannel, members, "England", variantNations)
    ).toEqual([
      { flagUrl: "england.svg", color: "#ff0000" },
      { flagUrl: "italy.svg", color: "#00ff00" },
    ]);
  });

  it("takes private channel flags from the channel name rather than the member list", () => {
    const privateChannel = { id: 2, name: "England, Italy", private: true } as Channel;

    expect(
      getChannelFlagUrls(privateChannel, [], "England", variantNations)
    ).toEqual([{ flagUrl: "italy.svg", color: "#00ff00" }]);
  });
});

const sender = (overrides: Partial<ChannelMember> = {}) =>
  ({
    id: 1,
    userId: 1,
    name: "Alice",
    picture: null,
    isCurrentUser: false,
    isBot: false,
    commitment: null,
    nation: { name: "England", color: "#ff0000" },
    isGameMaster: false,
    ...overrides,
  }) as ChannelMember;

describe("getMessageSenderLabel", () => {
  it("uses the nation name for a seated player", () => {
    expect(getMessageSenderLabel(sender())).toBe("England");
  });

  it("uses Game Master for a game master", () => {
    expect(
      getMessageSenderLabel(sender({ nation: null, isGameMaster: true }))
    ).toBe("Game Master");
  });

  it("falls back to the display name when there is no nation", () => {
    expect(getMessageSenderLabel(sender({ nation: null }))).toBe("Alice");
  });
});
