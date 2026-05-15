import { useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SvgLayerTree } from "@/components/dsvg/SvgLayerTree";
import { flattenTree } from "@/utils/svgTree";
import type { SvgTreeNode } from "@/utils/svgTree";

export interface LayerAssignments {
  provinces: string | null;
  namedCoasts: string | null;
  provinceNames: string | null;
  borders: string | null;
}

const LAYER_FIELDS: {
  key: keyof LayerAssignments;
  label: string;
  description: string;
}[] = [
  {
    key: "provinces",
    label: "Provinces",
    description:
      "Province shapes. Each path should have an ID matching the province abbreviation (e.g. fra, ger).",
  },
  {
    key: "namedCoasts",
    label: "Named Coasts",
    description:
      "Shapes for named coastal sub-regions (e.g. stp/nc, spa/sc). Optional.",
  },
  {
    key: "provinceNames",
    label: "Province Names",
    description: "Text labels for province names. Optional.",
  },
  {
    key: "borders",
    label: "Borders",
    description: "Border lines between provinces. Optional.",
  },
];

const NONE_VALUE = "__none__";

interface LayerAssignmentProps {
  tree: SvgTreeNode[];
  assignments: LayerAssignments;
  onChange: (assignments: LayerAssignments) => void;
}

export function LayerAssignment({
  tree,
  assignments,
  onChange,
}: LayerAssignmentProps) {
  const flatNodes = useMemo(() => flattenTree(tree), [tree]);

  const handleChange = (field: keyof LayerAssignments, value: string) => {
    onChange({ ...assignments, [field]: value === NONE_VALUE ? null : value });
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
        <p className="mb-3 font-medium text-foreground">How layers work</p>
        <p className="mb-2">
          The output SVG uses six fixed layers in order:
        </p>
        <ol className="mb-3 list-inside list-decimal space-y-1">
          <li>
            <span className="font-medium text-foreground">background</span> —
            All layers below <code>provinces</code> in your SVG, grouped with
            their sub-structure preserved.
          </li>
          <li>
            <span className="font-medium text-foreground">provinces</span> —
            Province shapes.
          </li>
          <li>
            <span className="font-medium text-foreground">named-coasts</span> —
            Shapes for named coastal sub-regions.
          </li>
          <li>
            <span className="font-medium text-foreground">province-names</span>{" "}
            — Text labels for provinces.
          </li>
          <li>
            <span className="font-medium text-foreground">borders</span> —
            Border lines.
          </li>
          <li>
            <span className="font-medium text-foreground">foreground</span> —
            All layers above <code>provinces</code> that are not one of the four
            named layers, grouped with sub-structure preserved.
          </li>
        </ol>
        <p>
          Layers not assigned to a named layer are automatically sorted into{" "}
          <strong>background</strong> or <strong>foreground</strong> based on
          their position relative to the provinces layer.
        </p>
      </div>

      <div className="grid gap-10 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <p className="text-sm font-medium">
            Assign your SVG layers to the four named layers. All fields are optional.
          </p>

          {LAYER_FIELDS.map(({ key, label, description }) => (
            <div key={key} className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">{label}</label>
              <p className="text-xs text-muted-foreground">{description}</p>
              <Select
                value={assignments[key] ?? NONE_VALUE}
                onValueChange={value => handleChange(key, value)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a layer..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE_VALUE}>None</SelectItem>
                  {flatNodes.map(node => (
                    <SelectItem key={node.key} value={node.key}>
                      {node.breadcrumb}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">SVG layers</p>
          <SvgLayerTree nodes={tree} />
        </div>
      </div>
    </div>
  );
}
