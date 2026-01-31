import { useState, useMemo, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProvinceTable } from "@/components/common/ProvinceTable";
import { ProvinceLayer } from "@/components/map/ProvinceLayer";
import { useVariant } from "@/hooks/useVariant";
import type { Province } from "@/types/variant";
import { validateProvinceId, isUniqueId } from "@/utils/idSuggestion";
import { calculateMapMaxHeight } from "@/utils/mapSizing";

function validateProvinces(provinces: Province[]): Map<string, string[]> {
  const errors = new Map<string, string[]>();
  const existingIds = provinces.map((p) => p.id);

  for (const province of provinces) {
    const provinceErrors: string[] = [];

    const idValidation = validateProvinceId(province.id);
    if (!idValidation.valid && idValidation.error) {
      provinceErrors.push(idValidation.error);
    }

    if (
      province.id &&
      !isUniqueId(
        province.id,
        existingIds.filter((id) => id !== province.id),
        province.id
      )
    ) {
      const duplicates = provinces.filter((p) => p.id === province.id);
      if (duplicates.length > 1) {
        provinceErrors.push("ID must be unique");
      }
    }

    if (province.type === "land" && province.startingUnit?.type === "Fleet") {
      provinceErrors.push("Fleet cannot start on land province");
    }

    if (province.type === "sea" && province.startingUnit?.type === "Army") {
      provinceErrors.push("Army cannot start on sea province");
    }

    if (province.startingUnit && !province.supplyCenter) {
      provinceErrors.push("Starting unit requires supply center");
    }

    if (province.startingUnit && !province.homeNation) {
      provinceErrors.push("Starting unit requires home nation");
    }

    if (provinceErrors.length > 0) {
      errors.set(province.id, provinceErrors);
    }
  }

  return errors;
}

export function PhaseProvinces() {
  const { variant, updateProvince, setProvinces } = useVariant();
  const [selectedProvinceId, setSelectedProvinceId] = useState<string | null>(null);
  const [hoveredProvinceId, setHoveredProvinceId] = useState<string | null>(null);

  const validationErrors = useMemo(() => {
    if (!variant) return new Map<string, string[]>();
    return validateProvinces(variant.provinces);
  }, [variant]);

  const hasInitialized = useRef(false);

  useEffect(() => {
    if (hasInitialized.current || !variant) return;
    hasInitialized.current = true;

    const provincesToUpdate = variant.provinces.filter((province) => {
      const svgLabels = province.labels.filter((label) => label.source === "svg");
      return !province.name && svgLabels.length > 0;
    });

    if (provincesToUpdate.length > 0) {
      const updatedProvinces = variant.provinces.map((province) => {
        const svgLabels = province.labels.filter((label) => label.source === "svg");
        if (!province.name && svgLabels.length > 0) {
          return { ...province, name: svgLabels[0].text };
        }
        return province;
      });
      setProvinces(updatedProvinces);
    }
  }, [variant, setProvinces]);

  if (!variant) {
    return null;
  }

  const { provinces, nations, dimensions, decorativeElements } = variant;

  const handleProvinceUpdate = (
    provinceId: string,
    updates: Partial<
      Pick<Province, "id" | "name" | "type" | "homeNation" | "supplyCenter" | "startingUnit">
    >
  ) => {
    if (updates.id && updates.id !== provinceId) {
      const updatedProvinces = provinces.map((p) =>
        p.id === provinceId ? { ...p, ...updates } : p
      );
      setProvinces(updatedProvinces);

      if (selectedProvinceId === provinceId) {
        setSelectedProvinceId(updates.id);
      }
    } else {
      updateProvince(provinceId, updates);
    }
  };

  const handleProvinceClick = (provinceId: string) => {
    setSelectedProvinceId(provinceId === selectedProvinceId ? null : provinceId);
  };

  const errorCount = validationErrors.size;
  const completedCount = provinces.filter(
    (p) => p.id && p.name && validateProvinceId(p.id).valid
  ).length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Province Details</CardTitle>
          <CardDescription>
            Define metadata for each province. Click a row to select it on the map.
            {errorCount > 0 && (
              <span className="ml-2 text-destructive">
                ({errorCount} province{errorCount !== 1 ? "s" : ""} with errors)
              </span>
            )}
            <span className="ml-2 text-muted-foreground">
              {completedCount} of {provinces.length} complete
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <svg
                viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                className="w-full h-auto border rounded-lg bg-muted"
                style={{ maxHeight: calculateMapMaxHeight(dimensions) }}
              >
                {decorativeElements.map((element) => (
                  <g
                    key={element.id}
                    dangerouslySetInnerHTML={{ __html: element.content }}
                  />
                ))}

                <ProvinceLayer
                  provinces={provinces}
                  nations={nations}
                  selectedProvinceId={selectedProvinceId}
                  hoveredProvinceId={hoveredProvinceId}
                  onProvinceClick={handleProvinceClick}
                  onProvinceMouseEnter={setHoveredProvinceId}
                  onProvinceMouseLeave={() => setHoveredProvinceId(null)}
                />
              </svg>

              {selectedProvinceId && (
                <div className="mt-2 p-2 bg-muted rounded text-sm">
                  <strong>Selected:</strong>{" "}
                  {provinces.find((p) => p.id === selectedProvinceId)?.name ||
                    selectedProvinceId}
                </div>
              )}
            </div>

            <ProvinceTable
              provinces={provinces}
              nations={nations}
              selectedProvinceId={selectedProvinceId}
              onProvinceSelect={handleProvinceClick}
              onProvinceHover={setHoveredProvinceId}
              onProvinceUpdate={handleProvinceUpdate}
              validationErrors={validationErrors}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
