import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ListItem, ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { austriaPhaseHistory } from "@/data/fixtures";
import type { OrderKind, OrderSlot } from "@/data/types";
import {
  Check,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  Hexagon,
  Merge,
  MoveUpRight,
  Plus,
  RedoDot,
  Square,
  Star,
  Swords,
  Undo2,
  X,
  type LucideIcon,
} from "lucide-react";

const lastIndex = austriaPhaseHistory.length - 1;

const initialIndex = (state: string) => {
  if (state === "first") return 0;
  if (state === "previous") return lastIndex - 1;
  return lastIndex;
};

const PhasePicker: React.FC<{
  selectedId: string;
  name: string;
  titleClassName?: string;
  onSelect: (index: number) => void;
}> = ({ selectedId, name, titleClassName, onSelect }) => {
  const [open, setOpen] = useState(false);
  const phases = [...austriaPhaseHistory].reverse();

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`${name}. Choose phase`}
          className="group flex max-w-full items-center gap-1 rounded-md text-left transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <span
            className={cn(
              "min-w-0 truncate font-semibold leading-tight",
              titleClassName
            )}
          >
            {name}
          </span>
          <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-accent-foreground" />
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-72 p-1">
        <div className="flex max-h-80 flex-col overflow-y-auto">
          {phases.map(phase => {
            const index = austriaPhaseHistory.findIndex(
              entry => entry.id === phase.id
            );
            const viewed = phase.id === selectedId;

            return (
              <button
                key={phase.id}
                type="button"
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left hover:bg-accent hover:text-accent-foreground"
                onClick={() => {
                  onSelect(index);
                  setOpen(false);
                }}
              >
                <span className="min-w-0 flex-1 truncate text-sm font-medium">
                  {phase.orders.phaseName}
                </span>
                {!phase.resolved && (
                  <span className="text-xs font-medium text-muted-foreground">
                    Current
                  </span>
                )}
                {viewed && <Check className="size-4 shrink-0" aria-hidden />}
              </button>
            );
          })}
        </div>
      </PopoverContent>
    </Popover>
  );
};

const HeaderButton: React.FC<{
  label: string;
  disabled: boolean;
  size: "icon" | "icon-sm";
  withTooltip: boolean;
  onClick: () => void;
  icon: LucideIcon;
}> = ({ label, disabled, size, withTooltip, onClick, icon: Icon }) => {
  const button = (
    <Button
      size={size}
      variant="outline"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon />
    </Button>
  );

  if (!withTooltip || disabled) {
    return button;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
};

const HeaderActions: React.FC<{
  size: "icon" | "icon-sm";
  withTooltip: boolean;
  atStart: boolean;
  atEnd: boolean;
  onPrevious: () => void;
  onNext: () => void;
}> = ({ size, withTooltip, atStart, atEnd, onPrevious, onNext }) => {
  return (
    <div className="flex items-center gap-1">
      <HeaderButton
        label="Previous phase"
        disabled={atStart}
        size={size}
        withTooltip={withTooltip}
        onClick={onPrevious}
        icon={ChevronLeft}
      />
      <HeaderButton
        label="Next phase"
        disabled={atEnd}
        size={size}
        withTooltip={withTooltip}
        onClick={onNext}
        icon={ChevronRight}
      />
    </div>
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

const OrderRow: React.FC<{ slot: OrderSlot }> = ({ slot }) => {
  const hasOrder = Boolean(slot.summary);
  const title = slotTitle(slot);

  return (
    <ListItem
      leading={<OrderMedia slot={slot} />}
      title={title}
      subtitle={slot.summary ?? "No order"}
      muted={!hasOrder}
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

const PhaseStepper: React.FC<{ state: string }> = ({ state }) => {
  const [index, setIndex] = useState(() => initialIndex(state));
  const [confirmed, setConfirmed] = useState(
    austriaPhaseHistory[initialIndex(state)].orders.confirmed
  );

  useEffect(() => {
    const nextIndex = initialIndex(state);
    setIndex(nextIndex);
    setConfirmed(austriaPhaseHistory[nextIndex].orders.confirmed);
  }, [state]);

  const goTo = (next: number) => {
    setIndex(next);
    setConfirmed(austriaPhaseHistory[next].orders.confirmed);
  };

  const entry = austriaPhaseHistory[index];
  const orders = entry.orders;
  const atStart = index === 0;
  const atEnd = index === lastIndex;
  const submitted = orders.slots.filter(slot => slot.summary).length;
  const total = orders.slots.length;
  const progress = `${submitted}/${total}`;
  const picker = (
    <PhasePicker
      selectedId={entry.id}
      name={orders.phaseName}
      onSelect={goTo}
    />
  );

  return (
    <GameDetailShell
      title={picker}
      subtitle={orders.timeRemaining}
      activeNavItem="Orders"
      ordersAttention={!entry.resolved && !confirmed && total > 0}
      headerAction={
        <HeaderActions
          size="icon-sm"
          withTooltip={false}
          atStart={atStart}
          atEnd={atEnd}
          onPrevious={() => goTo(index - 1)}
          onNext={() => goTo(index + 1)}
        />
      }
    >
      <ScreenContainer>
        <div className="hidden items-start justify-between gap-2 md:flex">
          <div className="min-w-0 flex-1">
            <PhasePicker
              selectedId={entry.id}
              name={orders.phaseName}
              titleClassName="text-xl leading-9"
              onSelect={goTo}
            />
            <p className="text-sm text-muted-foreground">
              {orders.timeRemaining}
            </p>
          </div>
          <HeaderActions
            size="icon"
            withTooltip
            atStart={atStart}
            atEnd={atEnd}
            onPrevious={() => goTo(index - 1)}
            onNext={() => goTo(index + 1)}
          />
        </div>

        {total === 0 ? (
          <section className="flex flex-col gap-2">
            <NationHeading
              nation={orders.nation}
              supplyCenterCount={orders.supplyCenterCount}
              unitCount={orders.unitCount}
            />
            <div className="px-1 py-6">
              <p className="font-semibold leading-tight">No orders required</p>
              <p className="mt-1 text-sm text-muted-foreground">
                You do not need to submit any orders during this phase.
              </p>
            </div>
          </section>
        ) : (
          <ListSection
            header={
              <NationHeading
                nation={orders.nation}
                supplyCenterCount={orders.supplyCenterCount}
                unitCount={orders.unitCount}
              />
            }
          >
            {orders.slots.map(slot => (
              <OrderRow key={slot.id} slot={slot} />
            ))}
          </ListSection>
        )}

        {!entry.resolved && total > 0 && (
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
        )}
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { PhaseStepper };
