import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const messageSchema = z.object({
    Id: z.string(),
    Body: z.string(),
    CreatedAt: z.string(),
    CreatedBy: z.string(),
    ChannelId: z.string(),
    GameId: z.string(),
    ChannelMembers: z.array(z.string()),
});

const listMessagesSchema = listApiResponseSchema(apiResponseSchema(messageSchema));

export { listMessagesSchema };
