import { z } from "zod";

const apiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Name: z.string(),
    Properties: schema,
    Links: z.union([z.array(z.object({
        Rel: z.string(),
        URL: z.string(),
        Method: z.string(),
    })), z.null()]).transform((links) => links ?? []),
});

const listApiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: z.array(schema),
});

export { apiResponseSchema, listApiResponseSchema };