import { useState } from "react";
import { ChevronRight, ChevronDown, Layers, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SvgTreeNode } from "@/utils/svgTree";

interface SvgLayerTreeNodeProps {
  node: SvgTreeNode;
  depth: number;
}

function SvgLayerTreeNode({ node, depth }: SvgLayerTreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1.5 rounded px-2 py-1 text-sm hover:bg-muted/50",
          depth === 0 && "font-medium"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <button
          type="button"
          className="flex h-4 w-4 shrink-0 items-center justify-center"
          onClick={() => setExpanded(v => !v)}
          aria-label={expanded ? "Collapse" : "Expand"}
          disabled={!hasChildren}
        >
          {hasChildren ? (
            expanded ? (
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            )
          ) : null}
        </button>

        {node.isLayer ? (
          <Layers className="h-3.5 w-3.5 shrink-0 text-blue-500" />
        ) : (
          <FolderOpen className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        )}

        <span className="min-w-0 truncate">{node.name}</span>

        {node.elementCount > 0 && (
          <span className="ml-auto shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
            {node.elementCount}
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map(child => (
            <SvgLayerTreeNode key={child.key} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

interface SvgLayerTreeProps {
  nodes: SvgTreeNode[];
}

export function SvgLayerTree({ nodes }: SvgLayerTreeProps) {
  if (nodes.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        No groups or layers found in this SVG.
      </p>
    );
  }

  return (
    <div className="rounded-lg border bg-background">
      {nodes.map(node => (
        <SvgLayerTreeNode key={node.key} node={node} depth={0} />
      ))}
    </div>
  );
}
