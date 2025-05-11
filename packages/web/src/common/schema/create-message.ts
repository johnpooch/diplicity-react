import { z } from "zod";
import { apiResponseSchema } from "./common";

const createMessageSchema = apiResponseSchema(z.object({
    ID: z.string(),
    Body: z.string(),
    CreatedAt: z.string(),
    ChannelMembers: z.array(z.string()),
    Sender: z.string(),
}));

export { createMessageSchema };
