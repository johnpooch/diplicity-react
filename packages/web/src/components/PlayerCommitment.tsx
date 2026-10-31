import React, { useState } from "react";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type {
  CommitmentBreakdown,
  CommitmentSquare,
  ShadeEnum,
} from "@/api/generated/endpoints";
import { cn } from "@/lib/utils";

const gridSlots = 48;

const formatPoints = (points: number) => {
  if (points > 0) return `+${points}`;
  if (points < 0) return `−${Math.abs(points)}`;
  return "0";
};

const shadeTone: Record<ShadeEnum, string> = {
  dark_red: "bg-red-600 dark:bg-red-500",
  red: "bg-red-400 dark:bg-red-700",
  light_red: "bg-red-200 dark:bg-red-900",
  grey: "bg-muted border border-border",
  light_green: "bg-emerald-200 dark:bg-emerald-900",
  green: "bg-emerald-400 dark:bg-emerald-700",
  dark_green: "bg-emerald-600 dark:bg-emerald-500",
};

const breakdownLabel = ({ kind, count }: CommitmentBreakdown) => {
  switch (kind) {
    case "muster_no_show":
      return "Didn't confirm during mustering";
    case "submitted":
      return `Submitted ${count} ${count === 1 ? "phase" : "phases"}`;
    case "nmr":
      return `Missed orders ×${count}`;
    case "civil_disorder":
      return "Abandoned game";
    case "early_withdrawal":
      return "Withdrew early";
    case "late_withdrawal":
      return "Withdrew late";
  }
};

const squareRows = (square: CommitmentSquare) =>
  square.anonymous
    ? [{ label: "Anonymous game", points: square.points }]
    : square.breakdown.map(row => ({
        label: breakdownLabel(row),
        points: row.points,
      }));

const squareLabel = (square: CommitmentSquare) => {
  if (square.anonymous) {
    return `Anonymous game: ${formatPoints(square.points)}`;
  }
  const effect = squareRows(square)
    .map(row => `${row.label} ${formatPoints(row.points)}`)
    .join(", ");
  return `${square.gameName}: ${effect || formatPoints(square.points)}`;
};

const missedOrders = (squares: readonly CommitmentSquare[]) => {
  const submitted = squares.reduce((sum, square) => sum + square.submitted, 0);
  const missed = squares.reduce((sum, square) => sum + square.missed, 0);
  const phases = submitted + missed;
  return phases === 0 ? "—" : `${Math.round((missed / phases) * 100)}%`;
};

const abandonedGames = (squares: readonly CommitmentSquare[]) =>
  squares.filter(square =>
    square.breakdown.some(row => row.kind === "civil_disorder")
  ).length;

interface SquareBreakdownProps {
  square: CommitmentSquare;
}

const SquareBreakdown: React.FC<SquareBreakdownProps> = ({ square }) => {
  const rows = squareRows(square);

  if (rows.length === 0) return <span>No phases played yet</span>;

  return (
    <table className="text-xs tabular-nums">
      <tbody>
        {rows.map(row => (
          <tr key={row.label}>
            <td className="pr-4">{row.label}</td>
            <td className="text-right">{formatPoints(row.points)}</td>
          </tr>
        ))}
        {rows.length > 1 && (
          <tr className="border-t border-background/30 font-semibold">
            <td className="pt-1 pr-4">Total</td>
            <td className="pt-1 text-right">{formatPoints(square.points)}</td>
          </tr>
        )}
      </tbody>
    </table>
  );
};

interface CommitmentRowProps {
  label: string;
  children: React.ReactNode;
}

const CommitmentRow: React.FC<CommitmentRowProps> = ({ label, children }) => (
  <div className="flex items-center justify-between gap-4 px-6 py-3">
    <span>{label}</span>
    {children}
  </div>
);

interface PlayerCommitmentProps {
  total: number;
  squares: readonly CommitmentSquare[];
}

export const PlayerCommitment: React.FC<PlayerCommitmentProps> = ({
  total,
  squares,
}) => {
  const [openIndex, setOpenIndex] = useState<number>();
  const offset = Math.max(0, squares.length - gridSlots);
  const recent = squares.slice(offset);

  return (
    <div className="flex flex-col divide-y md:flex-row md:divide-x md:divide-y-0">
      <div className="flex flex-1 flex-col divide-y text-sm">
        <CommitmentRow label="Commitment">
          <span
            className={cn(
              "font-semibold tabular-nums",
              total > 0 && "text-emerald-700 dark:text-emerald-400",
              total < 0 && "text-red-700 dark:text-red-400"
            )}
          >
            {formatPoints(total)}
          </span>
        </CommitmentRow>
        <CommitmentRow label="Missed orders">
          <span className="tabular-nums text-muted-foreground">
            {missedOrders(squares)}
          </span>
        </CommitmentRow>
        <CommitmentRow label="Abandoned games">
          <span className="tabular-nums text-muted-foreground">
            {abandonedGames(squares)}
          </span>
        </CommitmentRow>
      </div>
      <div className="flex shrink-0 justify-center px-6 py-4">
        <div className="flex w-fit flex-col gap-1.5">
          <span className="mb-0.5 text-xs text-muted-foreground">
            Recent games
          </span>
          <div className="grid grid-flow-col grid-rows-4 justify-start gap-1">
            {recent.map((square, index) => (
              <Tooltip
                key={offset + index}
                open={openIndex === index}
                onOpenChange={open =>
                  setOpenIndex(current =>
                    open ? index : current === index ? undefined : current
                  )
                }
              >
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    aria-label={squareLabel(square)}
                    onClick={() => setOpenIndex(index)}
                    className={cn(
                      "size-5 cursor-pointer rounded-[3px]",
                      shadeTone[square.shade]
                    )}
                  />
                </TooltipTrigger>
                <TooltipContent className="px-3 py-2">
                  <SquareBreakdown square={square} />
                </TooltipContent>
              </Tooltip>
            ))}
            {Array.from({ length: gridSlots - recent.length }, (_, index) => (
              <span
                key={index}
                className="size-5 rounded-[3px] border border-border/60 bg-muted/50"
              />
            ))}
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Older</span>
            <span>Newer</span>
          </div>
        </div>
      </div>
    </div>
  );
};
