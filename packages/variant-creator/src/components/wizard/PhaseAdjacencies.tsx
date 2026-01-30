import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ProvinceLayer } from "@/components/map/ProvinceLayer";
import { useVariant } from "@/hooks/useVariant";
import {
  detectAllAdjacencies,
  syncAdjacenciesToProvinces,
  buildAdjacencyMapFromProvinces,
  toggleAdjacency,
  getIsolatedProvinces,
  type AdjacencyMap,
} from "@/utils/adjacency";
import { Wand2, ChevronLeft, ChevronRight, AlertTriangle, X } from "lucide-react";

export function PhaseAdjacencies() {
  const { variant, setProvinces } = useVariant();
  const [selectedProvinceIndex, setSelectedProvinceIndex] = useState(0);
  const [hoveredProvinceId, setHoveredProvinceId] = useState<string | null>(
    null
  );
  const [adjacencyMap, setAdjacencyMap] = useState<AdjacencyMap>(() => ({}));
  const hasInitialized = useRef(false);

  const provinces = useMemo(
    () => variant?.provinces ?? [],
    [variant?.provinces]
  );

  const selectedProvince = provinces[selectedProvinceIndex] ?? null;
  const selectedProvinceId = selectedProvince?.id ?? null;

  useEffect(() => {
    if (!hasInitialized.current && variant && provinces.length > 0) {
      const existingAdjacencies = buildAdjacencyMapFromProvinces(provinces);
      setAdjacencyMap(existingAdjacencies);
      hasInitialized.current = true;
    }
  }, [variant, provinces]);

  const syncToProvinces = useCallback(
    (newAdjacencyMap: AdjacencyMap) => {
      if (!variant) return;
      const updatedProvinces = syncAdjacenciesToProvinces(
        provinces,
        newAdjacencyMap
      );
      setProvinces(updatedProvinces);
    },
    [variant, provinces, setProvinces]
  );

  const handleAutoDetect = () => {
    const detected = detectAllAdjacencies(provinces);
    setAdjacencyMap(detected);
    syncToProvinces(detected);
  };

  const handleProvinceClick = (provinceId: string) => {
    if (!selectedProvinceId || provinceId === selectedProvinceId) {
      return;
    }
    const newMap = toggleAdjacency(adjacencyMap, selectedProvinceId, provinceId);
    setAdjacencyMap(newMap);
    syncToProvinces(newMap);
  };

  const handleRemoveAdjacency = (adjacentId: string) => {
    if (!selectedProvinceId) return;
    const newMap = toggleAdjacency(adjacencyMap, selectedProvinceId, adjacentId);
    setAdjacencyMap(newMap);
    syncToProvinces(newMap);
  };

  const handlePrevious = () => {
    setSelectedProvinceIndex((prev) =>
      prev > 0 ? prev - 1 : provinces.length - 1
    );
  };

  const handleNext = () => {
    setSelectedProvinceIndex((prev) =>
      prev < provinces.length - 1 ? prev + 1 : 0
    );
  };

  const currentAdjacencies = useMemo(() => {
    if (!selectedProvinceId) return [];
    return adjacencyMap[selectedProvinceId] ?? [];
  }, [selectedProvinceId, adjacencyMap]);

  const isolatedProvinces = useMemo(
    () => getIsolatedProvinces(provinces, adjacencyMap),
    [provinces, adjacencyMap]
  );

  const totalAdjacencies = useMemo(() => {
    let count = 0;
    Object.values(adjacencyMap).forEach((arr) => {
      count += arr.length;
    });
    return count / 2;
  }, [adjacencyMap]);

  if (!variant) {
    return null;
  }

  const { dimensions, decorativeElements, nations } = variant;

  if (provinces.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Province Adjacencies</CardTitle>
            <CardDescription>
              No provinces found. Please complete previous phases first.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Province Adjacencies</CardTitle>
          <CardDescription>
            Define which provinces connect to each other. Select a province,
            then click neighboring provinces to toggle adjacencies.
            <span className="ml-2 text-muted-foreground">
              {Math.round(totalAdjacencies)} connections defined
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <svg
                viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                className="w-full h-auto border rounded-lg bg-muted"
                style={{ maxHeight: "40vh" }}
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
                  adjacentProvinceIds={currentAdjacencies}
                  onProvinceClick={handleProvinceClick}
                  onProvinceMouseEnter={setHoveredProvinceId}
                  onProvinceMouseLeave={() => setHoveredProvinceId(null)}
                />
              </svg>

              <div className="mt-2 flex items-center justify-between">
                <Button variant="outline" size="sm" onClick={handlePrevious}>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>

                <div className="text-sm text-center">
                  <div className="font-medium">
                    {selectedProvince?.name || selectedProvince?.id || "—"}
                  </div>
                  <div className="text-muted-foreground">
                    Province {selectedProvinceIndex + 1} of {provinces.length}
                    {" • "}
                    {currentAdjacencies.length} adjacencies
                  </div>
                </div>

                <Button variant="outline" size="sm" onClick={handleNext}>
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAutoDetect} variant="outline">
                <Wand2 className="mr-2 h-4 w-4" />
                Auto-Detect Adjacencies
              </Button>
            </div>

            {isolatedProvinces.length > 0 && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
                  <div>
                    <div className="font-medium text-destructive">
                      {isolatedProvinces.length} province
                      {isolatedProvinces.length !== 1 ? "s" : ""} with no
                      adjacencies
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {isolatedProvinces.map((p) => p.name || p.id).join(", ")}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="border rounded-lg max-h-[200px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr className="border-b">
                    <th className="px-4 py-3 text-left font-medium">
                      Adjacent to{" "}
                      {selectedProvince?.name || selectedProvince?.id}
                    </th>
                    <th className="w-20 px-4 py-3 text-right font-medium">
                      Remove
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {currentAdjacencies.length === 0 ? (
                    <tr>
                      <td
                        colSpan={2}
                        className="px-4 py-3 text-muted-foreground text-center"
                      >
                        No adjacencies defined. Click provinces on the map to
                        add.
                      </td>
                    </tr>
                  ) : (
                    currentAdjacencies.map((adjId) => {
                      const adjProvince = provinces.find((p) => p.id === adjId);
                      return (
                        <tr key={adjId} className="border-b hover:bg-muted/50">
                          <td className="px-4 py-3">
                            {adjProvince?.name || adjId}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveAdjacency(adjId)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
