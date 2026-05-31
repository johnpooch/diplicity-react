import { Channel, Member } from "@/api/generated/endpoints";
import { findNationFlagUrl } from "@/components/NationFlag";

export const brightnessByColor = (hex: string): number => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
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
  variantNations: ReadonlyArray<{ name: string; flagUrl: string | null }>
): (string | null)[] => {
  const nations = channel.private
    ? channel.name.split(", ").filter(n => n !== currentNationName)
    : members
        .map(m => m.nation)
        .filter((n): n is string => n !== null && n !== currentNationName);
  return nations.map(nation => findNationFlagUrl(variantNations, nation));
};
