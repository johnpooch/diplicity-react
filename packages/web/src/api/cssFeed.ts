import { z } from "zod";
import { parseOnlyInDev } from "@/lib/parseOnlyInDev";

const cssFeedAttachmentSchema = z.object({
  url: z.string(),
  name: z.string(),
  contentType: z.string().nullable(),
});

const cssFeedMessageSchema = z.object({
  id: z.string(),
  channelId: z.string(),
  authorId: z.string(),
  authorName: z.string(),
  authorAvatar: z.string().nullable(),
  content: z.string(),
  createdAt: z.string(),
  editedAt: z.string().nullable(),
  attachments: z.array(cssFeedAttachmentSchema),
});

const cssFeedChannelSchema = z.object({
  id: z.string(),
  name: z.string(),
  guildId: z.string(),
  messages: z.array(cssFeedMessageSchema),
});

const cssFeedFeedResponseSchema = z.object({
  channels: z.array(cssFeedChannelSchema),
});

type CssFeedMessage = z.infer<typeof cssFeedMessageSchema>;
type CssFeedChannel = z.infer<typeof cssFeedChannelSchema>;

const baseUrl = import.meta.env.VITE_CSS_FEED_API_BASE_URL;
const apiKey = import.meta.env.VITE_CSS_FEED_API_KEY;
const generalChannelId = import.meta.env.VITE_CSS_FEED_GENERAL_CHANNEL_ID;

const cssFeedConfigured = Boolean(baseUrl && apiKey && generalChannelId);

async function fetchWatchedChannels(): Promise<CssFeedChannel[]> {
  if (!cssFeedConfigured) {
    throw new Error("css-feed is not configured");
  }

  const response = await fetch(`${baseUrl}/api/feed`, {
    headers: { "X-Api-Key": apiKey },
  });

  if (!response.ok) {
    throw new Error(`css-feed request failed with status ${response.status}`);
  }

  const data = parseOnlyInDev(cssFeedFeedResponseSchema, await response.json());
  return data.channels;
}

export { fetchWatchedChannels, cssFeedConfigured, generalChannelId };
export type { CssFeedMessage, CssFeedChannel };
