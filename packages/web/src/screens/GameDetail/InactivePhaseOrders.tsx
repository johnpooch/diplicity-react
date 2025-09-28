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
import { OrderRead, service } from "../../store";
import { OrderSummary } from "../../components/OrderSummary";
import { Panel } from "../../components/Panel";
import { Notice } from "../../components/Notice";
import { IconName } from "../../components/Icon";
import { createUseStyles } from "../../components/utils/styles";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";


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

export const InactivePhaseOrders: React.FC = () => {
    const styles = useStyles({});
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
        gameId,
        phaseId: selectedPhase,
    });

    if (!ordersListQuery.data) return (
        <Panel>
            <Panel.Content>
                <Stack alignItems="center" justifyContent="center" height="100%" sx={{ paddingBottom: "56px" }}>
                </Stack>
            </Panel.Content>
        </Panel>
    );

    const ordersByNation = ordersListQuery.data.reduce((acc, order) => {
        acc[order.nation.name] = [...(acc[order.nation.name] || []), order];
        return acc;
    }, {} as Record<string, OrderRead[]>);

    const hasOrders = Object.values(ordersByNation).some(orders => orders.length > 0);

    return (
        <Panel>
            <Panel.Content>
                {!hasOrders ? (
                    <Stack alignItems="center" justifyContent="center" height="100%" sx={{ paddingBottom: "56px" }}>
                        <Notice
                            title="No orders created"
                            message="No orders were created by any nation in this phase."
                            icon={IconName.NoResults}
                        /></Stack>
                ) : (
                    Object.entries(ordersByNation).map(([nation, orders]) => (
                        <Stack key={nation}>
                            <ListSubheader key={nation}>{nation}</ListSubheader>
                            <Divider />
                            <List disablePadding>
                                {orders.map((order, index) => (
                                    <ListItem
                                        divider
                                        key={`${order.source.id}-${index}`}
                                    >
                                        <ListItemText
                                            primary={
                                                <OrderSummary
                                                    source={order.source.name ?? ""}
                                                    destination={order.target?.name}
                                                    aux={order.aux?.name}
                                                    type={order.orderType}
                                                    unitType={order.unitType}
                                                />
                                            }
                                            secondary={
                                                order.resolution ? (
                                                    <Typography
                                                        variant="body2"
                                                        sx={
                                                            order.resolution.status ===
                                                                "Succeeded"
                                                                ? styles.orderListItemTextSucceeded
                                                                : styles.orderListItemTextFailed
                                                        }
                                                    >
                                                        {order.resolution.status}
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
                    ))
                )}
            </Panel.Content>
        </Panel>
    );
};
