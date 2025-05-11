import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";
import { transformResolution } from "../../util";

const unitSchema = z.object({
    Type: z.string(),
    Nation: z.string(),
});

const unitStateSchema = z.object({
    Province: z.string(),
    Unit: unitSchema,
});

const scStateSchema = z.object({
    Province: z.string(),
    Owner: z.string(),
});

const dislodgedSchema = z.object({
    Province: z.string(),
    Dislodged: unitSchema,
});

const dislodgerSchema = z.object({
    Province: z.string(),
    Dislodger: z.string(),
});

const bounceSchema = z.object({
    Province: z.string(),
    BounceList: z.string(),
});

const resolutionSchema = z.object({
    Province: z.string(),
    Resolution: z.string(),
});


const phaseSchema = z.object({
    PhaseOrdinal: z.number(),
    Season: z.string(),
    Year: z.number(),
    Type: z.string(),
    Resolved: z.boolean(),
    CreatedAt: z.string(),
    CreatedAgo: z.number(),
    ResolvedAt: z.string(),
    ResolvedAgo: z.number(),
    DeadlineAt: z.string(),
    NextDeadlineIn: z.number(),
    UnitsJSON: z.string(),
    SCsJSON: z.string(),
    GameID: z.string(),
    Units: z.array(unitStateSchema),
    SCs: z.array(scStateSchema),
    Dislodgeds: z.array(dislodgedSchema).nullable(),
    Dislodgers: z.array(dislodgerSchema).nullable(),
    ForceDisbands: z.array(z.string()).nullable(),
    Bounces: z.array(bounceSchema).nullable(),
    Resolutions: z.union([z.array(resolutionSchema), z.null()]).transform((data) => {
        if (data === null) return [];
        return data.map((resolution) => {
            const { outcome, by } = transformResolution(resolution.Resolution);
            return { province: resolution.Province, outcome, by };
        })
    }),
    Host: z.string(),
    SoloSCCount: z.number(),
});


// Create the listPhasesSchema
const listPhasesSchema = listApiResponseSchema(apiResponseSchema(phaseSchema)).transform((data) => {
    const transformLinks = (links: ReturnType<ReturnType<typeof apiResponseSchema>["parse"]>["Links"]) => {
        const canCreateOrder = links.some(link => link.Rel === "create-order");
        return { canCreateOrder };
    };

    const transformedProperties = data.Properties.map((response) => {
        const { canCreateOrder } = transformLinks(response.Links);
        const phase = response.Properties;
        const transformedPhase = { ...phase, canCreateOrder };
        return { ...response, Properties: transformedPhase };
    });

    return { ...data, Properties: transformedProperties };
});

type Phase = z.infer<typeof listPhasesSchema>["Properties"][0]["Properties"];

export { listPhasesSchema };
export type { Phase };