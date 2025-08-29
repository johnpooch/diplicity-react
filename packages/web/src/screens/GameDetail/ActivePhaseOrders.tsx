import React, { useEffect } from "react";
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
import { NationOrder, orderSlice, Phase, Province, service } from "../../store";
import { Icon, IconName } from "../../components/Icon";
import { IconButton } from "../../components/Button";
import { OrderSummary } from "../../components/OrderSummary";
import { useDispatch } from "react-redux";
import { Panel } from "../../components/Panel";
import { createUseStyles } from "../../components/utils/styles";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";
import { useNavigate } from "react-router";

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

interface ActivePhaseOrdersProps {
    phase: Phase;
    userNation: string;
    nationOrders: NationOrder[];
    provinces: Province[];
    onConfirmOrders: () => void;
    isPhaseConfirmed: boolean;
    isConfirming: boolean;
}

export const ActivePhaseOrders: React.FC<ActivePhaseOrdersProps> = (props) => {
    const styles = useStyles(props);
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const { userNation, onConfirmOrders, isPhaseConfirmed, isConfirming } = props;

    const [getOptions, optionsQuery] = service.endpoints.gamePhaseOptionsCreate.useMutation();

    const ordersQuery = service.endpoints.gamePhaseOrdersList.useQuery({
        gameId: gameId,
        phaseId: selectedPhase,
    });

    // useEffect to call mutation when the component mounts
    useEffect(() => {
        getOptions({
            gameId: gameId,
            phaseId: selectedPhase,
            listOptionsRequest: {
                order: {}
            },
        });
    }, [getOptions, gameId, selectedPhase]);

    const handleCreateOrderForProvince = (provinceId: string) => {
        dispatch(orderSlice.actions.resetOrder());
        dispatch(orderSlice.actions.updateOrder(provinceId));
        navigate(`/game/${gameId}/create-order`);
    };

    if (!optionsQuery.data || !ordersQuery.data) return null;

    const nationOrder = ordersQuery.data?.find(o => o.nation === userNation);

    return (
        <Panel>
            <Panel.Content>
                <List disablePadding>
                    {optionsQuery.data?.map((option) => {
                        const order = nationOrder?.orders.find(o => o.source === option.province.id);
                        return (
                            <ListItem
                                key={option.province.id}
                                divider
                                secondaryAction={
                                    <IconButton
                                        icon={IconName.CreateOrder}
                                        onClick={() =>
                                            handleCreateOrderForProvince(option.province.id)
                                        }
                                    />
                                }
                            >
                                <ListItemText
                                    primary={
                                        order ? (
                                            <OrderSummary
                                                source={option.province.name}
                                                destination={order.target}
                                                aux={order.aux}
                                                type={order.orderType}
                                            />
                                        ) : (
                                            <Typography variant="body1">
                                                {option.unit
                                                    ? `${option.unit.type.charAt(0).toUpperCase()}${option.unit.type.slice(1)} ${option.province.name}`
                                                    : option.province.name}
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
