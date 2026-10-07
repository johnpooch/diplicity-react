import type { Label } from "@/api";
import { Button } from "@/components/ui/button";
import { LABELS } from "@/labels";
import { cn } from "@/lib/utils";

interface LabelButtonsProps {
  label: Label | null;
  disabled?: boolean;
  showKeys?: boolean;
  onLabel: (label: Label) => void;
}

export const LabelButtons: React.FC<LabelButtonsProps> = ({ label, disabled, showKeys, onLabel }) => (
  <div className="flex gap-2">
    {LABELS.map(option => (
      <Button
        key={option.label}
        variant="outline"
        disabled={disabled}
        aria-pressed={label === option.label}
        className={cn("flex-1", label === option.label && option.active)}
        onClick={() => onLabel(option.label)}
      >
        {option.name}
        {showKeys && <kbd className="text-xs opacity-60">{option.key}</kbd>}
      </Button>
    ))}
  </div>
);
