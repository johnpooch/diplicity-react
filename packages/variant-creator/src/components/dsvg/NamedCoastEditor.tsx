import {
  useMemo,
  useEffect,
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
} from "react";
import { AlertCircle } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { buildPreviewSvg } from "@/utils/svgPreview";
import { extractProvinces, extractLayerPaths } from "@/utils/svgProvinces";
import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";

export interface NamedCoastEntry {
  svgId: string;
  parentProvince: string;
  coastAbbr: string;
}

export interface NamedCoastEditorHandle {
  getData: () => NamedCoastEntry[];
}

interface NamedCoastEditorProps {
  svgContent: string;
  assignments: LayerAssignments;
  provinceAbbrs: Record<string, string>;
}

interface CoastState {
  parentProvince: string;
  coastAbbr: string;
}

export const NamedCoastEditor = forwardRef<
  NamedCoastEditorHandle,
  NamedCoastEditorProps
>(({ svgContent, assignments, provinceAbbrs }, ref) => {
  const namedCoastsKey = assignments.namedCoasts;

  const { viewBox, provinces: coastElements } = useMemo(
    () => extractProvinces(svgContent, namedCoastsKey),
    [svgContent, namedCoastsKey]
  );

  const aspectRatio = useMemo(() => {
    const parts = viewBox.split(/\s+/).map(Number);
    return parts.length >= 4 && parts[2] > 0 && parts[3] > 0
      ? `${parts[2]} / ${parts[3]}`
      : undefined;
  }, [viewBox]);

  const filteredSvg = useMemo(
    () => buildPreviewSvg(svgContent, assignments),
    [svgContent, assignments]
  );

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const blob = new Blob([filteredSvg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [filteredSvg]);

  const provincePaths = useMemo(
    () => extractLayerPaths(svgContent, assignments.provinces),
    [svgContent, assignments.provinces]
  );

  const borderPaths = useMemo(
    () => extractLayerPaths(svgContent, assignments.borders),
    [svgContent, assignments.borders]
  );

  const [entries, setEntries] = useState<Record<string, CoastState>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const blurTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (blurTimerRef.current) clearTimeout(blurTimerRef.current);
    },
    []
  );

  useEffect(() => {
    const initial: Record<string, CoastState> = {};
    coastElements.forEach(({ svgId }) => {
      initial[svgId] = { parentProvince: "", coastAbbr: "" };
    });
    setEntries(initial);
    setErrors({});
    setFocusedId(null);
  }, [coastElements]);

  useImperativeHandle(
    ref,
    () => ({
      getData() {
        return coastElements.map(({ svgId }) => ({
          svgId,
          parentProvince: entries[svgId]?.parentProvince ?? "",
          coastAbbr: entries[svgId]?.coastAbbr ?? "",
        }));
      },
    }),
    [coastElements, entries]
  );

  const handleFocus = (svgId: string) => {
    if (blurTimerRef.current) {
      clearTimeout(blurTimerRef.current);
      blurTimerRef.current = null;
    }
    setFocusedId(svgId);
  };

  const handleBlur = () => {
    blurTimerRef.current = setTimeout(() => setFocusedId(null), 100);
  };

  const handleParentChange = (svgId: string, value: string) => {
    setEntries(prev => ({
      ...prev,
      [svgId]: { ...prev[svgId], parentProvince: value },
    }));
  };

  const handleCoastAbbrChange = (svgId: string, value: string) => {
    setEntries(prev => ({
      ...prev,
      [svgId]: { ...prev[svgId], coastAbbr: value },
    }));
    if (errors[svgId]) {
      setErrors(prev => {
        const { [svgId]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  const handleCoastAbbrBlur = (svgId: string) => {
    handleBlur();
    const value = entries[svgId]?.coastAbbr ?? "";
    if (value && !/^[a-zA-Z]+$/.test(value)) {
      setErrors(prev => ({ ...prev, [svgId]: "Only letters are allowed." }));
    } else {
      setErrors(prev => {
        const { [svgId]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  const focusedPaths =
    focusedId != null
      ? (coastElements.find(p => p.svgId === focusedId)?.pathData ?? [])
      : [];

  const provinceOptions = [...new Set(Object.values(provinceAbbrs))].sort();

  const formContent =
    !namedCoastsKey ? (
      <p className="text-sm text-muted-foreground">
        No named-coast layer was selected. You can proceed to the next step.
      </p>
    ) : coastElements.length === 0 ? (
      <p className="text-sm text-muted-foreground">
        No objects found in the named-coast layer.
      </p>
    ) : (
      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium">
          Named coasts ({coastElements.length})
        </p>

        <div className="flex max-h-[70vh] flex-col gap-1 overflow-y-auto pr-1">
          <div className="grid grid-cols-[140px_1fr_72px] gap-2 pb-1 text-xs font-medium text-muted-foreground">
            <span>Layer ID</span>
            <span>Parent province</span>
            <span>Coast</span>
          </div>

          {coastElements.map(({ svgId }) => {
            const error = errors[svgId];
            return (
              <div key={svgId} className="flex flex-col gap-0.5">
                <div className="grid grid-cols-[140px_1fr_72px] items-center gap-2">
                  <span className="truncate font-mono text-xs text-muted-foreground">
                    {svgId}
                  </span>

                  <Select
                    value={entries[svgId]?.parentProvince ?? ""}
                    onValueChange={value => handleParentChange(svgId, value)}
                  >
                    <SelectTrigger
                      className="w-full"
                      onFocus={() => handleFocus(svgId)}
                      onBlur={handleBlur}
                    >
                      <SelectValue placeholder="Select…" />
                    </SelectTrigger>
                    <SelectContent>
                      {provinceOptions.map(abbr => (
                        <SelectItem key={abbr} value={abbr}>
                          {abbr}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Input
                    value={entries[svgId]?.coastAbbr ?? ""}
                    maxLength={2}
                    placeholder="nc"
                    aria-invalid={!!error}
                    onChange={e => handleCoastAbbrChange(svgId, e.target.value)}
                    onFocus={() => handleFocus(svgId)}
                    onBlur={() => handleCoastAbbrBlur(svgId)}
                    className="font-mono text-sm"
                  />
                </div>

                {error && (
                  <div className="col-start-3 flex items-center gap-1 pl-[calc(140px+1fr+0.5rem)] text-xs text-destructive">
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

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      {formContent}

      <div className="relative w-full" style={{ aspectRatio }}>
        {previewUrl && (
          <>
            <img
              src={previewUrl}
              alt="SVG layer preview"
              className="h-full w-full rounded-lg border object-contain"
            />
            <svg
              viewBox={viewBox}
              className="pointer-events-none absolute inset-0 h-full w-full"
            >
              {provincePaths.map((d, i) => (
                <path
                  key={`p-${i}`}
                  d={d}
                  fill="black"
                  fillOpacity="0.1"
                  stroke="none"
                />
              ))}
              {borderPaths.map((d, i) => (
                <path
                  key={`b-${i}`}
                  d={d}
                  fill="none"
                  stroke="black"
                  strokeOpacity="0.1"
                  strokeWidth="2"
                />
              ))}
              {focusedPaths.map((d, i) => (
                <path key={i} d={d} fill="yellow" fillOpacity="0.6" />
              ))}
            </svg>
          </>
        )}
      </div>
    </div>
  );
});

NamedCoastEditor.displayName = "NamedCoastEditor";
