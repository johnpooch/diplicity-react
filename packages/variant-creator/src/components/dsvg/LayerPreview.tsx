import {
  useMemo,
  useEffect,
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
} from "react";
import { buildPreviewSvg } from "@/utils/svgPreview";
import { extractProvinces } from "@/utils/svgProvinces";
import { ProvinceIdList } from "@/components/dsvg/ProvinceIdList";
import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";

export interface LayerPreviewHandle {
  validate: () => Record<string, string> | null;
}

interface LayerPreviewProps {
  svgContent: string;
  assignments: LayerAssignments;
}

function validateAbbr(
  svgId: string,
  value: string,
  abbrs: Record<string, string>
): string | null {
  if (!value || !/^[a-zA-Z]+$/.test(value)) {
    return "Only letters are allowed.";
  }
  const duplicate = Object.entries(abbrs).some(
    ([id, abbr]) => id !== svgId && abbr.toLowerCase() === value.toLowerCase()
  );
  if (duplicate) return "Duplicate abbreviation.";
  return null;
}

export const LayerPreview = forwardRef<LayerPreviewHandle, LayerPreviewProps>(
  ({ svgContent, assignments }, ref) => {
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

    const { viewBox, provinces } = useMemo(
      () => extractProvinces(svgContent, assignments.provinces),
      [svgContent, assignments.provinces]
    );

    const aspectRatio = useMemo(() => {
      const parts = viewBox.split(/\s+/).map(Number);
      if (parts.length >= 4 && parts[2] > 0 && parts[3] > 0) {
        return `${parts[2]} / ${parts[3]}`;
      }
      return undefined;
    }, [viewBox]);

    const [abbrs, setAbbrs] = useState<Record<string, string>>({});
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [focusedId, setFocusedId] = useState<string | null>(null);
    const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});

    useEffect(() => {
      const initial: Record<string, string> = {};
      provinces.forEach(({ svgId }) => {
        initial[svgId] = svgId.slice(0, 3).toLowerCase();
      });
      setAbbrs(initial);
      setErrors({});
      setFocusedId(null);
    }, [provinces]);

    useImperativeHandle(
      ref,
      () => ({
        validate() {
          const invalid = provinces.filter(
            p => !/^[a-zA-Z]{3}$/.test(abbrs[p.svgId] ?? "")
          );
          if (invalid.length > 0) {
            const newErrors: Record<string, string> = {};
            invalid.forEach(p => {
              newErrors[p.svgId] = "Must be exactly 3 letters.";
            });
            setErrors(prev => ({ ...prev, ...newErrors }));
            requestAnimationFrame(() => {
              const firstInput = inputRefs.current[invalid[0].svgId];
              firstInput?.scrollIntoView({ behavior: "smooth", block: "nearest" });
              firstInput?.focus();
            });
            return null;
          }
          return { ...abbrs };
        },
      }),
      [abbrs, provinces]
    );

    const handleAbbrChange = (svgId: string, value: string) => {
      setAbbrs(prev => ({ ...prev, [svgId]: value }));
      if (errors[svgId]) {
        setErrors(prev => {
          const { [svgId]: _, ...rest } = prev;
          return rest;
        });
      }
    };

    const handleFocus = (svgId: string) => {
      setFocusedId(svgId);
    };

    const handleBlur = (svgId: string) => {
      const value = abbrs[svgId] ?? "";
      const error = validateAbbr(svgId, value, abbrs);

      if (error) {
        setErrors(prev => ({ ...prev, [svgId]: error }));
        requestAnimationFrame(() => inputRefs.current[svgId]?.focus());
      } else {
        setErrors(prev => {
          const { [svgId]: _, ...rest } = prev;
          return rest;
        });
        setFocusedId(null);
      }
    };

    const focusedPaths =
      focusedId != null
        ? (provinces.find(p => p.svgId === focusedId)?.pathData ?? [])
        : [];

    return (
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <ProvinceIdList
          provinces={provinces}
          abbrs={abbrs}
          errors={errors}
          onAbbrChange={handleAbbrChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          inputRefs={inputRefs}
        />

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
                {focusedPaths.map((d, i) => (
                  <path key={i} d={d} fill="yellow" fillOpacity="0.6" />
                ))}
              </svg>
            </>
          )}
        </div>
      </div>
    );
  }
);

LayerPreview.displayName = "LayerPreview";
