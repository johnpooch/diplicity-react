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
    const hasMessagePostLink = data.Links.some(link => link.Rel === "message" && link.Method === "POST");

    const transformedProperties = data.Properties.map((response) => {
        const name = response.Name;
        const messagePreview = response.Properties.LatestMessage.Body;
        const closed = !hasMessagePostLink || response.Properties.Members.includes("Diplicity");
        return { ...response, Properties: { ...response.Properties, Name: name, messagePreview, closed } };
    });

    return { ...data, Properties: transformedProperties };
});

export { listChannelsSchema };
