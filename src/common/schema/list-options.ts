import { z } from "zod";

const baseOptionSchema = z.object({
    Type: z.string(),
});

type Option = z.infer<typeof baseOptionSchema> & {
    Next: Record<string, Option>;
}

const optionSchema: z.ZodType<Option> = baseOptionSchema.extend({
    Next: z.record(z.lazy(() => optionSchema)),
});

type TransformedOption = Option & {
    Next: Record<string, TransformedOption>;
    Name?: string;
}

const listOptionsSchema = z.object({
    Properties: z.record(optionSchema).transform((options) => {
        const transformOptions = (options: Record<string, Option>): Record<string, TransformedOption> => {
            const transformedOptions: Record<string, TransformedOption> = {};

            Object.entries(options).forEach(([key, value]) => {
                if (value.Type !== "SrcProvince") {
                    transformedOptions[key] = {
                        ...value,
                        Next: transformOptions(value.Next),
                        Name: undefined
                    };
                } else {
                    Object.assign(transformedOptions, transformOptions(value.Next));
                }
            });

            return transformedOptions;
        };

        return transformOptions(options);
    })
})

export { listOptionsSchema };