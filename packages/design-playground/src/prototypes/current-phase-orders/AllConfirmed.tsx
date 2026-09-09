import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
  austriaAdjustmentConfirmed,
  austriaMovementConfirmed,
  austriaRetreatConfirmed,
} from "@/data/fixtures";
import type { CurrentPhaseOrders, OrderKind, OrderSlot } from "@/data/types";
import {
  CheckSquare,
  Hexagon,
  History,
  Merge,
  MoveUpRight,
  Plus,
  RedoDot,
  Square,
  Star,
  Swords,
  Trash2,
  Undo2,
  X,
  type LucideIcon,
} from "lucide-react";

const screens: Record<string, CurrentPhaseOrders> = {
  movement: austriaMovementConfirmed,
  retreat: austriaRetreatConfirmed,
  adjustment: austriaAdjustmentConfirmed,
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
  const Icon = slot.kind ? orderIcons[slot.kind] : undefined;

  return (
    <div
      className={cn(
        "flex size-12 shrink-0 items-center justify-center rounded-full border",
        !Icon && "border-dashed"
      )}
    >
      {Icon && <Icon className="size-5" aria-hidden />}
    </div>
  );
};

const OrderCard: React.FC<{
  slot: OrderSlot;
  onDelete: () => void;
}> = ({ slot, onDelete }) => {
  const hasOrder = Boolean(slot.summary);

  return (
    <Card
      className={cn("overflow-hidden py-0", !hasOrder && "border-dashed")}
    >
      <CardContent className="flex items-center gap-3 p-3">
        <OrderMedia slot={slot} />
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <p className="truncate font-semibold leading-tight">
            {slotTitle(slot)}
          </p>
          <p className="truncate text-sm text-muted-foreground">
            {slot.summary ?? "No order"}
          </p>
        </div>
        {hasOrder && (
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Delete order for ${slot.province}`}
            onClick={onDelete}
          >
            <Trash2 />
          </Button>
        )}
      </CardContent>
    </Card>
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
        <span className="size-5 overflow-hidden rounded-full" aria-hidden>
          <NationFlag nation={nation} />
        </span>
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

const AllConfirmed: React.FC<{ state: string }> = ({ state }) => {
  const orders = screens[state] ?? screens.movement;
  const [cleared, setCleared] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(true);

  useEffect(() => {
    setCleared([]);
    setConfirmed(true);
  }, [state]);

  const slots = orders.slots.map(slot =>
    cleared.includes(slot.id)
      ? { ...slot, summary: undefined, kind: undefined }
      : slot
  );
  const submitted = slots.filter(slot => slot.summary).length;
  const total = slots.length;
  const progress = `${submitted}/${total}`;

  return (
    <GameDetailShell
      title={orders.phaseName}
      subtitle={orders.timeRemaining}
      activeNavItem="Orders"
      ordersAttention={!confirmed}
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
        <section className="flex flex-col gap-2">
          <NationHeading
            nation={orders.nation}
            supplyCenterCount={orders.supplyCenterCount}
            unitCount={orders.unitCount}
          />
          {slots.map(slot => (
            <OrderCard
              key={slot.id}
              slot={slot}
              onDelete={() => {
                setCleared(current => [...current, slot.id]);
                setConfirmed(false);
              }}
            />
          ))}
        </section>
        <Button
          className="w-full"
          size="lg"
          variant={confirmed ? "outline" : "default"}
          onClick={() => setConfirmed(current => !current)}
        >
          {confirmed ? <CheckSquare /> : <Square />}
          {confirmed
            ? `Orders confirmed (${progress})`
            : `Confirm orders (${progress})`}
        </Button>
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { AllConfirmed };
