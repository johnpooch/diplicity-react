import { Button } from "@/components/ui/button";
import { ScreenContainer } from "@/components/ui/screen-container";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import {
  austriaNoAdjustments,
  austriaNoMovement,
  austriaNoRetreats,
} from "@/data/fixtures";
import type { CurrentPhaseOrders } from "@/data/types";
import { History, Star, Swords } from "lucide-react";

interface ScreenConfig {
  orders: CurrentPhaseOrders;
  title: string;
  message: string;
}

const screens: Record<string, ScreenConfig> = {
  retreat: {
    orders: austriaNoRetreats,
    title: "No retreats required",
    message: "None of your units were dislodged.",
  },
  adjustment: {
    orders: austriaNoAdjustments,
    title: "No adjustments needed",
    message: "Your supply centers and units are even.",
  },
  movement: {
    orders: austriaNoMovement,
    title: "No orders required",
    message: "You do not need to submit any orders during this phase.",
  },
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

const NoOrdersRequired: React.FC<{ state: string }> = ({ state }) => {
  const screen = screens[state] ?? screens.retreat;
  const orders = screen.orders;

  return (
    <GameDetailShell
      title={orders.phaseName}
      subtitle={orders.timeRemaining}
      activeNavItem="Orders"
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
          <div className="px-1 py-6">
            <p className="font-semibold leading-tight">{screen.title}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {screen.message}
            </p>
          </div>
        </section>
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { NoOrdersRequired };
