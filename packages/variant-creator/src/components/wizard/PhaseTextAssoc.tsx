import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ProvinceLayer } from "@/components/map/ProvinceLayer";
import { TextLayer } from "@/components/map/TextLayer";
import { useVariant } from "@/hooks/useVariant";
import {
  autoAssociateText,
  syncAssociationsToProvinces,
  buildAssociationsFromProvinces,
} from "@/utils/textAssociation";
import { Wand2, X } from "lucide-react";

export function PhaseTextAssoc() {
  const { variant, setProvinces } = useVariant();
  const [selectedTextIndex, setSelectedTextIndex] = useState<number | null>(
    null
  );
  const [hoveredProvinceId, setHoveredProvinceId] = useState<string | null>(
    null
  );
  const [associations, setAssociations] = useState<Map<number, string | null>>(
    () => new Map()
  );
  const tableRowRefs = useRef<Map<number, HTMLTableRowElement>>(new Map());
  const hasInitialized = useRef(false);

  const textElements = useMemo(
    () => variant?.textElements ?? [],
    [variant?.textElements]
  );
  const provinces = useMemo(
    () => variant?.provinces ?? [],
    [variant?.provinces]
  );

  useEffect(() => {
    if (!hasInitialized.current && variant && textElements.length > 0) {
      const existingAssociations = buildAssociationsFromProvinces(
        textElements,
        provinces
      );
      setAssociations(existingAssociations);
      hasInitialized.current = true;
    }
  }, [variant, textElements, provinces]);

  const syncToProvinces = useCallback(
    (newAssociations: Map<number, string | null>) => {
      if (!variant) return;
      const updatedProvinces = syncAssociationsToProvinces(
        textElements,
        provinces,
        newAssociations
      );
      setProvinces(updatedProvinces);
    },
    [variant, textElements, provinces, setProvinces]
  );

  const handleAutoDetect = () => {
    const detected = autoAssociateText(textElements, provinces);
    setAssociations(detected);
    syncToProvinces(detected);
  };

  const handleAssociationChange = (
    textIndex: number,
    provinceId: string | null
  ) => {
    const newAssociations = new Map(associations);
    newAssociations.set(textIndex, provinceId);
    setAssociations(newAssociations);
    syncToProvinces(newAssociations);
  };

  const handleTextClick = (textIndex: number) => {
    setSelectedTextIndex(textIndex === selectedTextIndex ? null : textIndex);
    const row = tableRowRefs.current.get(textIndex);
    if (row) {
      row.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  const handleProvinceClick = (provinceId: string) => {
    if (selectedTextIndex !== null) {
      handleAssociationChange(selectedTextIndex, provinceId);
    }
  };

  const handleClearAssociation = (textIndex: number) => {
    handleAssociationChange(textIndex, null);
  };

  const associatedCount = useMemo(() => {
    let count = 0;
    associations.forEach((value) => {
      if (value !== null) count++;
    });
    return count;
  }, [associations]);

  if (!variant) {
    return null;
  }

  const { dimensions, decorativeElements, nations } = variant;

  if (textElements.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Text Association</CardTitle>
            <CardDescription>
              No text elements found in the SVG. You can proceed to the next
              phase.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              The uploaded SVG does not contain a text layer, or the text layer
              is empty. Province labels can be generated automatically in a
              later phase.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Text Association</CardTitle>
          <CardDescription>
            Link text elements from the SVG to their provinces. Click a text on
            the map, then click a province to associate them.
            <span className="ml-2 text-muted-foreground">
              {associatedCount} of {textElements.length} texts associated
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
                  selectedProvinceId={null}
                  hoveredProvinceId={hoveredProvinceId}
                  onProvinceClick={handleProvinceClick}
                  onProvinceMouseEnter={setHoveredProvinceId}
                  onProvinceMouseLeave={() => setHoveredProvinceId(null)}
                />

                <TextLayer
                  textElements={textElements}
                  associations={associations}
                  selectedTextIndex={selectedTextIndex}
                  onTextClick={handleTextClick}
                />
              </svg>

              {selectedTextIndex !== null && (
                <div className="mt-2 p-2 bg-muted rounded text-sm">
                  <strong>Selected text:</strong>{" "}
                  &quot;{textElements[selectedTextIndex].content}&quot; - Click a
                  province to associate
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAutoDetect} variant="outline">
                <Wand2 className="mr-2 h-4 w-4" />
                Auto-Detect
              </Button>
            </div>

            <div className="border rounded-lg max-h-[300px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr className="border-b">
                    <th className="w-12 px-4 py-3 text-left font-medium">#</th>
                    <th className="px-4 py-3 text-left font-medium">Text Content</th>
                    <th className="w-48 px-4 py-3 text-left font-medium">Province</th>
                    <th className="w-20 px-4 py-3 text-left font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {textElements.map((text, index) => {
                    const isSelected = index === selectedTextIndex;
                    const associatedProvinceId = associations.get(index);

                    return (
                      <tr
                        key={index}
                        ref={(el: HTMLTableRowElement | null) => {
                          if (el) {
                            tableRowRefs.current.set(index, el);
                          } else {
                            tableRowRefs.current.delete(index);
                          }
                        }}
                        className={`cursor-pointer border-b hover:bg-muted/50 ${isSelected ? "bg-muted" : ""}`}
                        onClick={() => setSelectedTextIndex(index)}
                      >
                        <td className="px-4 py-3 font-mono text-muted-foreground">
                          {index + 1}
                        </td>
                        <td
                          className={`px-4 py-3 ${
                            associatedProvinceId === null
                              ? "text-destructive"
                              : ""
                          }`}
                        >
                          {text.content || "(empty)"}
                        </td>
                        <td className="px-4 py-3">
                          <Select
                            value={associatedProvinceId ?? "none"}
                            onValueChange={(value) =>
                              handleAssociationChange(
                                index,
                                value === "none" ? null : value
                              )
                            }
                          >
                            <SelectTrigger
                              className="w-full"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <SelectValue placeholder="Select province" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">
                                (none - decorative)
                              </SelectItem>
                              {provinces.map((province) => (
                                <SelectItem
                                  key={province.id}
                                  value={province.id}
                                >
                                  {province.name || province.id}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="px-4 py-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleClearAssociation(index);
                            }}
                            disabled={associatedProvinceId === null}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
