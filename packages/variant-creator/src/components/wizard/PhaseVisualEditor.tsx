import { useState, useMemo, useRef, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ProvinceLayer } from "@/components/map/ProvinceLayer";
import { MarkerLayer, type SelectedElement } from "@/components/map/MarkerLayer";
import { LabelLayer } from "@/components/map/LabelLayer";
import { useVariant } from "@/hooks/useVariant";
import { resetToAutoPosition, resetLabelToAutoPosition } from "@/utils/positionReset";
import type { Position } from "@/types/variant";
import type { MarkerType } from "@/components/map/DraggableMarker";
import { RotateCcw, Check } from "lucide-react";

interface VisibilityState {
  units: boolean;
  dislodged: boolean;
  supplyCenters: boolean;
  labels: boolean;
}

interface EditingLabel {
  provinceId: string;
  labelIndex: number;
  text: string;
}

export function PhaseVisualEditor() {
  const {
    variant,
    updateProvincePosition,
    updateProvinceLabel,
    updateProvince,
  } = useVariant();

  const svgRef = useRef<SVGSVGElement>(null);

  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [visibility, setVisibility] = useState<VisibilityState>({
    units: true,
    dislodged: true,
    supplyCenters: true,
    labels: true,
  });
  const [editingLabel, setEditingLabel] = useState<EditingLabel | null>(null);

  const provinces = useMemo(() => variant?.provinces ?? [], [variant?.provinces]);
  const nations = useMemo(() => variant?.nations ?? [], [variant?.nations]);

  const selectedProvince = useMemo(() => {
    if (!selectedElement) return null;
    return provinces.find((p) => p.id === selectedElement.provinceId) ?? null;
  }, [selectedElement, provinces]);

  const selectedLabel = useMemo(() => {
    if (!selectedElement || selectedElement.type !== "label") return null;
    if (selectedElement.labelIndex === undefined) return null;
    return selectedProvince?.labels[selectedElement.labelIndex] ?? null;
  }, [selectedElement, selectedProvince]);

  const handleMarkerClick = useCallback(
    (provinceId: string, type: MarkerType) => {
      setSelectedElement({ type, provinceId });
      setEditingLabel(null);
    },
    []
  );

  const handleMarkerDrag = useCallback(
    (provinceId: string, type: MarkerType, position: Position) => {
      const positionType =
        type === "unit"
          ? "unitPosition"
          : type === "dislodged"
          ? "dislodgedUnitPosition"
          : "supplyCenterPosition";
      updateProvincePosition(provinceId, positionType, position);
    },
    [updateProvincePosition]
  );

  const handleLabelClick = useCallback(
    (provinceId: string, labelIndex: number) => {
      setSelectedElement({ type: "label", provinceId, labelIndex });
      setEditingLabel(null);
    },
    []
  );

  const handleLabelDrag = useCallback(
    (provinceId: string, labelIndex: number, position: Position) => {
      updateProvinceLabel(provinceId, labelIndex, { position });
    },
    [updateProvinceLabel]
  );

  const handleLabelDoubleClick = useCallback(
    (provinceId: string, labelIndex: number) => {
      const province = provinces.find((p) => p.id === provinceId);
      const label = province?.labels[labelIndex];
      if (label) {
        setEditingLabel({
          provinceId,
          labelIndex,
          text: label.text,
        });
        setSelectedElement({ type: "label", provinceId, labelIndex });
      }
    },
    [provinces]
  );

  const handleEditLabelText = useCallback(
    (text: string) => {
      if (!editingLabel) return;
      setEditingLabel({ ...editingLabel, text });
    },
    [editingLabel]
  );

  const handleSaveEditingLabel = useCallback(() => {
    if (!editingLabel) return;
    updateProvinceLabel(editingLabel.provinceId, editingLabel.labelIndex, {
      text: editingLabel.text,
    });
    setEditingLabel(null);
  }, [editingLabel, updateProvinceLabel]);

  const handleLabelRotationChange = useCallback(
    (rotation: number) => {
      if (!selectedElement || selectedElement.type !== "label") return;
      if (selectedElement.labelIndex === undefined) return;
      updateProvinceLabel(selectedElement.provinceId, selectedElement.labelIndex, {
        rotation,
      });
    },
    [selectedElement, updateProvinceLabel]
  );

  const handleResetToAuto = useCallback(() => {
    if (!selectedElement || !selectedProvince) return;

    if (selectedElement.type === "label") {
      if (selectedElement.labelIndex === undefined) return;
      const autoPosition = resetLabelToAutoPosition(selectedProvince);
      updateProvinceLabel(selectedElement.provinceId, selectedElement.labelIndex, {
        position: autoPosition,
        rotation: 0,
      });
    } else {
      const autoPositions = resetToAutoPosition(selectedProvince);
      const positionType =
        selectedElement.type === "unit"
          ? "unitPosition"
          : selectedElement.type === "dislodged"
          ? "dislodgedUnitPosition"
          : "supplyCenterPosition";
      updateProvince(selectedElement.provinceId, {
        [positionType]: autoPositions[positionType],
      });
    }
  }, [selectedElement, selectedProvince, updateProvinceLabel, updateProvince]);

  const handleSvgClick = useCallback(() => {
    setSelectedElement(null);
    setEditingLabel(null);
  }, []);

  const toggleVisibility = useCallback((key: keyof VisibilityState) => {
    setVisibility((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  if (!variant) {
    return null;
  }

  const { dimensions, decorativeElements } = variant;

  if (provinces.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Visual Editor</CardTitle>
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
          <CardTitle>Visual Editor</CardTitle>
          <CardDescription>
            Adjust positions for units, supply centers, and labels. Click to
            select, drag to move. Double-click labels to edit text.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-units"
                  checked={visibility.units}
                  onCheckedChange={() => toggleVisibility("units")}
                />
                <label htmlFor="show-units" className="text-sm cursor-pointer">
                  Units
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-dislodged"
                  checked={visibility.dislodged}
                  onCheckedChange={() => toggleVisibility("dislodged")}
                />
                <label htmlFor="show-dislodged" className="text-sm cursor-pointer">
                  Dislodged
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-supply-centers"
                  checked={visibility.supplyCenters}
                  onCheckedChange={() => toggleVisibility("supplyCenters")}
                />
                <label htmlFor="show-supply-centers" className="text-sm cursor-pointer">
                  Supply Centers
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-labels"
                  checked={visibility.labels}
                  onCheckedChange={() => toggleVisibility("labels")}
                />
                <label htmlFor="show-labels" className="text-sm cursor-pointer">
                  Labels
                </label>
              </div>
            </div>

            <div>
              <svg
                ref={svgRef}
                viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                className="w-full h-auto border rounded-lg bg-muted"
                style={{ maxHeight: "50vh" }}
                onClick={handleSvgClick}
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
                  selectedProvinceId={null}
                  hoveredProvinceId={null}
                  onProvinceClick={handleSvgClick}
                />

                <MarkerLayer
                  provinces={provinces}
                  nations={nations}
                  markerType="supplyCenter"
                  selectedElement={selectedElement}
                  onMarkerClick={handleMarkerClick}
                  onMarkerDrag={handleMarkerDrag}
                  visible={visibility.supplyCenters}
                  svgRef={svgRef}
                />

                <MarkerLayer
                  provinces={provinces}
                  nations={nations}
                  markerType="unit"
                  selectedElement={selectedElement}
                  onMarkerClick={handleMarkerClick}
                  onMarkerDrag={handleMarkerDrag}
                  visible={visibility.units}
                  svgRef={svgRef}
                />

                <MarkerLayer
                  provinces={provinces}
                  nations={nations}
                  markerType="dislodged"
                  selectedElement={selectedElement}
                  onMarkerClick={handleMarkerClick}
                  onMarkerDrag={handleMarkerDrag}
                  visible={visibility.dislodged}
                  svgRef={svgRef}
                />

                <LabelLayer
                  provinces={provinces}
                  selectedElement={selectedElement}
                  onLabelClick={handleLabelClick}
                  onLabelDrag={handleLabelDrag}
                  onLabelDoubleClick={handleLabelDoubleClick}
                  visible={visibility.labels}
                  svgRef={svgRef}
                />
              </svg>
            </div>

            {selectedElement && selectedProvince && (
              <Card>
                <CardHeader className="py-4">
                  <CardTitle className="text-base">
                    {selectedElement.type === "unit" && "Unit Position"}
                    {selectedElement.type === "dislodged" && "Dislodged Unit Position"}
                    {selectedElement.type === "supplyCenter" && "Supply Center Position"}
                    {selectedElement.type === "label" && "Label"}
                  </CardTitle>
                  <CardDescription>
                    {selectedProvince.name || selectedProvince.id}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {editingLabel && selectedElement.type === "label" ? (
                    <div className="flex gap-2">
                      <Input
                        value={editingLabel.text}
                        onChange={(e) => handleEditLabelText(e.target.value)}
                        placeholder="Label text"
                        className="flex-1"
                      />
                      <Button size="sm" onClick={handleSaveEditingLabel}>
                        <Check className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : selectedElement.type === "label" && selectedLabel ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="label-x">X</Label>
                          <Input
                            id="label-x"
                            type="number"
                            value={Math.round(selectedLabel.position.x)}
                            onChange={(e) =>
                              updateProvinceLabel(
                                selectedElement.provinceId,
                                selectedElement.labelIndex!,
                                {
                                  position: {
                                    x: parseFloat(e.target.value) || 0,
                                    y: selectedLabel.position.y,
                                  },
                                }
                              )
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="label-y">Y</Label>
                          <Input
                            id="label-y"
                            type="number"
                            value={Math.round(selectedLabel.position.y)}
                            onChange={(e) =>
                              updateProvinceLabel(
                                selectedElement.provinceId,
                                selectedElement.labelIndex!,
                                {
                                  position: {
                                    x: selectedLabel.position.x,
                                    y: parseFloat(e.target.value) || 0,
                                  },
                                }
                              )
                            }
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="label-rotation">Rotation (degrees)</Label>
                        <Input
                          id="label-rotation"
                          type="number"
                          value={selectedLabel.rotation ?? 0}
                          onChange={(e) =>
                            handleLabelRotationChange(parseFloat(e.target.value) || 0)
                          }
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="position-x">X</Label>
                        <Input
                          id="position-x"
                          type="number"
                          value={Math.round(getSelectedPosition(selectedElement, selectedProvince)?.x ?? 0)}
                          onChange={(e) => {
                            const position = getSelectedPosition(selectedElement, selectedProvince);
                            if (position) {
                              handleMarkerDrag(
                                selectedElement.provinceId,
                                selectedElement.type as MarkerType,
                                { x: parseFloat(e.target.value) || 0, y: position.y }
                              );
                            }
                          }}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="position-y">Y</Label>
                        <Input
                          id="position-y"
                          type="number"
                          value={Math.round(getSelectedPosition(selectedElement, selectedProvince)?.y ?? 0)}
                          onChange={(e) => {
                            const position = getSelectedPosition(selectedElement, selectedProvince);
                            if (position) {
                              handleMarkerDrag(
                                selectedElement.provinceId,
                                selectedElement.type as MarkerType,
                                { x: position.x, y: parseFloat(e.target.value) || 0 }
                              );
                            }
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <Button variant="outline" size="sm" onClick={handleResetToAuto}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset to Auto
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getSelectedPosition(
  selectedElement: SelectedElement,
  province: { unitPosition: Position; dislodgedUnitPosition: Position; supplyCenterPosition?: Position }
): Position | null {
  switch (selectedElement.type) {
    case "unit":
      return province.unitPosition;
    case "dislodged":
      return province.dislodgedUnitPosition;
    case "supplyCenter":
      return province.supplyCenterPosition ?? null;
    default:
      return null;
  }
}
