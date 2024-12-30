import { z } from "zod";
import { apiResponseSchema } from "./common";

const inconsistencySchema = z.object({
    Inconsistencies: z.array(z.string()),
    Province: z.string(),
});

const orderSchema = z.object({
    GameID: z.string(),
    PhaseOrdinal: z.number(),
    Nation: z.string(),
    Parts: z.array(z.string()),
});

const corroborationSchema = z.object({
    Orders: z.union([z.array(orderSchema), z.null()]).transform((val) => val === null ? [] : val),
    Inconsistencies: z.array(inconsistencySchema),
});

const listOrdersSchema = apiResponseSchema(corroborationSchema);

export { orderSchema, corroborationSchema, listOrdersSchema };