import { useState, useRef } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const PRESET_COLORS = [
  { name: "England Blue", value: "#2196F3" },
  { name: "France Cyan", value: "#00BCD4" },
  { name: "Germany Gray", value: "#607D8B" },
  { name: "Austria Red", value: "#F44336" },
  { name: "Italy Green", value: "#4CAF50" },
  { name: "Russia Purple", value: "#9C27B0" },
  { name: "Turkey Yellow", value: "#FFC107" },
  { name: "Dark Blue", value: "#1565C0" },
  { name: "Teal", value: "#009688" },
  { name: "Orange", value: "#FF5722" },
  { name: "Pink", value: "#E91E63" },
  { name: "Brown", value: "#795548" },
];

interface NationColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  disabled?: boolean;
}

export function NationColorPicker({
  value,
  onChange,
  disabled,
}: NationColorPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customColor, setCustomColor] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  const handlePresetClick = (color: string) => {
    onChange(color);
    setCustomColor(color);
    setIsOpen(false);
  };

  const handleCustomChange = (newValue: string) => {
    setCustomColor(newValue);
    if (/^#[0-9A-Fa-f]{6}$/.test(newValue)) {
      onChange(newValue);
    }
  };

  const handleSwatchClick = () => {
    if (disabled) return;
    setIsOpen(!isOpen);
  };

  const isValidHex = /^#[0-9A-Fa-f]{6}$/.test(customColor);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleSwatchClick}
        disabled={disabled}
        className={cn(
          "h-9 w-9 rounded-md border shadow-sm transition-colors",
          "hover:ring-2 hover:ring-ring hover:ring-offset-2",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          disabled && "cursor-not-allowed opacity-50"
        )}
        style={{ backgroundColor: value }}
        aria-label="Select color"
      />

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-2 w-64 rounded-lg border bg-popover p-3 shadow-lg">
          <div className="mb-3 grid grid-cols-6 gap-2">
            {PRESET_COLORS.map((preset) => (
              <button
                key={preset.value}
                type="button"
                onClick={() => handlePresetClick(preset.value)}
                className={cn(
                  "relative h-8 w-8 rounded-md border transition-all",
                  "hover:scale-110 hover:ring-2 hover:ring-ring",
                  "focus:outline-none focus:ring-2 focus:ring-ring"
                )}
                style={{ backgroundColor: preset.value }}
                title={preset.name}
              >
                {value === preset.value && (
                  <Check
                    className="absolute inset-0 m-auto h-4 w-4"
                    style={{
                      color: isLightColor(preset.value) ? "#000" : "#fff",
                    }}
                  />
                )}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                ref={inputRef}
                type="text"
                value={customColor}
                onChange={(e) => handleCustomChange(e.target.value)}
                placeholder="#000000"
                className={cn(
                  "font-mono text-sm",
                  !isValidHex && customColor !== "" && "border-destructive"
                )}
              />
            </div>
            <Button
              type="button"
              size="sm"
              onClick={() => setIsOpen(false)}
              disabled={!isValidHex}
            >
              Done
            </Button>
          </div>

          {!isValidHex && customColor !== "" && (
            <p className="mt-1 text-xs text-destructive">
              Enter a valid hex color (e.g., #FF5733)
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function isLightColor(hex: string): boolean {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5;
}
