import { Channel, ChannelMember, Member } from "@/api/generated/endpoints";

export type ChannelNation = { flagUrl: string | null; color: string };

export const GAME_MASTER_LABEL = "Game Master";

export const NEUTRAL_SENDER_COLOR = "#808080";

export const getMessageSenderLabel = (sender: ChannelMember): string => {
  if (sender.isGameMaster) return GAME_MASTER_LABEL;
  return sender.nation?.name ?? sender.name;
};

// Normalise any hex colour to 6-digit form (#RRGGBB). Falls back to grey for
// non-hex values (e.g. rgb()) so callers can safely concatenate an alpha byte.
export const toHex6 = (color: string): string => {
  const short = /^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$/.exec(color);
  if (short) return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`;
  if (/^#[0-9a-fA-F]{6}$/.test(color)) return color;
  return "#808080";
};

export const brightnessByColor = (hex: string): number => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(toHex6(hex));
  if (!match) return 128;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
};

// Private channel names are formatted by the backend as "Nation1, Nation2, ..."
const getOtherNationNames = (
  channel: Channel,
  currentNationName: string | undefined
): string[] =>
  channel.name
    .split(",")
    .map(s => s.trim())
    .filter(n => n !== currentNationName);

export const getChannelDisplayName = (
  channel: Channel,
  currentNationName: string | undefined
): string => {
  if (channel.title) return channel.title;
  if (!channel.private || !currentNationName) return channel.name;
  const others = getOtherNationNames(channel, currentNationName);
  return others.length > 0 ? others.join(", ") : channel.name;
};

// Whatever the title does not already say: the nations for a named
// channel, and the players behind them for an unnamed one.
export const getChannelSubtitle = (
  channel: Channel,
  members: readonly Member[],
  currentNationName: string | undefined
): string | null => {
  if (!channel.private) return null;
  const others = getOtherNationNames(channel, currentNationName);
  if (others.length === 0) return null;
  if (channel.title) return others.join(", ");
  const playerNames = others
    .map(nation => members.find(m => m.nation === nation)?.name)
    .filter((name): name is string => name !== undefined);
  return playerNames.length > 0 ? playerNames.join(", ") : null;
};

const getChannelNationNames = (
  channel: Channel,
  members: readonly Member[],
  currentNationName: string | undefined
): string[] =>
  channel.private
    ? getOtherNationNames(channel, currentNationName)
    : members
        .filter(m => !m.kicked)
        .map(m => m.nation)
        .filter((n): n is string => n !== null);

export const getChannelFlagUrls = (
  channel: Channel,
  members: readonly Member[],
  currentNationName: string | undefined,
  variantNations: ReadonlyArray<{ name: string; flagUrl: string | null; color: string }>
): ChannelNation[] => {
  const nationNames = getChannelNationNames(channel, members, currentNationName);
  return nationNames.map(name => {
    const vn = variantNations.find(n => n.name === name);
    return { flagUrl: vn?.flagUrl ?? null, color: vn?.color ?? "#808080" };
  });
};

// Public Press is never a direct 1:1 conversation, however few nations
// currently have a seat in it, so it always shows sender labels; only a
// private channel can be the direct kind that hides them.
export const isGroupChannel = (
  channel: Channel,
  members: readonly Member[],
  currentNationName: string | undefined
): boolean =>
  !channel.private ||
  getChannelNationNames(channel, members, currentNationName).length > 1;
