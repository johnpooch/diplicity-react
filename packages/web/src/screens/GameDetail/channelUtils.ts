import { Channel } from "@/api/generated/endpoints";

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
