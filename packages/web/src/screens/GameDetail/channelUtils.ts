import { Channel, Member } from "@/api/generated/endpoints";

export type ChannelNation = { flagUrl: string | null; color: string };

export const brightnessByColor = (hex: string): number => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(hex);
  if (!match) return 128;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
};

export const getChannelDisplayName = (
  channel: Channel,
  currentNationName: string | undefined
): string => {
  if (!channel.private || !currentNationName) return channel.name;
  const others = channel.name
    .split(", ")
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
    ? channel.name.split(", ").filter(n => n !== currentNationName)
    : members
        .map(m => m.nation)
        .filter((n): n is string => n !== null);
  return nationNames.map(name => {
    const vn = variantNations.find(n => n.name === name);
    return { flagUrl: vn?.flagUrl ?? null, color: vn?.color ?? "#808080" };
  });
};
