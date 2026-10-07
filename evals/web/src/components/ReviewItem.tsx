import { useEffect, useMemo, useRef, useState } from "react";
import type { Label, QueueItem } from "@/api";
import { Board } from "@/components/Board";
import { LabelButtons } from "@/components/LabelButtons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type Verdict = { label: Label; reason: string };

interface ReviewItemProps {
  item: QueueItem;
  saved: Verdict | undefined;
  pending: boolean;
  canGoBack: boolean;
  onSave: (verdict: Verdict) => void;
  onSkip: () => void;
  onBack: () => void;
}

const LABEL_KEYS: Record<string, Label> = { r: "reasonable", u: "unreasonable" };
const TYPING_TARGETS = ["INPUT", "TEXTAREA", "SELECT"];

export const ReviewItem: React.FC<ReviewItemProps> = ({
  item,
  saved,
  pending,
  canGoBack,
  onSave,
  onSkip,
  onBack,
}) => {
  const [label, setLabel] = useState<Label | null>(saved?.label ?? null);
  const [reason, setReason] = useState(saved?.reason ?? "");
  const [showReasoning, setShowReasoning] = useState(false);
  const reasonField = useRef<HTMLInputElement>(null);
  const orders = useMemo(() => item.orders.map(id => item.details[id]), [item]);

  const choose = (chosen: Label) => {
    setLabel(chosen);
    reasonField.current?.focus();
  };

  const save = () => {
    if (label !== null && !pending) {
      onSave({ label, reason });
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (event.metaKey || event.ctrlKey || event.altKey || TYPING_TARGETS.includes(target.tagName)) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === "enter" && target.tagName === "BUTTON") {
        return;
      }
      if (key in LABEL_KEYS) {
        event.preventDefault();
        choose(LABEL_KEYS[key]);
      } else if (key === "enter") {
        save();
      } else if (key === "s" || key === "arrowright") {
        onSkip();
      } else if ((key === "b" || key === "arrowleft") && canGoBack) {
        onBack();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  return (
    <div className="flex min-h-0 flex-1">
      <div className="min-w-0 flex-1 p-6">
        <Board board={item.fixture} orders={orders} />
      </div>
      <div className="flex w-[26rem] shrink-0 flex-col gap-6 overflow-y-auto border-l p-6">
        <div>
          <p className="text-sm text-muted-foreground">
            {item.fixture.id} · {item.fixture.nation} · {item.fixture.phase.season} {item.fixture.phase.year}
          </p>
          <h1 className="mt-1 text-lg font-semibold">{item.name || "No orders"}</h1>
        </div>
        <ul className="text-sm">
          {orders.map((order, index) => (
            <li key={item.orders[index]}>
              {order.source_name}: {order.description}
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-3">
          <LabelButtons label={label} disabled={pending} showKeys onLabel={choose} />
          <Input
            ref={reasonField}
            placeholder="Reason (optional)"
            aria-label="Reason"
            value={reason}
            onChange={event => setReason(event.target.value)}
            onKeyDown={event => {
              if (event.key === "Enter") {
                event.preventDefault();
                save();
              } else if (event.key === "Escape") {
                event.currentTarget.blur();
              }
            }}
          />
          <Button disabled={label === null || pending} onClick={save}>
            Save and next
            <kbd className="text-xs opacity-60">Enter</kbd>
          </Button>
        </div>
        {item.reasonings.length > 0 && (
          <div className="flex flex-col gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="self-start"
              aria-expanded={showReasoning}
              onClick={() => setShowReasoning(!showReasoning)}
            >
              {showReasoning ? "Hide reasoning" : "Show reasoning"}
            </Button>
            {showReasoning &&
              item.reasonings.map(entry => (
                <div key={entry.epoch} className="text-sm">
                  {item.reasonings.length > 1 && (
                    <p className="text-xs text-muted-foreground">Epoch {entry.epoch}</p>
                  )}
                  <p className="whitespace-pre-wrap">{entry.reasoning}</p>
                </div>
              ))}
          </div>
        )}
        <div className="mt-auto flex justify-between">
          <Button variant="ghost" size="sm" disabled={!canGoBack} onClick={onBack}>
            Back
            <kbd className="text-xs opacity-60">B</kbd>
          </Button>
          <Button variant="ghost" size="sm" onClick={onSkip}>
            Skip
            <kbd className="text-xs opacity-60">S</kbd>
          </Button>
        </div>
      </div>
    </div>
  );
};
