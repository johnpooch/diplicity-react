import React from "react";
import { Button, Divider, List, ListSubheader, Stack } from "@mui/material";
import { Phase, service } from "../../store";
import { Icon, IconName } from "../../components/Icon";
import { Panel } from "../../components/Panel";
import { Notice } from "../../components/Notice";
import { useSelectedGameContext } from "../../context";
import { OrderCard } from "../../components/OrderCard";
import { IconButton } from "../../components/Button";
import { MemberAvatar } from "../../components/MemberAvatar";

interface ActivePhaseOrdersProps {
  phase: Phase;
  userNation: string;
  onConfirmOrders: () => void;
  isPhaseConfirmed: boolean;
  isConfirming: boolean;
}

export const ActivePhaseOrders: React.FC<ActivePhaseOrdersProps> = props => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();

  const { onConfirmOrders, isPhaseConfirmed, isConfirming } = props;

  const phaseStateRetrieveQuery =
    service.endpoints.gamePhaseStateRetrieve.useQuery({
      gameId: gameId,
    });

  const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
    gameId,
    phaseId: props.phase.id,
  });

  const [deleteOrder, deleteOrderMutation] =
    service.endpoints.gameOrdersDeleteDestroy.useMutation();

  const handleDeleteOrder = (sourceId: string) => {
    deleteOrder({ gameId, sourceId });
  };

  if (!phaseStateRetrieveQuery.data)
    return (
      <Panel>
        <Panel.Content>
          <Stack
            alignItems="center"
            justifyContent="center"
            height="100%"
            sx={{ paddingBottom: "56px" }}
          ></Stack>
        </Panel.Content>
      </Panel>
    );

  const hasOrderableProvinces =
    phaseStateRetrieveQuery.data?.orderableProvinces.length > 0;

  const variant = gameRetrieveQuery?.data?.variant.id;
  const member = gameRetrieveQuery?.data?.members.find(
    m => m.nation === props.userNation
  );

  return (
    <Panel>
      <Panel.Content>
        {!hasOrderableProvinces ? (
          <Stack
            alignItems="center"
            justifyContent="center"
            height="100%"
            sx={{ paddingBottom: "56px" }}
          >
            <Notice
              title="No orders required"
              message="You do not need to submit any orders during this phase"
              icon={IconName.Empty}
            />
          </Stack>
        ) : (
          <List disablePadding>
            <ListSubheader
              key={props.userNation}
              sx={{
                color: "text.primary",
                paddingLeft: 1,
                paddingRight: 1,
                fontSize: "15px",
              }}
            >
              <Stack direction="row" gap={1} alignItems="center">
                <MemberAvatar
                  member={member!}
                  size="small"
                  variant={variant!}
                />
                {props.userNation}
              </Stack>
            </ListSubheader>
            <Divider />
            {phaseStateRetrieveQuery.data?.orderableProvinces.map(province => {
              const order = ordersListQuery.data?.find(
                o => o.source.id === province.id
              );
              const unit = props.phase.units.find(
                u => u.province.id === province.id
              );
              return (
                <OrderCard
                  province={province}
                  unit={unit}
                  order={order}
                  key={province.id}
                  primaryAction={
                    order ? (
                      <IconButton
                        icon={IconName.Delete}
                        onClick={() => handleDeleteOrder(province.id)}
                        disabled={deleteOrderMutation.isLoading}
                      />
                    ) : null
                  }
                />
              );
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
              startIcon={<Icon name={IconName.OrdersConfirmed} />}
            >
              Orders confirmed
            </Button>
          )}
        </Stack>
      </Panel.Footer>
    </Panel>
  );
};
