import { useGetOrdersQuery, useGetPhaseQuery, useGetVariantQuery } from "../../common";

type Order = {
    source: string;
    orderType: string;
    target: string | undefined;
    aux: string | undefined;
    outcome: {
        outcome: string;
        by?: string;
    } | undefined;
};

const createOrders = (
    variant: NonNullable<ReturnType<typeof useGetVariantQuery>["data"]>,
    phase: NonNullable<ReturnType<typeof useGetPhaseQuery>["data"]>,
    orders: NonNullable<ReturnType<typeof useGetOrdersQuery>["data"]>
) => {
    const ordersByNation = new Map<string, Order[]>();

    orders.Orders.forEach((order) => {
        const [source, orderType, target, aux] = order.Parts;
        if (!source) throw new Error("No source found");
        if (!orderType) throw new Error("No orderType found");
        const outcome = phase.Resolutions?.find((resolution) => resolution.province === source);

        const orderData = {
            source: variant.ProvinceLongNames[source],
            orderType: orderType,
            target: target ? variant.ProvinceLongNames[target] : undefined,
            aux: aux ? variant.ProvinceLongNames[aux] : undefined,
            outcome: outcome ? {
                outcome: outcome.outcome,
                by: outcome.by ? variant.ProvinceLongNames[outcome.by] : undefined,
            } : undefined,
        };

        if (!ordersByNation.has(order.Nation)) {
            ordersByNation.set(order.Nation, []);
        }

        ordersByNation.get(order.Nation)!.push(orderData);
    });

    return Array.from(ordersByNation.entries()).map(([nation, orders]) => ({
        nation,
        orders,
    }));
}

export { createOrders };