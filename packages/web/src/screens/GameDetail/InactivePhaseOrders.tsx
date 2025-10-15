import React from "react";
import { Divider, List, ListSubheader, Stack } from "@mui/material";
import { OrderRead, service } from "../../store";
import { Panel } from "../../components/Panel";
import { Notice } from "../../components/Notice";
import { IconName } from "../../components/Icon";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";
import { OrderCard } from "../../components/OrderCard";
import { MemberAvatar } from "../../components/MemberAvatar";

export const InactivePhaseOrders: React.FC = () => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  if (!ordersListQuery.data || !gameRetrieveQuery.data)
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

  const phase = gameRetrieveQuery.data.phases.find(p => p.id === selectedPhase);
  const variant = gameRetrieveQuery.data.variant.id;

  const ordersByNation = ordersListQuery.data.reduce(
    (acc, order) => {
      acc[order.nation.name] = [...(acc[order.nation.name] || []), order];
      return acc;
    },
    {} as Record<string, OrderRead[]>
  );

  const hasOrders = Object.values(ordersByNation).some(
    orders => orders.length > 0
  );

  return (
    <Panel>
      <Panel.Content>
        {!hasOrders ? (
          <Stack
            alignItems="center"
            justifyContent="center"
            height="100%"
            sx={{ paddingBottom: "56px" }}
          >
            <Notice
              title="No orders created"
              message="No orders were created by any nation in this phase."
              icon={IconName.NoResults}
            />
          </Stack>
        ) : (
          Object.entries(ordersByNation).map(([nation, orders]) => {
            const unit = phase?.units.find(
              u => u.province.id === orders[0].source.id
            );
            const member = gameRetrieveQuery.data?.members.find(
              m => m.nation === nation
            );
            return (
              <Stack key={nation}>
                <ListSubheader
                  key={nation}
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
                      variant={variant}
                    />
                    {nation}
                  </Stack>
                </ListSubheader>
                <Divider />
                <List disablePadding>
                  {orders.map((order, index) => (
                    <OrderCard
                      province={order.source}
                      unit={unit}
                      order={order}
                      key={`${order.source.id}-${index}`}
                    />
                  ))}
                </List>
              </Stack>
            );
          })
        )}
      </Panel.Content>
    </Panel>
  );
};
