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

type TransformedOrder = {
    source: string;
    destination?: string;
    aux?: string;
} & ({
    type: "Hold" | "Disband" | "Build"
} | {
    type: "Move" | "Retreat" | "MoveViaConvoy";
    source: string;
    destination: string;
} | {
    type: "Support" | "Convoy"
    source: string;
    aux: string;
    destination: string;
})

const listOrdersSchema = apiResponseSchema(corroborationSchema).transform((value) => {
    const { Orders, Inconsistencies } = value.Properties;

    // Convert orders into TransformedOrder type
    const transformOrders = (order: typeof Orders[number]) => {
        const [source, orderType, auxOrDestination, auxDestination] = order.Parts;
        switch (orderType) {
            case "Hold":
                return { type: "Hold", source } as const;
            case "Disband":
                return { type: "Disband", source } as const;
            case "Build":
                return { type: "Build", source } as const;
            case "Move":
                return { type: "Move", source, destination: auxOrDestination } as const;
            case "Retreat":
                return { type: "Retreat", source, destination: auxOrDestination } as const;
            case "Convoy":
                return { type: "Convoy", source, aux: auxOrDestination, destination: auxDestination } as const;
            case "Support":
                return { type: "Support", source, aux: auxOrDestination, destination: auxDestination } as const;
            default:
                throw new Error(`Unknown order type: ${orderType}`);
        }
    };

    // Group orders by nation
    const orders = Orders.reduce((acc, order) => {
        const nation = order.Nation;
        if (!acc[nation]) {
            acc[nation] = [];
        }
        acc[nation].push(transformOrders(order));
        return acc;
    }, {} as Record<string, TransformedOrder[]>);

    // Group inconsistencies by province
    const inconsistencies = Inconsistencies.reduce((acc, inconsistency) => {
        const province = inconsistency.Province;
        if (!acc[province]) {
            acc[province] = [];
        }
        acc[province].push(...inconsistency.Inconsistencies);
        return acc;
    }, {} as Record<string, string[]>);

    return {
        Properties: {
            orders,
            inconsistencies,
        }
    };
})

export { orderSchema, corroborationSchema, listOrdersSchema };