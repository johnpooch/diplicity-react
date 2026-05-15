import { useState, useMemo, useEffect } from "react";
import { Download, ChevronDown, ChevronRight } from "lucide-react";
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
  const displayNodes = useMemo(
    () => tree.flatMap(n => (n.children.length > 0 ? n.children : [n])),
    [tree]
  );

  // Split displayNodes into background/foreground based on position relative to provinces
  const { backgroundItems, foregroundItems } = useMemo(() => {
    const assignedKeySet = new Set(
      [assignments.provinces, assignments.namedCoasts, assignments.provinceNames, assignments.borders]
        .filter((k): k is string => k !== null)
    );
    const provincesIdx = assignments.provinces
      ? displayNodes.findIndex(n => n.key === assignments.provinces)
      : -1;
    const bg: SvgTreeNode[] = [];
    const fg: SvgTreeNode[] = [];
    displayNodes.forEach((node, i) => {
      if (assignedKeySet.has(node.key)) return;
      if (provincesIdx === -1 || i < provincesIdx) bg.push(node);
      else fg.push(node);
    });
    return { backgroundItems: bg, foregroundItems: fg };
  }, [displayNodes, assignments]);

  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(
    () => new Set(tree.flatMap(n => (n.children.length > 0 ? n.children : [n])).map(n => n.key))
  );

  const toggleLeaf = (key: string) => {
    setVisibleKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleGroup = (keys: string[]) => {
    setVisibleKeys(prev => {
      const allOn = keys.every(k => prev.has(k));
      const next = new Set(prev);
      keys.forEach(k => (allOn ? next.delete(k) : next.add(k)));
      return next;
    });
  };

  const groupCheckedState = (keys: string[]): boolean | "indeterminate" => {
    if (keys.length === 0) return true;
    const on = keys.filter(k => visibleKeys.has(k)).length;
    if (on === keys.length) return true;
    if (on === 0) return false;
    return "indeterminate";
  };

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

  // Assigned layers in canonical output order, skipping unassigned ones
  const assignedLayers = (
    [
      { label: "provinces", key: assignments.provinces },
      { label: "named-coasts", key: assignments.namedCoasts },
      { label: "province-names", key: assignments.provinceNames },
      { label: "borders", key: assignments.borders },
    ] as { label: string; key: string | null }[]
  ).filter((l): l is { label: string; key: string } => l.key !== null);

  const bgKeys = backgroundItems.map(n => n.key);
  const fgKeys = foregroundItems.map(n => n.key);

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <div className="flex flex-col gap-4">
        <div className="flex max-h-[70vh] flex-col overflow-y-auto pr-1">
          <GroupRow
            label="background"
            checked={groupCheckedState(bgKeys)}
            onToggle={() => toggleGroup(bgKeys)}
          >
            {backgroundItems.map(node => (
              <LeafRow
                key={node.key}
                id={node.key}
                name={node.name}
                checked={visibleKeys.has(node.key)}
                onToggle={() => toggleLeaf(node.key)}
              />
            ))}
          </GroupRow>

          {assignedLayers.map(({ label, key }) => (
            <div key={key} className="flex items-center gap-1.5 py-0.5">
              <div className="w-4 shrink-0" />
              <Checkbox
                id={key}
                checked={visibleKeys.has(key)}
                onCheckedChange={() => toggleLeaf(key)}
              />
              <Label htmlFor={key} className="cursor-pointer font-mono text-xs">
                {label}
              </Label>
            </div>
          ))}

          <GroupRow
            label="foreground"
            checked={groupCheckedState(fgKeys)}
            onToggle={() => toggleGroup(fgKeys)}
          >
            {foregroundItems.map(node => (
              <LeafRow
                key={node.key}
                id={node.key}
                name={node.name}
                checked={visibleKeys.has(node.key)}
                onToggle={() => toggleLeaf(node.key)}
              />
            ))}
          </GroupRow>
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

interface GroupRowProps {
  label: string;
  checked: boolean | "indeterminate";
  onToggle: () => void;
  children: React.ReactNode;
}

function GroupRow({ label, checked, onToggle, children }: GroupRowProps) {
  const [open, setOpen] = useState(true);
  const Chevron = open ? ChevronDown : ChevronRight;
  return (
    <div>
      <div className="flex items-center gap-1.5 py-0.5">
        <button
          type="button"
          className="flex w-4 shrink-0 items-center justify-center text-muted-foreground"
          onClick={() => setOpen(o => !o)}
        >
          <Chevron className="h-3 w-3" />
        </button>
        <Checkbox
          id={`group-${label}`}
          checked={checked}
          onCheckedChange={onToggle}
        />
        <Label
          htmlFor={`group-${label}`}
          className="cursor-pointer font-mono text-xs font-medium"
        >
          {label}
        </Label>
      </div>
      {open && <div className="ml-[22px] flex flex-col">{children}</div>}
    </div>
  );
}

interface LeafRowProps {
  id: string;
  name: string;
  checked: boolean;
  onToggle: () => void;
}

function LeafRow({ id, name, checked, onToggle }: LeafRowProps) {
  return (
    <div className="flex items-center gap-1.5 py-0.5">
      <Checkbox id={id} checked={checked} onCheckedChange={onToggle} />
      <Label htmlFor={id} className="cursor-pointer font-mono text-xs">
        {name}
      </Label>
    </div>
  );
}
