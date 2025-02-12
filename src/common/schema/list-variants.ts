import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const DEFAULT_FLAGS: Record<string, string> = {
    Austria: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Austria.svg",
    England: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/England.svg",
    France: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/France.svg",
    Germany: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Germany.svg",
    Italy: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Italy.svg",
    Russia: "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Russia.svg",
}

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

        const nations = response.Properties.Nations;

        // Check if the variant has a flag for each nation, if not use the default flag (if it exists)
        nations.forEach(nation => {
            if (!(nation in flags)) {
                flags[nation] = DEFAULT_FLAGS[nation];
            }
        });

        // Joren! Do something simlar for nation colors. Create a default list of colors (similar to the getNationColor function) and assign them here.

        const variant = response.Properties;
        const transformedVariant = { ...variant, Flags: flags, Units: units, Map: map, Provinces: variant.ProvinceLongNames, Colors: variant.NationColors };
        return { ...response, Properties: transformedVariant };
    });

    return { ...data, Properties: transformedProperties };
});

export { listVariantsSchema };