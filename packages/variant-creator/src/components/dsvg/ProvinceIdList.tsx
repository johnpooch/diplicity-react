import { AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { ProvinceElement } from "@/utils/svgProvinces";

interface ProvinceIdListProps {
  provinces: ProvinceElement[];
  abbrs: Record<string, string>;
  errors: Record<string, string>;
  onAbbrChange: (svgId: string, value: string) => void;
  onFocus: (svgId: string) => void;
  onBlur: (svgId: string) => void;
  inputRefs: React.MutableRefObject<Record<string, HTMLInputElement | null>>;
}

export function ProvinceIdList({
  provinces,
  abbrs,
  errors,
  onAbbrChange,
  onFocus,
  onBlur,
  inputRefs,
}: ProvinceIdListProps) {
  if (provinces.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No provinces found in the selected layer.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium">
        Province abbreviations ({provinces.length})
      </p>
      <div className="flex max-h-[70vh] flex-col gap-1 overflow-y-auto pr-1">
        {provinces.map(({ svgId }) => {
          const error = errors[svgId];

          return (
            <div key={svgId} className="flex flex-col gap-0.5">
              <div className="flex items-center gap-2">
                <span className="w-28 shrink-0 truncate font-mono text-xs text-muted-foreground">
                  {svgId}
                </span>
                <Input
                  ref={el => {
                    inputRefs.current[svgId] = el;
                  }}
                  value={abbrs[svgId] ?? ""}
                  maxLength={3}
                  aria-invalid={!!error}
                  onChange={e => onAbbrChange(svgId, e.target.value)}
                  onFocus={() => onFocus(svgId)}
                  onBlur={() => onBlur(svgId)}
                  className="h-7 font-mono text-sm"
                />
              </div>
              {error && (
                <div className="flex items-center gap-1 pl-[7.5rem] text-xs text-destructive">
                  <AlertCircle className="h-3 w-3 shrink-0" />
                  {error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
