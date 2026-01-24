import React, { Suspense } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import {
  Trash2,
  CheckSquare,
  Square,
  Play,
  Inbox,
  SearchX,
} from "lucide-react";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemActions,
  ItemGroup,
  ItemSeparator,
} from "@/components/ui/item";
import { Notice } from "@/components/Notice";
import { MemberAvatar } from "@/components/MemberAvatar";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PhaseSelect } from "@/components/PhaseSelect";
import { useRequiredParams } from "@/hooks";
import {
  PhaseRetrieve,
  PhaseState,
  Province,
  useGameOrdersDeleteDestroy,
  useGameOrdersListSuspense,
  useGamePhaseRetrieveSuspense,
  useGamePhaseStatesListSuspense,
  useGameConfirmPhasePartialUpdate,
  useGameResolvePhaseCreate,
  useGameRetrieveSuspense,
  useVariantsListSuspense,
  getGameRetrieveQueryKey,
  getGameOrdersListQueryKey,
  Order,
  GameRetrieve,
  Member,
  Unit,
} from "@/api/generated/endpoints";
import { cn } from "../../lib/utils";

type NationGroup = {
  nation: string;
  member: Member;
  items: Array<{
    province: Province;
    order?: Order;
    unit?: Unit;
  }>;
};

const buildNationGroups = (
  isActivePhase: boolean,
  phaseStates: readonly PhaseState[],
  orders: readonly Order[],
  phase: PhaseRetrieve,
  game: GameRetrieve
): NationGroup[] => {
  if (isActivePhase) {
    return phaseStates
      .filter(ps => ps.orderableProvinces.length > 0)
      .map(ps => ({
        nation: ps.member.nation ?? "",
        member: ps.member,
        items: (ps.orderableProvinces as Province[]).map(province => ({
          province,
          order: orders.find(o => o.source.id === province.id),
          unit: phase.units.find(u => u.province.id === province.id),
        })),
      }));
  }

  const ordersByNation = orders.reduce(
    (acc, order) => {
      const nation = order.nation.name;
      acc[nation] = [...(acc[nation] || []), order];
      return acc;
    },
    {} as Record<string, Order[]>
  );

  return Object.entries(ordersByNation).map(([nation, nationOrders]) => ({
    nation,
    member: game.members.find(m => m.nation === nation)!,
    items: nationOrders.map(order => ({
      province: order.source,
      order,
      unit: phase.units.find(u => u.province.id === order.source.id),
    })),
  }));
};

const OrdersScreen: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const selectedPhase = Number(phaseId);

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: phase } = useGamePhaseRetrieveSuspense(gameId, selectedPhase);
  const { data: orders } = useGameOrdersListSuspense(gameId, selectedPhase);
  const { data: variants } = useVariantsListSuspense();
  const { data: phaseStates } = useGamePhaseStatesListSuspense(gameId);

  const deleteOrderMutation = useGameOrdersDeleteDestroy();
  const confirmOrdersMutation = useGameConfirmPhasePartialUpdate();
  const resolvePhaseMutation = useGameResolvePhaseCreate();

  const variant = variants.find(v => v.id === game.variantId)!;

  const isActivePhase = phase.status === "active";

  const handleDeleteOrder = async (sourceId: string) => {
    try {
      await deleteOrderMutation.mutateAsync({ gameId, sourceId });
      queryClient.invalidateQueries({
        queryKey: getGameOrdersListQueryKey(gameId, selectedPhase),
      });
      toast.success("Order deleted");
    } catch {
      toast.error("Failed to delete order");
    }
  };

  const handleConfirmOrders = async () => {
    const newConfirmedState = !game.phaseConfirmed;
    try {
      await confirmOrdersMutation.mutateAsync({
        gameId,
        data: { ordersConfirmed: newConfirmedState },
      });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
      toast.success(
        newConfirmedState ? "Orders confirmed" : "Orders unconfirmed"
      );
    } catch {
      toast.error(
        newConfirmedState
          ? "Failed to confirm orders"
          : "Failed to unconfirm orders"
      );
    }
  };

  const handleResolvePhase = async () => {
    try {
      await resolvePhaseMutation.mutateAsync({ gameId });
      toast.success("Phase resolved");
    } catch {
      toast.error("Failed to resolve phase");
    }
  };

  const handleNavigateToGameInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/game-info`);
  };

  const handleNavigateToPlayerInfo = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/player-info`);
  };

  const nationGroups = buildNationGroups(
    isActivePhase,
    phaseStates,
    orders,
    phase,
    game
  );
  const hasContent = nationGroups.length > 0;

  const emptyState = isActivePhase
    ? {
        icon: Inbox,
        title: "No orders required",
        message: "You do not need to submit any orders during this phase",
      }
    : {
        icon: SearchX,
        title: "No orders created",
        message: "No orders were created by any nation in this phase.",
      };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={
          <div className="flex items-center gap-2">
            <div className="flex-1 flex justify-center">
              <PhaseSelect />
            </div>
            <GameDropdownMenu
              gameId={gameId}
              canLeave={game.canLeave}
              onNavigateToGameInfo={handleNavigateToGameInfo}
              onNavigateToPlayerInfo={handleNavigateToPlayerInfo}
            />
          </div>
        }
        onNavigateBack={() => navigate("/")}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            {!hasContent ? (
              <Notice
                icon={emptyState.icon}
                title={emptyState.title}
                message={emptyState.message}
                className="h-full"
              />
            ) : (
              <Accordion
                type="multiple"
                defaultValue={[
                  nationGroups.find(g => g.member.isCurrentUser)?.nation ?? "",
                ]}
              >
                {nationGroups.map(({ nation, member, items }) => (
                  <AccordionItem key={nation} value={nation}>
                    <AccordionTrigger className="p-0 items-center px-2 py-1">
                      <div className="flex items-center gap-2">
                        <MemberAvatar member={member} variant={variant.id} />
                        {nation}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="p-0">
                      <ItemGroup>
                        {items.map((item, index) => (
                          <React.Fragment key={item.province.id}>
                            {index === 0 && <Separator />}
                            <Item size="sm">
                              <ItemContent>
                                <ItemTitle>
                                  {item.unit?.type} {item.province.name}
                                </ItemTitle>
                                <ItemDescription>
                                  {item.order
                                    ? item.order.summary
                                    : "Order not provided"}
                                </ItemDescription>
                              </ItemContent>
                              {isActivePhase && item.order && (
                                <ItemActions>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() =>
                                      handleDeleteOrder(item.province.id)
                                    }
                                    disabled={deleteOrderMutation.isPending}
                                  >
                                    <Trash2 className="size-4" />
                                  </Button>
                                </ItemActions>
                              )}
                              {!isActivePhase &&
                                item.order &&
                                item.order.resolution?.status && (
                                  <ItemContent
                                    className={cn(
                                      "text-xs",
                                      item.order.resolution.status ===
                                        "Succeeded"
                                        ? "text-green-600"
                                        : "text-red-600"
                                    )}
                                  >
                                    {item.order.resolution.status}
                                  </ItemContent>
                                )}
                            </Item>
                            {index < items.length - 1 && <ItemSeparator />}
                          </React.Fragment>
                        ))}
                      </ItemGroup>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </Panel.Content>

          {isActivePhase && (
            <>
              <Separator />
              <Panel.Footer>
                <div className="flex gap-2 justify-end w-full">
                  {game.sandbox ? (
                    <Button
                      disabled={resolvePhaseMutation.isPending}
                      onClick={handleResolvePhase}
                    >
                      <Play className="size-4" />
                      Resolve phase
                    </Button>
                  ) : (
                    <>
                      {hasContent ? (
                        <Button
                          disabled={confirmOrdersMutation.isPending}
                          onClick={handleConfirmOrders}
                        >
                          {game.phaseConfirmed ? (
                            <CheckSquare className="size-4" />
                          ) : (
                            <Square className="size-4" />
                          )}
                          {game.phaseConfirmed
                            ? "Orders confirmed"
                            : "Confirm orders"}
                        </Button>
                      ) : (
                        <Button disabled>
                          <CheckSquare className="size-4" />
                          Orders confirmed
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </Panel.Footer>
            </>
          )}
        </Panel>
      </div>
    </div>
  );
};

const OrdersScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <OrdersScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { OrdersScreenSuspense as OrdersScreen };
