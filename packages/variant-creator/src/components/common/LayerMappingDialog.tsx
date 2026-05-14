import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { flattenLayerTree, type LayerNameMapping, type SvgLayer } from "@/utils/svg";

const NONE = "__none__";

interface LayerMappingDialogProps {
  open: boolean;
  layers: SvgLayer[];
  onConfirm: (mapping: LayerNameMapping) => void;
  onCancel: () => void;
}

export function LayerMappingDialog({
  open,
  layers,
  onConfirm,
  onCancel,
}: LayerMappingDialogProps) {
  const flatLayers = flattenLayerTree(layers);
  const [provinces, setProvinces] = useState<string>("");
  const [text, setText] = useState<string>(
    flatLayers.find((l) => l.name === "text")?.path ?? NONE
  );
  const [namedCoasts, setNamedCoasts] = useState<string>(
    flatLayers.find((l) => l.name === "named-coasts")?.path ?? NONE
  );

  const handleConfirm = () => {
    if (!provinces) return;
    onConfirm({
      provinces,
      text: text === NONE ? undefined : text,
      namedCoasts: namedCoasts === NONE ? undefined : namedCoasts,
    });
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onCancel(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Map SVG Layers</DialogTitle>
          <DialogDescription>
            The expected layer names weren&apos;t found in your SVG. Select which
            layer corresponds to each role.
          </DialogDescription>
        </DialogHeader>

        {layers.length === 0 ? (
          <p className="text-sm text-destructive">
            No named layers found in this SVG. Ensure your layers have names or
            IDs set (e.g. in Inkscape, check Layer Properties).
          </p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1">
              <Label>
                Provinces <span className="text-destructive">*</span>
              </Label>
              <p className="text-xs text-muted-foreground">
                The layer containing province polygon paths.
              </p>
              <Select value={provinces} onValueChange={setProvinces}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a layer…" />
                </SelectTrigger>
                <SelectContent>
                  {flatLayers.map((layer) => (
                    <SelectItem key={layer.path} value={layer.path}>
                      {layer.path.split("/").join(" › ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>Text labels</Label>
              <p className="text-xs text-muted-foreground">
                The layer containing province name labels.
              </p>
              <Select value={text} onValueChange={setText}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>None</SelectItem>
                  {flatLayers.map((layer) => (
                    <SelectItem key={layer.path} value={layer.path}>
                      {layer.path.split("/").join(" › ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>Named coasts</Label>
              <p className="text-xs text-muted-foreground">
                The layer with coast-specific paths (e.g. stp/nc, stp/sc).
                Leave as None if your variant has no named coasts.
              </p>
              <Select value={namedCoasts} onValueChange={setNamedCoasts}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>None</SelectItem>
                  {flatLayers.map((layer) => (
                    <SelectItem key={layer.path} value={layer.path}>
                      {layer.path.split("/").join(" › ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!provinces || layers.length === 0}
          >
            Continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
