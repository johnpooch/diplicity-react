import { describe, it, expect } from "vitest";
import type { Channel, Member } from "@/api/generated/endpoints";
import {
  getChannelDisplayName,
  getChannelFlagUrls,
  getChannelSubtitle,
} from "./channelUtils";

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

describe("getChannelDisplayName", () => {
  it("prefers the name the players gave the channel", () => {
    const channel = {
      id: 2,
      name: "England, Italy",
      title: "The great alliance",
      private: true,
    } as Channel;

    expect(getChannelDisplayName(channel, "England")).toBe("The great alliance");
  });

  it("falls back to the other nations when the channel has no name", () => {
    const channel = { id: 2, name: "England, Italy", private: true } as Channel;

    expect(getChannelDisplayName(channel, "England")).toBe("Italy");
  });
});

describe("getChannelSubtitle", () => {
  it("names the players behind the nations when the channel has no name", () => {
    const channel = { id: 2, name: "England, Italy", private: true } as Channel;
    const members = [member(1, "England"), member(2, "Italy")];

    expect(getChannelSubtitle(channel, members, "England")).toBe("Player 2");
  });

  it("lists the nations when the channel has a name of its own", () => {
    const channel = {
      id: 2,
      name: "England, Italy",
      title: "The great alliance",
      private: true,
    } as Channel;
    const members = [member(1, "England"), member(2, "Italy")];

    expect(getChannelSubtitle(channel, members, "England")).toBe("Italy");
  });

  it("is empty for a public channel, whose title says everything", () => {
    expect(getChannelSubtitle(publicChannel, [], "England")).toBeNull();
  });

  it("is empty when no member holds the nation any more", () => {
    const channel = { id: 2, name: "England, Italy", private: true } as Channel;

    expect(getChannelSubtitle(channel, [member(1, "England")], "England")).toBeNull();
  });
});

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
