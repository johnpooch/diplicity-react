import { useGetOrdersQuery, useGetPhaseQuery, useGetVariantQuery } from "../../common";

type Outcome = "OK" | "Bounced" | "SupportBroken" | undefined;

type Order = {
    source: string;
    orderType: string;
    target: string | undefined;
    aux: string | undefined;
    outcome: Outcome;
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
        const resolution = phase.Resolutions?.find((resolution) => resolution.Province === source);

        const outcome: Outcome = resolution?.Resolution.includes("OK") ? "OK" : resolution?.Resolution.includes("Bounce") ? "Bounced" : resolution?.Resolution.includes("SupportBroken") ? "SupportBroken" : undefined;

        const orderData = {
            source: variant.getProvinceLongName(source),
            orderType: orderType,
            target: target ? variant.getProvinceLongName(target) : undefined,
            aux: aux ? variant.getProvinceLongName(aux) : undefined,
            outcome: outcome
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