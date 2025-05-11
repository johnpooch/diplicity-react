import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const phaseStateSchema = z.object({
    PhaseOrdinal: z.number(),
    Nation: z.string(),
    ReadyToResolve: z.boolean(),
    WantsDIAS: z.boolean(),
    WantsConcede: z.boolean(),
    OnProbation: z.boolean(),
    NoOrders: z.boolean(),
    Eliminated: z.boolean(),
    Messages: z.string(),
});

const listPhaseStatesSchema = listApiResponseSchema(apiResponseSchema(phaseStateSchema)).transform((data) => {
    const transformLinks = (links: ReturnType<ReturnType<typeof apiResponseSchema>["parse"]>["Links"]) => {
        const canUpdate = links.some(link => link.Rel === "update");
        return { canUpdate };
    };

    const transformedProperties = data.Properties.map((response) => {
        const { canUpdate } = transformLinks(response.Links);
        const phaseState = response.Properties;
        const transformedPhaseState = { ...phaseState, canUpdate };
        return { ...response, Properties: transformedPhaseState };
    });

    return { ...data, Properties: transformedProperties };
});

export { listPhaseStatesSchema };