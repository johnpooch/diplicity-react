import { useEffect, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { ListItem, ListSection } from "@/components/ui/list";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import {
  austriaAdjustment,
  austriaMovementConfirmed,
  austriaMovementIncomplete,
  austriaRetreat,
  austriaSandbox,
  austriaTwelveUnits,
} from "@/data/fixtures";
import type { CurrentPhaseOrders, OrderKind, OrderSlot } from "@/data/types";
import {
  CheckSquare,
  CircleDashed,
  Eye,
  Hexagon,
  History,
  Inbox,
  Merge,
  MoveUpRight,
  Play,
  Plus,
  RedoDot,
  Square,
  Star,
  Swords,
  Trash2,
  Undo2,
  UserX,
  X,
  type LucideIcon,
} from "lucide-react";

type ScreenKind = "orders" | "no-orders" | "civil-disorder" | "spectator";

interface ScreenConfig {
  kind: ScreenKind;
  orders?: CurrentPhaseOrders;
}

const screens: Record<string, ScreenConfig> = {
  incomplete: { kind: "orders", orders: austriaMovementIncomplete },
  confirmed: { kind: "orders", orders: austriaMovementConfirmed },
  "no-orders": { kind: "no-orders", orders: austriaMovementIncomplete },
  "civil-disorder": {
    kind: "civil-disorder",
    orders: austriaMovementIncomplete,
  },
  spectator: { kind: "spectator", orders: austriaMovementIncomplete },
  sandbox: { kind: "orders", orders: austriaSandbox },
  twelve: { kind: "orders", orders: austriaTwelveUnits },
  retreat: { kind: "orders", orders: austriaRetreat },
  adjustment: { kind: "orders", orders: austriaAdjustment },
};

const HeaderActions: React.FC<{
  size: "icon" | "icon-sm";
  withTooltip: boolean;
}> = ({ size, withTooltip }) => {
  const button = (
    <Button size={size} variant="outline" aria-label="Select previous phase">
      <History />
    </Button>
  );

  if (!withTooltip) {
    return button;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent>Select previous phase</TooltipContent>
    </Tooltip>
  );
};

const orderIcons: Record<OrderKind, LucideIcon> = {
  move: MoveUpRight,
  hold: Hexagon,
  support: Merge,
  convoy: RedoDot,
  retreat: Undo2,
  disband: X,
  build: Plus,
};

const slotTitle = (slot: OrderSlot) =>
  slot.unitType ? `${slot.unitType} ${slot.province}` : slot.province;

const OrderMedia: React.FC<{ slot: OrderSlot }> = ({ slot }) => {
  const Icon = slot.kind ? orderIcons[slot.kind] : CircleDashed;

  return (
    <div className="flex size-8 shrink-0 items-center justify-center">
      <Icon
        className={cn("size-6", !slot.kind && "text-muted-foreground")}
        aria-hidden
      />
    </div>
  );
};

const OrderRow: React.FC<{
  slot: OrderSlot;
  canDelete: boolean;
  onDelete?: () => void;
}> = ({ slot, canDelete, onDelete }) => {
  const hasOrder = Boolean(slot.summary);
  const title = slotTitle(slot);

  return (
    <ListItem
      leading={<OrderMedia slot={slot} />}
      title={title}
      subtitle={slot.summary ?? "No order"}
      muted={!hasOrder}
      trailingAction={
        canDelete && hasOrder ? (
          <Button
            variant="ghost"
            size="icon"
            className="size-11"
            aria-label={`Delete order for ${title}`}
            onClick={onDelete}
          >
            <Trash2 />
          </Button>
        ) : undefined
      }
    />
  );
};

const NationHeading: React.FC<{
  nation: string;
  supplyCenterCount: number;
  unitCount: number;
}> = ({ nation, supplyCenterCount, unitCount }) => {
  return (
    <h2 className="flex items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
      <span className="flex min-w-0 items-center gap-2">
        <NationFlag nation={nation} size="sm" />
        {nation}
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
      </span>
    </h2>
  );
};

const ConfirmButton: React.FC<{
  label: string;
  icon: LucideIcon;
  confirmed: boolean;
  onClick: () => void;
}> = ({ label, icon: Icon, confirmed, onClick }) => {
  return (
    <Button
      className="w-full"
      size="lg"
      variant={confirmed ? "outline" : "default"}
      onClick={onClick}
    >
      <Icon />
      {label}
    </Button>
  );
};

const EmptyNotice: React.FC<{
  icon: LucideIcon;
  title: string;
  message: string;
  action?: ReactNode;
}> = ({ icon: Icon, title, message, action }) => {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icon className="opacity-60" />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{message}</EmptyDescription>
      </EmptyHeader>
      {action && <EmptyContent>{action}</EmptyContent>}
    </Empty>
  );
};

const BareGlyphs: React.FC<{ state: string }> = ({ state }) => {
  const screen = screens[state] ?? screens.incomplete;
  const orders = screen.orders ?? austriaMovementIncomplete;
  const [cleared, setCleared] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(orders.confirmed);
  const [recovered, setRecovered] = useState(false);

  useEffect(() => {
    setCleared([]);
    setConfirmed(orders.confirmed);
    setRecovered(false);
  }, [state, orders.confirmed]);

  const kind =
    screen.kind === "civil-disorder" && recovered ? "orders" : screen.kind;
  const canModify = kind === "orders";

  const slots = orders.slots.map(slot =>
    cleared.includes(slot.id)
      ? { ...slot, summary: undefined, kind: undefined }
      : slot
  );
  const submitted = slots.filter(slot => slot.summary).length;
  const total = slots.length;
  const progress = `${submitted}/${total}`;

  const ordersAttention =
    kind === "orders" &&
    (orders.sandbox ? submitted < total : !confirmed);

  const footerAction = (() => {
    if (kind !== "orders" || total === 0) return undefined;
    if (orders.sandbox) {
      return { label: "Resolve phase", icon: Play };
    }
    if (confirmed) {
      return { label: `Orders confirmed (${progress})`, icon: CheckSquare };
    }
    return { label: `Confirm orders (${progress})`, icon: Square };
  })();

  return (
    <GameDetailShell
      title={orders.phaseName}
      subtitle={orders.timeRemaining}
      activeNavItem="Orders"
      ordersAttention={ordersAttention}
      headerAction={<HeaderActions size="icon-sm" withTooltip={false} />}
    >
      <ScreenContainer>
        <div className="hidden items-start justify-between gap-2 md:flex">
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold leading-9">
              {orders.phaseName}
            </h1>
            <p className="text-sm text-muted-foreground">
              {orders.timeRemaining}
            </p>
          </div>
          <HeaderActions size="icon" withTooltip />
        </div>

        {kind === "civil-disorder" && (
          <EmptyNotice
            icon={UserX}
            title="Civil Disorder"
            message="Your nation is in civil disorder. Your units hold each turn and you cannot submit orders."
            action={
              <Button size="lg" onClick={() => setRecovered(true)}>
                I'm back
              </Button>
            }
          />
        )}

        {kind === "spectator" && (
          <EmptyNotice
            icon={Eye}
            title="Spectating"
            message="You are not playing in this game. Orders become visible once the phase resolves."
          />
        )}

        {kind === "no-orders" && (
          <EmptyNotice
            icon={Inbox}
            title="No orders required"
            message="You do not need to submit any orders during this phase."
          />
        )}

        {kind === "orders" && (
          <ListSection
            header={
              <NationHeading
                nation={orders.nation}
                supplyCenterCount={orders.supplyCenterCount}
                unitCount={orders.unitCount}
              />
            }
          >
            {slots.map(slot => (
              <OrderRow
                key={slot.id}
                slot={slot}
                canDelete={canModify}
                onDelete={() => {
                  setCleared(current => [...current, slot.id]);
                  setConfirmed(false);
                }}
              />
            ))}
          </ListSection>
        )}

        {footerAction && (
          <ConfirmButton
            label={footerAction.label}
            icon={footerAction.icon}
            confirmed={confirmed && !orders.sandbox}
            onClick={() => {
              if (!orders.sandbox) {
                setConfirmed(current => !current);
              }
            }}
          />
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { BareGlyphs };
