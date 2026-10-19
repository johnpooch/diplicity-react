import { useState } from "react";
import { TriangleAlert } from "lucide-react";
import type { GamePhase } from "@/api";
import { Button } from "@/components/ui/button";
import { formatResult, succeeded } from "@/games";
import { cn } from "@/lib/utils";

interface GameAnswerPanelProps {
  phase: GamePhase;
  nation: string;
}

const NO_ORDERS: Record<string, string> = {
  Movement: "so its units held",
  Retreat: "so its dislodged units were disbanded",
  Adjustment: "so the engine's civil-disorder default applied",
};

interface RawProps {
  title: string;
  text: string;
}

const Raw: React.FC<RawProps> = ({ title, text }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex flex-col gap-1">
      <Button variant="ghost" size="sm" className="justify-start px-0 text-muted-foreground" onClick={() => setOpen(!open)}>
        {open ? "Hide" : "Show"} {title}
      </Button>
      {open && (
        <pre className="max-h-96 overflow-auto rounded-md bg-muted px-3 py-2 font-mono text-xs whitespace-pre-wrap">
          {text}
        </pre>
      )}
    </div>
  );
};

export const GameAnswerPanel: React.FC<GameAnswerPanelProps> = ({ phase, nation }) => {
  const { answer } = phase;
  if (answer === null) {
    return (
      <p className="text-sm text-muted-foreground">
        {nation} had no legal order this phase, so the model was not asked.
      </p>
    );
  }

  const dislodged = new Set(phase.dislodged.map(province => province.split("/")[0]));

  return (
    <div className="flex flex-col gap-6">
      {answer.problem && (
        <div className="flex gap-2 rounded-md border border-amber-500 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          <div>
            <p className="font-medium">Failed answer: {answer.problem}</p>
            <p>
              No orders were submitted for {nation}, {NO_ORDERS[phase.phase.type]}.
            </p>
          </div>
        </div>
      )}
      <section className="flex flex-col gap-1">
        <h2 className="text-sm font-semibold">Reasoning</h2>
        <p className={cn("text-sm whitespace-pre-wrap", !answer.reasoning && "text-muted-foreground")}>
          {answer.reasoning ?? "No reasoning given."}
        </p>
      </section>
      <section className="flex flex-col gap-1">
        <h2 className="text-sm font-semibold">Orders</h2>
        {answer.orders.length === 0 ? (
          <p className="text-sm text-muted-foreground">No orders.</p>
        ) : (
          <ul className="flex flex-col divide-y text-sm">
            {answer.orders.map(order => (
              <li key={order.id} className="flex items-baseline justify-between gap-3 py-1.5">
                <span className="font-medium">{order.name}</span>
                <span
                  className={cn(
                    "shrink-0 text-xs",
                    succeeded(order.result) ? "text-muted-foreground" : "font-medium text-amber-700"
                  )}
                >
                  {formatResult(order.result)}
                  {dislodged.has(order.source) && " · dislodged"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="flex flex-col">
        <Raw title="raw prompt" text={`${answer.system}\n\n${answer.user}`} />
        <Raw title="raw completion" text={answer.completion ?? "No completion: the model call failed."} />
      </section>
    </div>
  );
};
