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
import { OrderSummary } from "../../components/OrderSummary";
import { Panel } from "../../components/Panel";
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


    // const orderableProvincesQuery = service.endpoints.gamePhaseOrderableProvincesList.useQuery({
    //     gameId: gameId,
    // });

    const phaseStateRetrieveQuery = service.endpoints.gamePhaseStateRetrieve.useQuery({
        gameId: gameId,
    });

    const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
        gameId,
        phaseId: props.phase.id,
    });

    if (!phaseStateRetrieveQuery.data) return null;

    return (
        <Panel>
            <Panel.Content>
                <List disablePadding>
                    {phaseStateRetrieveQuery.data?.orderableProvinces.map((province) => {
                        const order = ordersListQuery.data?.find(o => o.source.id === province.id);
                        return (
                            <ListItem
                                key={province.id}
                                divider
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
            </Panel.Content>
            <Divider />
            <Panel.Footer>
                <Stack
                    gap={1}
                    direction="row"
                    alignItems={"center"}
                    justifyContent={"flex-end"}
                >
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
                </Stack>
            </Panel.Footer>
        </Panel>
    );
};
