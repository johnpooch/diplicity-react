import { Channel, Member } from "@/api/generated/endpoints";
import { findNationFlagUrl } from "@/components/NationFlag";

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
