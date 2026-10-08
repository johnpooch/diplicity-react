import { useState } from "react";
import { Pencil } from "lucide-react";
import type { Label, OrderSet } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LABELS } from "@/labels";
import { cn } from "@/lib/utils";

interface OrderSetRowProps {
  orderSet: OrderSet;
  selected: boolean;
  pending: boolean;
  onSelect: () => void;
  onSave: (label: Label, reason: string) => void;
}

export const OrderSetRow: React.FC<OrderSetRowProps> = ({ orderSet, selected, pending, onSelect, onSave }) => {
  const [editing, setEditing] = useState(false);
  const [reason, setReason] = useState(orderSet.reason);
  const other = LABELS.find(option => option.label !== orderSet.label)!;
  const open = selected && editing;

  const saveReason = () => {
    if (reason.trim() !== orderSet.reason) {
      onSave(orderSet.label, reason);
    }
  };

  return (
    <li
      className={cn("cursor-pointer rounded-md px-3 py-2 hover:bg-accent", selected && "bg-accent")}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium">{orderSet.name || "No orders"}</p>
          {!open && orderSet.reason && <p className="text-sm text-muted-foreground">{orderSet.reason}</p>}
        </div>
        {selected && !editing && (
          <Button size="icon-sm" variant="ghost" aria-label="Edit" onClick={() => setEditing(true)}>
            <Pencil />
          </Button>
        )}
      </div>
      {open && (
        <div className="mt-2 flex flex-col gap-2">
          <Input
            autoFocus
            placeholder="Reason"
            aria-label="Reason"
            value={reason}
            onChange={event => setReason(event.target.value)}
            onBlur={saveReason}
            onKeyDown={event => {
              if (event.key === "Enter") {
                saveReason();
                setEditing(false);
              }
            }}
          />
          <div className="flex justify-between gap-2">
            <Button size="sm" variant="outline" disabled={pending} onClick={() => onSave(other.label, reason)}>
              Mark {other.name.toLowerCase()}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Done
            </Button>
          </div>
        </div>
      )}
    </li>
  );
};
