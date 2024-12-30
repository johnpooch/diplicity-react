import { z } from "zod"

const apiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: schema,
    Links: z.array(z.object({
        Rel: z.string(),
        URL: z.string(),
        Method: z.string(),
    })),
})

const listApiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: z.array(schema),
})

export { apiResponseSchema, listApiResponseSchema }