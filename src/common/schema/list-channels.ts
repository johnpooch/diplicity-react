import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const channelSchema = z.object({
    Members: z.array(z.string()),
    NMessages: z.number(),
    LatestMessage: z.object({
        Sender: z.string(),
        Body: z.string(),
        CreatedAt: z.string(),
        Age: z.number(),
    })
});

const listChannelsSchema = listApiResponseSchema(apiResponseSchema(channelSchema)).transform((data) => {
    const transformedProperties = data.Properties.map((response) => {
        const name = response.Name
        return { ...response, Properties: { ...response.Properties, Name: name } };
    })
    return { ...data, Properties: transformedProperties };
});


export { listChannelsSchema };
