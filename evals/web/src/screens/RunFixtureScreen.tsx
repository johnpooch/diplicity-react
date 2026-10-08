import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useRunFixture, type Reasoning, type RunOrderSet, type UnusableAnswer } from "@/api";
import { Board } from "@/components/Board";
import { RunStats } from "@/components/RunStats";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { Button } from "@/components/ui/button";
import { formatScore, LABELS, plural, UNMARKED } from "@/labels";
import { cn } from "@/lib/utils";

interface RunFixtureProps {
  name: string;
  fixtureId: string;
}

interface OrderSetItemProps {
  orderSet: RunOrderSet;
  selected: boolean;
  onSelect: () => void;
}

interface UnusableItemProps {
  answer: UnusableAnswer;
  selected: boolean;
  onSelect: () => void;
}

interface GroupProps {
  name: string;
  dot: string;
  count: number;
  children: React.ReactNode;
}

const keyOf = (orders: string[]) => orders.join("|");

const Reasonings: React.FC<{ reasonings: Reasoning[] }> = ({ reasonings }) =>
  reasonings.length === 0 ? (
    <p className="text-sm text-muted-foreground">No reasoning given.</p>
  ) : (
    <div className="flex flex-col gap-3">
      {reasonings.map(entry => (
        <div key={entry.epoch} className="text-sm">
          <p className="text-xs text-muted-foreground">Epoch {entry.epoch}</p>
          <p className="whitespace-pre-wrap">{entry.reasoning}</p>
        </div>
      ))}
    </div>
  );

const OrderSetItem: React.FC<OrderSetItemProps> = ({ orderSet, selected, onSelect }) => (
  <li
    className={cn("cursor-pointer rounded-md px-3 py-2 hover:bg-accent", selected && "bg-accent")}
    onClick={onSelect}
  >
    <div className="flex items-baseline justify-between gap-2">
      <p className="text-sm font-medium">{orderSet.name || "No orders"}</p>
      <span
        className="shrink-0 text-xs text-muted-foreground tabular-nums"
        title={`Produced in ${plural(orderSet.epochs.length, "epoch")}`}
      >
        ×{orderSet.epochs.length}
      </span>
    </div>
    {orderSet.reason && <p className="text-sm text-muted-foreground">{orderSet.reason}</p>}
    {selected && (
      <div className="mt-3 flex flex-col gap-3 border-t pt-3">
        <Reasonings reasonings={orderSet.reasonings} />
      </div>
    )}
  </li>
);

const UnusableItem: React.FC<UnusableItemProps> = ({ answer, selected, onSelect }) => (
  <li
    className={cn("cursor-pointer rounded-md px-3 py-2 hover:bg-accent", selected && "bg-accent")}
    onClick={onSelect}
  >
    <p className="text-xs text-muted-foreground">Epoch {answer.epoch}</p>
    <p className="text-sm">{answer.problem}</p>
    {selected && (
      <pre className="mt-3 overflow-x-auto border-t pt-3 text-xs whitespace-pre-wrap">{answer.completion}</pre>
    )}
  </li>
);

const Group: React.FC<GroupProps> = ({ name, dot, count, children }) => (
  <section className="flex flex-col gap-1">
    <h2 className="flex items-center gap-2 px-3 text-sm font-semibold">
      <span className={`size-2 rounded-full ${dot}`} />
      {name}
      <span className="font-normal text-muted-foreground tabular-nums">{count}</span>
    </h2>
    <ul className="flex flex-col gap-0.5">{children}</ul>
  </section>
);

const RunFixture: React.FC<RunFixtureProps> = ({ name, fixtureId }) => {
  const { data: run } = useRunFixture(name, fixtureId);
  const { fixture, summary } = run;
  const [selectedKey, setSelectedKey] = useState<string | null>(
    run.order_sets.length > 0 ? keyOf(run.order_sets[0].orders) : null
  );
  const selected = run.order_sets.find(orderSet => keyOf(orderSet.orders) === selectedKey);
  const shown = useMemo(() => (selected ? selected.orders.map(id => selected.details[id]) : []), [selected]);

  const groups = [
    ...LABELS.map(option => ({ ...option, orderSets: run.order_sets.filter(own => own.label === option.label) })),
    { ...UNMARKED, label: null, orderSets: run.order_sets.filter(own => own.label === null) },
  ];

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col gap-4 p-6">
        <div>
          <h1 className="text-lg font-semibold">
            {fixture.nation} · {fixture.phase.season} {fixture.phase.year} {fixture.phase.type}
          </h1>
          <p className="text-sm text-muted-foreground">
            {selected ? selected.name || "No orders" : "No order set to draw"}
          </p>
        </div>
        <div className="min-h-0 flex-1">
          <Board board={fixture} orders={shown} />
        </div>
      </div>
      <div className="flex w-[26rem] shrink-0 flex-col gap-6 overflow-y-auto border-l p-6">
        <header className="flex flex-col gap-4">
          <div>
            <Link to={`/runs/${name}`} className="text-sm text-muted-foreground hover:underline">
              Back to run
            </Link>
            <p className="truncate text-sm font-medium">{fixture.id}</p>
          </div>
          <p className="text-3xl font-semibold tabular-nums">
            {formatScore(summary.score)}
            <span className="ml-2 text-base font-normal text-muted-foreground">reasonable</span>
          </p>
          <ScoreBreakdown counts={summary} />
          <RunStats counts={summary} epochs={summary.answers} />
          <div className="flex gap-2">
            {summary.new > 0 && (
              <Button asChild size="sm">
                <Link to={`/runs/${name}/review`}>Review unmarked</Link>
              </Button>
            )}
            <Button asChild size="sm" variant="outline">
              <Link to={`/fixtures/${fixtureId}`}>Edit labels</Link>
            </Button>
          </div>
        </header>
        {groups
          .filter(group => group.orderSets.length > 0)
          .map(group => (
            <Group key={group.name} name={group.name} dot={group.dot} count={group.orderSets.length}>
              {group.orderSets.map(orderSet => (
                <OrderSetItem
                  key={keyOf(orderSet.orders)}
                  orderSet={orderSet}
                  selected={keyOf(orderSet.orders) === selectedKey}
                  onSelect={() => setSelectedKey(keyOf(orderSet.orders))}
                />
              ))}
            </Group>
          ))}
        {run.unusable.length > 0 && (
          <Group name="Failed" dot="bg-amber-500" count={run.unusable.length}>
            {run.unusable.map(answer => (
              <UnusableItem
                key={answer.epoch}
                answer={answer}
                selected={selectedKey === `epoch:${answer.epoch}`}
                onSelect={() => setSelectedKey(`epoch:${answer.epoch}`)}
              />
            ))}
          </Group>
        )}
      </div>
    </div>
  );
};

export const RunFixtureScreen: React.FC = () => {
  const { runName, fixtureId } = useParams();
  return runName && fixtureId ? (
    <RunFixture key={`${runName}|${fixtureId}`} name={runName} fixtureId={fixtureId} />
  ) : null;
};
