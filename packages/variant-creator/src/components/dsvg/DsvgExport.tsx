import { useState, useMemo, useEffect } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { buildDsvgOutput, buildVisibilityPreviewSvg } from "@/utils/svgBuild";
import type { SvgTreeNode } from "@/utils/svgTree";
import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";

interface DsvgExportProps {
  svgContent: string;
  assignments: LayerAssignments;
  tree: SvgTreeNode[];
  fileName: string;
}

export function DsvgExport({ svgContent, assignments, tree, fileName }: DsvgExportProps) {
  // Go one level deeper so individual named layers are listed, not their container
  const displayNodes = useMemo(
    () => tree.flatMap(n => (n.children.length > 0 ? n.children : [n])),
    [tree]
  );

  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(
    () =>
      new Set(
        tree
          .flatMap(n => (n.children.length > 0 ? n.children : [n]))
          .map(n => n.key)
      )
  );

  const previewSvg = useMemo(
    () => buildVisibilityPreviewSvg(svgContent, displayNodes, visibleKeys),
    [svgContent, displayNodes, visibleKeys]
  );

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const blob = new Blob([previewSvg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [previewSvg]);

  const aspectRatio = useMemo(() => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgContent, "image/svg+xml");
    const vb = doc.documentElement.getAttribute("viewBox") ?? "";
    const parts = vb.split(/\s+/).map(Number);
    return parts.length >= 4 && parts[2] > 0 && parts[3] > 0
      ? `${parts[2]} / ${parts[3]}`
      : undefined;
  }, [svgContent]);

  const toggleLayer = (key: string) => {
    setVisibleKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleDownload = () => {
    const output = buildDsvgOutput(svgContent, assignments);
    const baseName = fileName.replace(/\.svg$/i, "");
    const blob = new Blob([output], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}.d.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Layers ({displayNodes.length})</p>
          <div className="flex max-h-[70vh] flex-col gap-1.5 overflow-y-auto pr-1">
            {displayNodes.map(node => (
              <div key={node.key} className="flex items-center gap-2">
                <Checkbox
                  id={node.key}
                  checked={visibleKeys.has(node.key)}
                  onCheckedChange={() => toggleLayer(node.key)}
                />
                <Label
                  htmlFor={node.key}
                  className="cursor-pointer font-mono text-xs"
                >
                  {node.name}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <Button onClick={handleDownload}>
          <Download className="h-4 w-4" />
          Download dSVG
        </Button>
      </div>

      <div className="relative w-full" style={{ aspectRatio }}>
        {previewUrl && (
          <img
            src={previewUrl}
            alt="SVG layer preview"
            className="h-full w-full rounded-lg border object-contain"
          />
        )}
      </div>
    </div>
  );
}
