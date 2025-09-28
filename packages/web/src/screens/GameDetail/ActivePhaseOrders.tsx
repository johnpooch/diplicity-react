import React from "react";
import {
    Button,
    Divider,
    List,
    ListItem,
    ListItemText,
    Stack,
    Typography,
} from "@mui/material";
import { Phase, service } from "../../store";
import { Icon, IconName } from "../../components/Icon";
import { IconButton } from "../../components/Button";
import { OrderSummary } from "../../components/OrderSummary";
import { Panel } from "../../components/Panel";
import { Notice } from "../../components/Notice";
import { useSelectedGameContext } from "../../context";

interface ActivePhaseOrdersProps {
    phase: Phase;
    userNation: string;
    onConfirmOrders: () => void;
    isPhaseConfirmed: boolean;
    isConfirming: boolean;
}

export const ActivePhaseOrders: React.FC<ActivePhaseOrdersProps> = (props) => {
    const { gameId } = useSelectedGameContext();

    const { onConfirmOrders, isPhaseConfirmed, isConfirming } = props;

    const phaseStateRetrieveQuery = service.endpoints.gamePhaseStateRetrieve.useQuery({
        gameId: gameId,
    });

    const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
        gameId,
        phaseId: props.phase.id,
    });

    const [deleteOrder, deleteOrderMutation] = service.endpoints.gameOrdersDeleteDestroy.useMutation();

    const handleDeleteOrder = (sourceId: string) => {
        deleteOrder({ gameId, sourceId });
    };

    if (!phaseStateRetrieveQuery.data) return (
        <Panel>
            <Panel.Content>
                <Stack alignItems="center" justifyContent="center" height="100%" sx={{ paddingBottom: "56px" }}>
                </Stack>
            </Panel.Content>
        </Panel>
    );

    const hasOrderableProvinces = phaseStateRetrieveQuery.data?.orderableProvinces.length > 0;

    return (
        <Panel>
            <Panel.Content>
                {!hasOrderableProvinces ? (
                    <Stack alignItems="center" justifyContent="center" height="100%" sx={{ paddingBottom: "56px" }}>
                        <Notice
                            title="No orders required"
                            message="You do not need to submit any orders during this phase"
                            icon={IconName.Empty}
                        />
                    </Stack>
                ) : (
                    <List disablePadding>
                        {phaseStateRetrieveQuery.data?.orderableProvinces.map((province) => {
                            const order = ordersListQuery.data?.find(o => o.source.id === province.id);
                            return (
                                <ListItem
                                    key={province.id}
                                    divider
                                    secondaryAction={
                                        order ? (
                                            <IconButton
                                                icon={IconName.Delete}
                                                onClick={() => handleDeleteOrder(province.id)}
                                                disabled={deleteOrderMutation.isLoading}
                                            />
                                        ) : null
                                    }
                                >
                                    <ListItemText
                                        primary={
                                            order ? (
                                                <OrderSummary
                                                    source={province.name}
                                                    destination={order.target?.name || null}
                                                    aux={order.aux?.name || null}
                                                    type={order.orderType}
                                                />
                                            ) : (
                                                <Typography variant="body1">
                                                    {province.name}
                                                </Typography>
                                            )
                                        }
                                    />
                                </ListItem>
                            )
                        })}
                    </List>
                )}
            </Panel.Content>
            <Divider />
            <Panel.Footer>
                <Stack
                    gap={1}
                    direction="row"
                    alignItems={"center"}
                    justifyContent={"flex-end"}
                >
                    {hasOrderableProvinces ? (
                        <Button
                            variant="contained"
                            size="medium"
                            disabled={isConfirming}
                            onClick={onConfirmOrders}
                            startIcon={
                                isPhaseConfirmed ? (
                                    <Icon name={IconName.OrdersConfirmed} />
                                ) : (
                                    <Icon name={IconName.OrdersNotConfirmed} />
                                )
                            }
                        >
                            {isPhaseConfirmed ? "Orders confirmed" : "Confirm orders"}
                        </Button>
                    ) : (
                        <Button
                            variant="contained"
                            size="medium"
                            disabled={true}
                            startIcon={
                                <Icon name={IconName.OrdersConfirmed} />
                            }
                        >
                            Orders confirmed
                        </Button>
                    )}
                </Stack>
            </Panel.Footer>
        </Panel>
    );
};
