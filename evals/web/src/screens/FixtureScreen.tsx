import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Plus } from "lucide-react";
import { useFixture, useLabelOrderSet, type Label } from "@/api";
import { Board } from "@/components/Board";
import { LabelButtons } from "@/components/LabelButtons";
import { OrderSetRow } from "@/components/OrderSetRow";
import { SetBuilder } from "@/components/SetBuilder";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LABELS } from "@/labels";

interface FixtureProps {
  fixtureId: string;
}

const keyOf = (orders: string[]) => orders.join("|");

const Fixture: React.FC<FixtureProps> = ({ fixtureId }) => {
  const { data: fixture } = useFixture(fixtureId);
  const labelOrderSet = useLabelOrderSet();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string> | null>(null);
  const [draftReason, setDraftReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const selected = fixture.order_sets.find(orderSet => keyOf(orderSet.orders) === selectedKey);
  const shown = useMemo(
    () => (draft ? Object.values(draft) : (selected?.orders ?? [])).map(id => fixture.orders[id]),
    [draft, selected, fixture]
  );

  const save = async (orders: string[], label: Label, reason: string) => {
    setError(null);
    try {
      await labelOrderSet.mutateAsync({ fixtureId, orders, label, reason });
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return false;
    }
  };

  const saveDraft = async (label: Label) => {
    const orders = Object.values(draft ?? {}).sort();
    if (await save(orders, label, draftReason)) {
      setSelectedKey(keyOf(orders));
      setDraft(null);
      setDraftReason("");
    }
  };

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col gap-4 p-6">
        <div>
          <h1 className="text-lg font-semibold">
            {fixture.nation} · {fixture.phase.season} {fixture.phase.year} {fixture.phase.type}
          </h1>
          {fixture.notes && <p className="text-sm text-muted-foreground">{fixture.notes}</p>}
        </div>
        <div className="min-h-0 flex-1">
          <Board board={fixture} orders={shown} />
        </div>
      </div>
      <div className="flex w-[26rem] shrink-0 flex-col gap-6 overflow-y-auto border-l p-6">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {LABELS.map(group => {
          const orderSets = fixture.order_sets.filter(orderSet => orderSet.label === group.label);
          return (
            <section key={group.label} className="flex flex-col gap-1">
              <h2 className="flex items-center gap-2 px-3 text-sm font-semibold">
                <span className={`size-2 rounded-full ${group.dot}`} />
                {group.name}
              </h2>
              {orderSets.length === 0 ? (
                <p className="px-3 text-sm text-muted-foreground">None yet.</p>
              ) : (
                <ul className="flex flex-col gap-0.5">
                  {orderSets.map(orderSet => (
                    <OrderSetRow
                      key={keyOf(orderSet.orders)}
                      orderSet={orderSet}
                      selected={draft === null && keyOf(orderSet.orders) === selectedKey}
                      pending={labelOrderSet.isPending}
                      onSelect={() => {
                        setDraft(null);
                        setSelectedKey(keyOf(orderSet.orders));
                      }}
                      onSave={(label, reason) => save(orderSet.orders, label, reason)}
                    />
                  ))}
                </ul>
              )}
            </section>
          );
        })}
        {draft === null ? (
          <Button variant="outline" onClick={() => setDraft({})}>
            <Plus />
            Add order set
          </Button>
        ) : (
          <section className="flex flex-col gap-3 rounded-md border p-3">
            <h2 className="text-sm font-semibold">New order set</h2>
            <SetBuilder fixture={fixture} draft={draft} onChange={setDraft} />
            <Input
              placeholder="Reason"
              aria-label="Reason"
              value={draftReason}
              onChange={event => setDraftReason(event.target.value)}
            />
            <LabelButtons label={null} disabled={labelOrderSet.isPending} onLabel={saveDraft} />
            <Button variant="ghost" size="sm" onClick={() => setDraft(null)}>
              Cancel
            </Button>
          </section>
        )}
      </div>
    </div>
  );
};

export const FixtureScreen: React.FC = () => {
  const { fixtureId } = useParams();
  return fixtureId ? <Fixture key={fixtureId} fixtureId={fixtureId} /> : null;
};
