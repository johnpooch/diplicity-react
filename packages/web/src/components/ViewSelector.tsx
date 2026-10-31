import { useState } from "react";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import { Check, ListFilter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useIsMobile } from "@/hooks/use-mobile";

interface ViewSelectorOption<K extends string> {
  key: K;
  label: string;
}

interface ViewSelectorProps<K extends string> {
  options: readonly ViewSelectorOption<K>[];
  value: K;
  defaultValue: K;
  onChange: (value: K) => void;
  label: string;
  title: string;
  description: string;
}

function ViewSelector<K extends string>({
  options,
  value,
  defaultValue,
  onChange,
  label,
  title,
  description,
}: ViewSelectorProps<K>) {
  const isMobile = useIsMobile();
  const [open, setOpen] = useState(false);
  const selected = options.find(option => option.key === value) ?? options[0];
  const triggerLabel = `${label}, ${selected.label} selected`;

  const handleSelect = (next: K) => {
    onChange(next);
    setOpen(false);
  };

  const optionButtons = (
    <div className="grid gap-1">
      {options.map(option => (
        <Button
          key={option.key}
          variant={value === option.key ? "secondary" : "ghost"}
          aria-pressed={value === option.key}
          onClick={() => handleSelect(option.key)}
          className="justify-between"
        >
          {option.label}
          {value === option.key && <Check />}
        </Button>
      ))}
    </div>
  );

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="relative" aria-label={triggerLabel}>
            <ListFilter />
            {value !== defaultValue && (
              <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-primary ring-2 ring-background" />
            )}
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="rounded-t-lg p-2">
          <VisuallyHidden.Root>
            <SheetTitle>{title}</SheetTitle>
            <SheetDescription>{description}</SheetDescription>
          </VisuallyHidden.Root>
          {optionButtons}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" aria-label={triggerLabel}>
          {selected.label}
          <ListFilter />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-64 p-2">
        {optionButtons}
      </PopoverContent>
    </Popover>
  );
}

export { ViewSelector };
