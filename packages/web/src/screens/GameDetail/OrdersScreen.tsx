import React, { Suspense, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import {
  Trash2,
  CheckSquare,
  Square,
  Play,
  SearchX,
  Star,
  Swords,
  UserX,
  Handshake,
  Eye,
  ChevronDown,
  Hexagon,
  Merge,
  MoveUpRight,
  Plus,
  RedoDot,
  X,
  type LucideIcon,
} from "lucide-react";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ListItem, ListSection } from "@/components/ui/list";
import { Notice } from "@/components/Notice";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { NationBadge } from "@/components/NationBadge";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PhaseStepperTitle, PhaseStepperActions } from "@/components/PhaseStepper";
import { useRequiredParams } from "@/hooks";
import {
  PhaseRetrieve,
  PhaseState,
  Province,
  Variant,
  useGameOrdersDeleteDestroy,
  useGameOrdersListSuspense,
  useGamePhaseRetrieveSuspense,
  useGamePhaseStatesListSuspense,
  useGameConfirmPhasePartialUpdate,
  useGameResolvePhaseCreate,
  useGameRetrieveSuspense,
  useGamesDrawProposalsListSuspense,
  useGameRecoverFromCivilDisorderCreate,
  getGameRetrieveQueryKey,
  getGameOrdersListQueryKey,
  getGamePhaseStatesListQueryKey,
  getGameOptionsRetrieveQueryKey,
  Order,
  OrderTypeEnum,
  Member,
  Unit,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { cn } from "@/lib/utils";

type NationGroup = {
  nation: string;
  member: { isCurrentUser: boolean };
  items: Array<{
    province: Province;
    order?: Order;
    unit?: Unit;
  }>;
};

// A fleet on a named coast (e.g. "spa/nc") sits on the coast province, but the
// order source / orderable province is always the parent ("spa"). Match on
// either so the unit (and its type + coast name) is found.
const findUnitForProvince = (
  units: readonly Unit[],
  provinceId: string
): Unit | undefined => {
  const matches = (u: Unit) =>
    u.province.id === provinceId || u.province.parentId === provinceId;
  return units.find(u => matches(u) && u.dislodged) ?? units.find(matches);
};

// Mirror of findUnitForProvince, in reverse: a fleet on a named coast has
// order.source pointing at the parent province, not the coast itself.
const findOrderForUnit = (
  orders: readonly Order[],
  unit: Unit
): Order | undefined =>
  orders.find(
    o => o.source.id === unit.province.id || o.source.id === unit.province.parentId
  );

const buildNationGroups = (
  isActivePhase: boolean,
  phaseStates: readonly PhaseState[],
  orders: readonly Order[],
  phase: PhaseRetrieve,
  members: readonly Member[]
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
          unit: findUnitForProvince(phase.units, province.id),
        })),
      }));
  }

  // A historical phase's units are its starting units, before that phase's
  // orders resolved — one row per unit, whether or not it received an order,
  // plus any order with no matching starting unit (a build, which creates a
  // unit that didn't exist yet at phase start).
  const nations = new Set([
    ...phase.units.map(u => u.nation.name),
    ...orders.map(o => o.nation.name),
  ]);

  return Array.from(nations).map(nation => {
    const member = members.find(m => m.nation === nation);
    if (!member && import.meta.env.DEV) {
      console.warn(`buildNationGroups: no member found for nation "${nation}"`);
    }

    const nationOrders = orders.filter(o => o.nation.name === nation);
    const unitItems = phase.units
      .filter(u => u.nation.name === nation)
      .map(unit => ({
        province: unit.province,
        order: findOrderForUnit(nationOrders, unit),
        unit,
      }));
    const orderedSourceIds = new Set(
      unitItems
        .map(item => item.order?.source.id)
        .filter((id): id is string => id !== undefined)
    );
    const buildItems = nationOrders
      .filter(order => !orderedSourceIds.has(order.source.id))
      .map(order => ({
        province: order.source,
        order,
        unit: findUnitForProvince(phase.units, order.source.id),
      }));

    return {
      nation,
      member: member ?? { isCurrentUser: false },
      items: [...unitItems, ...buildItems],
    };
  });
};

const orderIcons: Partial<Record<OrderTypeEnum, LucideIcon>> = {
  Move: MoveUpRight,
  MoveViaConvoy: MoveUpRight,
  Hold: Hexagon,
  Support: Merge,
  Convoy: RedoDot,
  Build: Plus,
  Disband: X,
};

const OrderMedia: React.FC<{ order?: Order; isActivePhase: boolean }> = ({
  order,
  isActivePhase,
}) => {
  const Icon = order ? orderIcons[order.orderType] : undefined;
  const isMissing = !order && isActivePhase;

  return (
    <div
      className={cn(
        "flex size-12 shrink-0 items-center justify-center rounded-full border",
        !Icon && !isMissing && "border-dashed",
        isMissing && "border-destructive/70"
      )}
    >
      {Icon && <Icon className="size-5" aria-hidden />}
      {isMissing && <X className="size-5 text-destructive/70" aria-hidden />}
    </div>
  );
};

const OrderRow: React.FC<{
  item: NationGroup["items"][number];
  isActivePhase: boolean;
  canDelete: boolean;
  onDelete: () => void;
}> = ({ item, isActivePhase, canDelete, onDelete }) => {
  const title = `${item.unit?.type ?? ""} ${item.unit?.province.name ?? item.province.name}`.trim();
  const resolutionStatus = !isActivePhase ? item.order?.resolution?.status : undefined;

  return (
    <ListItem
      leading={<OrderMedia order={item.order} isActivePhase={isActivePhase} />}
      title={title}
      subtitle={item.order ? item.order.summary : "Order not provided"}
      muted={!item.order}
      trailing={
        resolutionStatus && (
          <span
            className={cn(
              "text-xs",
              resolutionStatus === "Succeeded" ? "text-green-600" : "text-red-600"
            )}
          >
            {resolutionStatus}
          </span>
        )
      }
      trailingAction={
        canDelete && item.order ? (
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Delete order for ${title}`}
            onClick={onDelete}
          >
            <Trash2 className="size-4" />
          </Button>
        ) : undefined
      }
    />
  );
};

const NationHeading: React.FC<{
  nation: string;
  flagUrl: string | null;
  nationColor: string | null;
  variantNations: Variant["nations"];
  isCurrentUser: boolean;
  supplyCenterCount: number;
  unitCount: number;
  collapsible: boolean;
  open: boolean;
  onToggle: () => void;
}> = ({
  nation,
  flagUrl,
  nationColor,
  variantNations,
  isCurrentUser,
  supplyCenterCount,
  unitCount,
  collapsible,
  open,
  onToggle,
}) => {
  const content = (
    <>
      <span className="flex min-w-0 items-center gap-2">
        <NationFlag flagUrl={flagUrl} alt={nation} size="sm" color={nationColor} />
        <span className="truncate">{nation}</span>
        {isCurrentUser && (
          <NationBadge nations={variantNations} nation={nation}>
            you
          </NationBadge>
        )}
      </span>
      <span className="flex shrink-0 items-center gap-2.5">
        <span className="flex items-center gap-1">
          <Star className="size-3.5" />
          {supplyCenterCount}
        </span>
        <span className="flex items-center gap-1">
          <Swords className="size-3.5" />
          {unitCount}
        </span>
        {collapsible && (
          <ChevronDown
            className={cn("size-4 transition-transform", open && "rotate-180")}
            aria-hidden
          />
        )}
      </span>
    </>
  );

  if (!collapsible) {
    return (
      <h2 className="flex items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
        {content}
      </h2>
    );
  }

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      className="flex w-full items-center justify-between gap-3 text-sm font-medium text-muted-foreground"
    >
      {content}
    </button>
  );
};

const NationOrdersSections: React.FC<{
  nationGroups: NationGroup[];
  variant: Variant;
  isActivePhase: boolean;
  canModifyOrders: boolean;
  onDeleteOrder: (sourceId: string) => void;
  getSupplyCenterCount: (nation: string) => number;
  getUnitCount: (nation: string) => number;
}> = ({
  nationGroups,
  variant,
  isActivePhase,
  canModifyOrders,
  onDeleteOrder,
  getSupplyCenterCount,
  getUnitCount,
}) => {
  const collapsible = nationGroups.length > 1;
  const orderedGroups = [...nationGroups].sort((a, b) =>
    Number(b.member.isCurrentUser) - Number(a.member.isCurrentUser)
  );
  const [openNations, setOpenNations] = useState<string[]>(() =>
    nationGroups.filter(g => g.member.isCurrentUser).map(g => g.nation)
  );

  const toggleNation = (nation: string) => {
    setOpenNations(current =>
      current.includes(nation)
        ? current.filter(n => n !== nation)
        : [...current, nation]
    );
  };

  return (
    <div className="flex flex-col gap-4">
      {orderedGroups.map(({ nation, member, items }) => {
        const open = !collapsible || openNations.includes(nation);
        return (
          <div key={nation} className="flex flex-col gap-2">
            <NationHeading
              nation={nation}
              flagUrl={findNationFlagUrl(variant.nations, nation)}
              nationColor={findNationColor(variant.nations, nation)}
              variantNations={variant.nations}
              isCurrentUser={collapsible && member.isCurrentUser}
              supplyCenterCount={getSupplyCenterCount(nation)}
              unitCount={getUnitCount(nation)}
              collapsible={collapsible}
              open={open}
              onToggle={() => toggleNation(nation)}
            />
            {open && (
              <ListSection>
                {items.map(item => (
                  <OrderRow
                    key={item.province.id}
                    item={item}
                    isActivePhase={isActivePhase}
                    canDelete={canModifyOrders}
                    onDelete={() => onDeleteOrder(item.province.id)}
                  />
                ))}
              </ListSection>
            )}
          </div>
        );
      })}
    </div>
  );
};

const DrawProposalsBadge: React.FC<{ gameId: string; currentMemberId?: number }> = ({
  gameId,
  currentMemberId,
}) => {
  const { data: proposals } = useGamesDrawProposalsListSuspense(gameId);
  if (currentMemberId === undefined) return null;
  const count = proposals.filter(
    p => p.status === "pending" && p.myVote !== null && p.myVote.accepted === null
  ).length;
  if (count === 0) return null;
  return (
    <Badge
      variant="destructive"
      className="absolute -top-1 -right-1 h-4 w-4 p-0 justify-center text-[10px]"
    >
      {count}
    </Badge>
  );
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
  const variant = useGameVariant(game);
  const { data: phaseStates } = useGamePhaseStatesListSuspense(gameId);

  const deleteOrderMutation = useGameOrdersDeleteDestroy();
  const confirmOrdersMutation = useGameConfirmPhasePartialUpdate();
  const resolvePhaseMutation = useGameResolvePhaseCreate();
  const recoverMutation = useGameRecoverFromCivilDisorderCreate();

  if (!variant) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground"></div>
      </div>
    );
  }

  const isActivePhase = phase.status === "active";
  const isGameFinished =
    game.status === "completed" || game.status === "abandoned";
  const members = Array.isArray(game.members) ? game.members : [];
  const safeOrders = Array.isArray(orders) ? orders : [];
  const safePhaseStates = Array.isArray(phaseStates) ? phaseStates : [];
  const currentMember = members.find(m => m.isCurrentUser);
  const isSpectator = !currentMember;
  const isCurrentMemberInCivilDisorder = currentMember?.civilDisorder ?? false;
  const canModifyOrders =
    !isSpectator &&
    isActivePhase &&
    !isGameFinished &&
    !isCurrentMemberInCivilDisorder;

  const getSupplyCenterCount = (nation: string) => {
    return phase.supplyCenters.filter(sc => sc.nation.name === nation).length;
  };

  const getUnitCount = (nation: string) => {
    return phase.units.filter(u => u.nation.name === nation).length;
  };

  const handleDeleteOrder = async (sourceId: string) => {
    try {
      await deleteOrderMutation.mutateAsync({ gameId, sourceId });
      queryClient.invalidateQueries({
        queryKey: getGameOrdersListQueryKey(gameId, selectedPhase),
      });
      queryClient.invalidateQueries({
        queryKey: getGamePhaseStatesListQueryKey(gameId),
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
      const result = await resolvePhaseMutation.mutateAsync({ gameId });
      queryClient.invalidateQueries({
        queryKey: getGameOptionsRetrieveQueryKey(gameId),
      });
      toast.success("Phase resolved");
      navigate(`/game/${gameId}/phase/${result.id}/orders`);
    } catch {
      toast.error("Failed to resolve phase");
    }
  };

  const handleRecoverFromCivilDisorder = async () => {
    try {
      await recoverMutation.mutateAsync({ gameId });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
      toast.success("Welcome back!");
    } catch {
      toast.error("Failed to recover from civil disorder");
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
    safePhaseStates,
    safeOrders,
    phase,
    members
  );
  const hasContent = nationGroups.length > 0;

  const isStartedGame =
    game.status === "active" ||
    game.status === "completed" ||
    game.status === "abandoned";
  const showDrawProposalsButton = !game.sandbox && isStartedGame;

  const handleNavigateToDrawProposals = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/draw-proposals`);
  };

  const rightFooterButton = (() => {
    if (!canModifyOrders) return null;
    if (game.sandbox)
      return (
        <Button disabled={resolvePhaseMutation.isPending} onClick={handleResolvePhase}>
          <Play className="size-4" />
          Resolve phase
        </Button>
      );
    if (hasContent)
      return (
        <Button disabled={confirmOrdersMutation.isPending} onClick={handleConfirmOrders}>
          {game.phaseConfirmed ? (
            <CheckSquare className="size-4" />
          ) : (
            <Square className="size-4" />
          )}
          {game.phaseConfirmed ? "Orders confirmed" : "Confirm orders"}
        </Button>
      );
    return (
      <Button disabled>
        <CheckSquare className="size-4" />
        Orders confirmed
      </Button>
    );
  })();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={<PhaseStepperTitle />}
        rightButton={
          <div className="flex items-center gap-1">
            <PhaseStepperActions />
            <GameDropdownMenu
              game={game}
              onNavigateToGameInfo={handleNavigateToGameInfo}
              onNavigateToPlayerInfo={handleNavigateToPlayerInfo}
            />
          </div>
        }
        onNavigateBack={() => navigate("/")}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            {isCurrentMemberInCivilDisorder ? (
              <Notice
                icon={UserX}
                title="Civil Disorder"
                message="Your nation is in civil disorder. Your units hold each turn and you cannot submit orders."
                className="h-full"
                actions={
                  <Button
                    onClick={handleRecoverFromCivilDisorder}
                    disabled={recoverMutation.isPending}
                  >
                    I'm back
                  </Button>
                }
              />
            ) : !hasContent && !isActivePhase ? (
              <Notice
                icon={SearchX}
                title="No orders created"
                message="No orders were created by any nation in this phase."
                className="h-full"
              />
            ) : !hasContent && isSpectator ? (
              <Notice
                icon={Eye}
                title="Spectating"
                message="You are not playing in this game. Orders become visible once the phase resolves."
                className="h-full"
              />
            ) : !hasContent ? (
              <section className="flex flex-col gap-2">
                <NationHeading
                  nation={currentMember?.nation ?? ""}
                  flagUrl={findNationFlagUrl(variant.nations, currentMember?.nation)}
                  nationColor={findNationColor(variant.nations, currentMember?.nation)}
                  variantNations={variant.nations}
                  isCurrentUser={false}
                  supplyCenterCount={getSupplyCenterCount(currentMember?.nation ?? "")}
                  unitCount={getUnitCount(currentMember?.nation ?? "")}
                  collapsible={false}
                  open
                  onToggle={() => {}}
                />
                <div className="px-1 py-6">
                  <p className="font-semibold leading-tight">No orders required</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    You do not need to submit any orders during this phase.
                  </p>
                </div>
              </section>
            ) : (
              <NationOrdersSections
                key={phaseId}
                nationGroups={nationGroups}
                variant={variant}
                isActivePhase={isActivePhase}
                canModifyOrders={canModifyOrders}
                onDeleteOrder={handleDeleteOrder}
                getSupplyCenterCount={getSupplyCenterCount}
                getUnitCount={getUnitCount}
              />
            )}
          </Panel.Content>

          {!isCurrentMemberInCivilDisorder && (rightFooterButton || showDrawProposalsButton) && (
            <Panel.Footer divider>
              <div className="flex w-full items-center">
                <div className="flex-1">
                  {showDrawProposalsButton && (
                    <Button
                      variant="outline"
                      onClick={handleNavigateToDrawProposals}
                      className="relative"
                    >
                      <Handshake className="size-4" />
                      Draw proposals
                      <Suspense fallback={null}>
                        <DrawProposalsBadge
                          gameId={gameId}
                          currentMemberId={currentMember?.id}
                        />
                      </Suspense>
                    </Button>
                  )}
                </div>
                {rightFooterButton}
              </div>
            </Panel.Footer>
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
