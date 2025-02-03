import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const messageSchema = z.object({
    ID: z.string(),
    Sender: z.string(),
    Body: z.string(),
    CreatedAt: z.string().transform((value) => new Date(value)),
});

const listMessagesSchema = listApiResponseSchema(apiResponseSchema(messageSchema));

export { listMessagesSchema };
