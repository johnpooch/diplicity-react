import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const variantSchema = z.object({
    Name: z.string(),
    Nations: z.array(z.string()),
    ProvinceLongNames: z.union([z.record(z.string(), z.string()), z.null()]).transform((val) => val === null ? {} : val),
    NationColors: z.union([z.record(z.string(), z.string()), z.null()]).transform((val) => val === null ? {} : val),
    CreatedBy: z.string(),
    Description: z.string(),
    Rules: z.string(),
    Start: z.object({
        Year: z.number(),
        Season: z.string(),
        Type: z.string(),
    }),
})

const listVariantsSchema = listApiResponseSchema(apiResponseSchema(variantSchema)).transform((data) => {
    const transformLinks = (links: ReturnType<ReturnType<typeof apiResponseSchema>["parse"]>["Links"]) => {
        const flagLinks = links.filter(link => link.Rel.startsWith("flag-"));
        const unitLinks = links.filter(link => link.Rel.startsWith("unit-"));
        const mapLink = links.find(link => link.Rel === "map");

        const flags = flagLinks.reduce((acc, link) => {
            const nation = link.Rel.replace("flag-", "");
            acc[nation] = link.URL;
            return acc;
        }, {} as Record<string, string>);

        const units = unitLinks.reduce((acc, link) => {
            const unit = link.Rel.replace("unit-", "");
            acc[unit] = link.URL;
            return acc;
        }, {} as Record<string, string>);

        return { flags, units, map: mapLink?.URL };
    };

    const transformedProperties = data.Properties.map((response) => {
        const { flags, units, map } = transformLinks(response.Links);
        const variant = response.Properties;
        const transformedVariant = { ...variant, Flags: flags, Units: units, Map: map, Provinces: variant.ProvinceLongNames, Colors: variant.NationColors };
        return { ...response, Properties: transformedVariant };
    });

    return { ...data, Properties: transformedProperties };
});

export { listVariantsSchema };