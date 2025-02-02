import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const channelSchema = z.object({
    Id: z.string(),
    Name: z.string(),
    GameId: z.string(),
    CreatedAt: z.string(),
    CreatedBy: z.string(),
    Members: z.array(z.string()),
});

const listChannelsSchema = listApiResponseSchema(apiResponseSchema(channelSchema));

export { listChannelsSchema };
