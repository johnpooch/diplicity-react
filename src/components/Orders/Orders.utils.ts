import { useGetOrdersQuery, useGetVariantQuery } from "../../common";

type Order = {
    source: string;
    unitTypeSvg: string;
    orderType: string;
    target: string | undefined;
    aux: string | undefined;
};

const createOrders = (
    variant: NonNullable<ReturnType<typeof useGetVariantQuery>["data"]>,
    orders: NonNullable<ReturnType<typeof useGetOrdersQuery>["data"]>
) => {
    const ordersByNation = new Map<string, Order[]>();

    orders.Orders.forEach((order) => {
        const [source, orderType, target, aux] = order.Parts;
        if (!source) throw new Error("No source found");
        if (!orderType) throw new Error("No orderType found");

        const orderData = {
            source: variant.getProvinceLongName(source),
            orderType: orderType,
            target: target ? variant.getProvinceLongName(target) : undefined,
            aux: aux ? variant.getProvinceLongName(aux) : undefined,
            unitTypeSvg: variant.getUnitTypeSrc(source),
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