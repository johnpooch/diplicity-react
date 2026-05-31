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
): (string | null)[] =>
  channel.memberIds
    .map(id => members.find(m => m.id === id)?.nation ?? null)
    .filter((nation): nation is string => nation !== null && nation !== currentNationName)
    .map(nation => findNationFlagUrl(variantNations, nation));
