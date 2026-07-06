import { Channel, ChannelMember, Member } from "@/api/generated/endpoints";

export type ChannelNation = { flagUrl: string | null; color: string };

// Placeholder for channel members without an assigned nation yet (staging chat).
export const DEFAULT_NATION_COLOR = "#808080";

// Normalise any hex colour to 6-digit form (#RRGGBB). Falls back to grey for
// non-hex values (e.g. rgb()) so callers can safely concatenate an alpha byte.
export const toHex6 = (color: string): string => {
  const short = /^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$/.exec(color);
  if (short) return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`;
  if (/^#[0-9a-fA-F]{6}$/.test(color)) return color;
  return DEFAULT_NATION_COLOR;
};

// Before a game starts, members have no nation yet — fall back to their name.
export const getSenderDisplayName = (sender: Pick<ChannelMember, "name" | "nation">): string =>
  sender.nation?.name ?? sender.name;

export const brightnessByColor = (hex: string): number => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(toHex6(hex));
  if (!match) return 128;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
};

// Private channel names are formatted by the backend as "Nation1, Nation2, ..."
export const getChannelDisplayName = (
  channel: Channel,
  currentNationName: string | undefined
): string => {
  if (!channel.private || !currentNationName) return channel.name;
  const others = channel.name
    .split(",")
    .map(s => s.trim())
    .filter(n => n !== currentNationName);
  return others.length > 0 ? others.join(", ") : channel.name;
};

export const getChannelFlagUrls = (
  channel: Channel,
  members: readonly Member[],
  currentNationName: string | undefined,
  variantNations: ReadonlyArray<{ name: string; flagUrl: string | null; color: string }>
): ChannelNation[] => {
  const nationNames = channel.private
    ? channel.name.split(",").map(s => s.trim()).filter(n => n !== currentNationName)
    : members
        .map(m => m.nation)
        .filter((n): n is string => n !== null);
  return nationNames.map(name => {
    const vn = variantNations.find(n => n.name === name);
    return { flagUrl: vn?.flagUrl ?? null, color: vn?.color ?? DEFAULT_NATION_COLOR };
  });
};
