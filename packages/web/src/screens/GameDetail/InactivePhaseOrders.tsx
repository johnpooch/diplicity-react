import React from "react";
import {
    Divider,
    List,
    ListItem,
    ListItemText,
    ListSubheader,
    Stack,
    Typography,
} from "@mui/material";
import { OrderListResponse, Phase, Province } from "../../store";
import { OrderSummary } from "../../components/OrderSummary";
import { Panel } from "../../components/Panel-x";
import { createUseStyles } from "../../components/utils/styles";

type Orderable = {
    province?: Province;
    provinceId: string;
    unitType?: string;
    order?: {
        target?: Province;
        aux?: Province;
        orderType?: string;
        resolution?: {
            status?: string;
            by?: string;
        };
    };
};

const generateOrderables = (
    phase: Phase,
    nationOrders: OrderListResponse[],
    provinces: Province[]
) => {
    const { options } = phase;
    const orderables: Record<string, Orderable[]> = {};

    // For inactive phases, show all nations
    const nations = Object.keys(options);

    nations.forEach(nation => {
        const sources = Object.keys(options[nation]);
        const orders = nationOrders.find(o => o.nation === nation)?.orders ?? [];

        orderables[nation] = sources.map(source => {
            const order = orders.find(o => o.source.id === source);
            return {
                province: provinces.find(p => p.id === source),
                provinceId: source,
                unitType: phase.units.find(u => u.province.id === source)?.type,
                order: order
                    ? {
                        target: provinces.find(p => p.id === order.target?.id),
                        aux: provinces.find(p => p.id === order.aux?.id),
                        orderType: order.orderType,
                        resolution: order.resolution
                            ? {
                                status: order.resolution.status,
                                by: order.resolution.by ?? undefined,
                            }
                            : undefined,
                    }
                    : undefined,
            };
        });
    });

    return orderables;
};

const useStyles = createUseStyles(() => ({
    orderListItemTextSucceeded: {
        color: "green",
    },
    orderListItemTextFailed: {
        color: "red",
    },
    noOrderText: {
        color: "gray",
    },
}));

interface InactivePhaseOrdersProps {
    phase: Phase;
    nationOrders: OrderListResponse[];
    provinces: Province[];
}

export const InactivePhaseOrders: React.FC<InactivePhaseOrdersProps> = (props) => {
    const styles = useStyles(props);
    const { phase, nationOrders, provinces } = props;

    const orderables = generateOrderables(phase, nationOrders, provinces);

    return (
        <Panel>
            <Panel.Content>
                {Object.entries(orderables).map(([nation, orderables]) => (
                    <Stack key={nation}>
                        <ListSubheader key={nation}>{nation}</ListSubheader>
                        <Divider />
                        <List disablePadding>
                            {orderables.map((orderable, index) => (
                                <ListItem
                                    divider
                                    key={`${orderable.provinceId}-${index}`}
                                >
                                    <ListItemText
                                        primary={
                                            orderable.order ? (
                                                <OrderSummary
                                                    source={orderable.province?.name ?? ""}
                                                    destination={orderable.order.target?.name}
                                                    aux={orderable.order.aux?.name}
                                                    type={orderable.order.orderType}
                                                />
                                            ) : (
                                                <Typography variant="body1">
                                                    {orderable.unitType
                                                        ? `${orderable.unitType.charAt(0).toUpperCase()}${orderable.unitType.slice(1)} ${orderable.province}`
                                                        : orderable.province?.name}
                                                </Typography>
                                            )
                                        }
                                        secondary={
                                            orderable.order && orderable.order.resolution ? (
                                                <Typography
                                                    variant="body2"
                                                    sx={
                                                        orderable.order.resolution.status ===
                                                            "Succeeded"
                                                            ? styles.orderListItemTextSucceeded
                                                            : styles.orderListItemTextFailed
                                                    }
                                                >
                                                    {orderable.order.resolution.status}
                                                </Typography>
                                            ) : (
                                                <Typography variant="body2" sx={styles.noOrderText}>
                                                    No order issued
                                                </Typography>
                                            )
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Stack>
                ))}
            </Panel.Content>
        </Panel>
    );
};
