import React, { useState } from "react";
import {
    Button,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListSubheader,
    Stack,
    Typography,
} from "@mui/material";
import { NationOrder, orderSlice, Phase, Province, service } from "../../../store";
import { GameDetailAppBar } from "../../composites/GameDetailAppBar";
import { GameDetailLayout } from "../../layouts/GameDetailLayout";
import { useNavigate, useParams } from "react-router";
import { Icon, IconName } from "../../elements/Icon";
import { IconButton } from "../../elements/Button";
import { PhaseSelect } from "../../composites/PhaseSelect";
import { useSelectedPhaseContext } from "../../../context";
import { createUseStyles } from "../../utils/styles";
import { OrderSummary } from "../../order-summary";
import { CreateOrder } from "../../create-order";
import { useDispatch } from "react-redux";
import { Panel } from "../../panel";
import { Map } from "../../map";

/**
 * Represents a unit or province that can be ordered in the given phase.
 */
type Orderable = {
    province?: string;
    provinceId: string;
    unitType?: string;
    order?: {
        target?: string;
        aux?: string;
        orderType?: string;
        resolution?: {
            status?: string;
            by?: string;
        };
    };
};

const generateOrderables = (
    phase: Phase,
    userNation: string,
    nationOrders: NationOrder[],
    provinces: Province[]
) => {
    const { options } = phase;
    const orderables: Record<string, Orderable[]> = {};

    const nations = Object.keys(options).filter(nation => {
        if (phase.status === "active") {
            return nation === userNation;
        }
        return true;
    });

    // Get sources for each nation and add to an object
    const sources: Record<string, string[]> = {};
    nations.forEach(nation => {
        sources[nation] = Object.keys(options[nation]);
    });

    nations.forEach(nation => {
        const sources = Object.keys(options[nation]);
        const orders = nationOrders.find(o => o.nation === nation)?.orders ?? [];

        orderables[nation] = sources.map(source => {
            const order = orders.find(o => o.source === source);
            return {
                province: provinces.find(p => p.id === source)?.name,
                provinceId: source,
                unitType: phase.units.find(u => u.province.id === source)?.type,
                order: order
                    ? {
                        target: provinces.find(p => p.id === order.target)?.name,
                        aux: provinces.find(p => p.id === order.aux)?.name,
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
}));

const OrdersScreen: React.FC = props => {
    const { gameId } = useParams<{ gameId: string }>();
    if (!gameId) throw new Error("Game ID is required");

    const styles = useStyles(props);
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const [showCreateOrder, setShowCreateOrder] = useState(false);

    const { selectedPhase } = useSelectedPhaseContext();

    const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
        gameId,
    });

    const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
        gameId,
        phaseId: selectedPhase,
    });

    const [confirmOrders, confirmOrdersMutation] =
        service.endpoints.gameConfirmCreate.useMutation();

    const handleConfirmOrders = async () => {
        await confirmOrders({ gameId }).unwrap();
    };

    if (
        gameRetrieveQuery.isError ||
        !gameRetrieveQuery.data ||
        ordersListQuery.isError ||
        !ordersListQuery.data
    ) {
        return null;
    }

    const game = gameRetrieveQuery.data;
    const orders = ordersListQuery.data;

    const orderables = generateOrderables(
        game.phases.find(p => p.id === selectedPhase)!,
        game.members.find(m => m.isCurrentUser)!.nation,
        orders,
        game.variant.provinces
    );

    const handleCreateOrderForProvince = (provinceId: string) => {
        dispatch(orderSlice.actions.resetOrder());
        dispatch(orderSlice.actions.updateOrder(provinceId));
        setShowCreateOrder(true);
    };

    return (
        <GameDetailLayout
            appBar={<GameDetailAppBar title={<PhaseSelect />} onNavigateBack={() => navigate("/")} />}
            rightPanel={
                <Map />
            }
            content={
                <Panel>
                    <Panel.Content>
                        {Object.entries(orderables).map(([nation, orderables]) => (
                            <Stack>
                                <ListSubheader key={nation}>{nation}</ListSubheader>
                                <Divider />
                                <List disablePadding>
                                    {orderables.map(orderable => (
                                        <ListItem
                                            divider
                                            secondaryAction={
                                                <IconButton
                                                    icon={IconName.CreateOrder}
                                                    onClick={() =>
                                                        handleCreateOrderForProvince(orderable.provinceId)
                                                    }
                                                />
                                            }
                                        >
                                            <ListItemText
                                                primary={
                                                    orderable.order ? (
                                                        <OrderSummary
                                                            source={orderable.province as string}
                                                            destination={orderable.order.target}
                                                            aux={orderable.order.aux}
                                                            type={orderable.order.orderType}
                                                        />
                                                    ) : (
                                                        <Typography variant="body1">
                                                            {orderable.unitType
                                                                ? `${orderable.unitType.charAt(0).toUpperCase()}${orderable.unitType.slice(1)} ${orderable.province}`
                                                                : orderable.province}
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
                    <Divider />
                    <Panel.Footer>
                        {showCreateOrder ? (
                            <CreateOrder onClose={() => setShowCreateOrder(false)} />
                        ) : (
                            <Stack
                                gap={1}
                                direction="row"
                                alignItems={"center"}
                                justifyContent={"flex-end"}
                            >
                                <Button
                                    variant="contained"
                                    size="medium"
                                    disabled={confirmOrdersMutation.isLoading}
                                    onClick={handleConfirmOrders}
                                    startIcon={
                                        game.phaseConfirmed ? (
                                            <Icon name={IconName.OrdersConfirmed} />
                                        ) : (
                                            <Icon name={IconName.OrdersNotConfirmed} />
                                        )
                                    }
                                >
                                    {game.phaseConfirmed ? "Orders confirmed" : "Confirm orders"}
                                </Button>
                            </Stack>
                        )}
                    </Panel.Footer>
                </Panel>
            }
        />
    );
};

export { OrdersScreen };

