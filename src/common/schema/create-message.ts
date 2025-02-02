import { z } from "zod";
import { apiResponseSchema } from "./common";

const createMessageSchema = apiResponseSchema(z.object({
    Id: z.string(),
    Body: z.string(),
    CreatedAt: z.string(),
    CreatedBy: z.string(),
    ChannelId: z.string(),
    GameId: z.string(),
    ChannelMembers: z.array(z.string()),
}));

export { createMessageSchema };
