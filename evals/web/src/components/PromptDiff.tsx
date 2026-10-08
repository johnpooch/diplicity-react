import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { hasChanges, promptDiff, type Block } from "@/promptDiff";

interface PromptDiffProps {
  title: string;
  before: string | null;
  after: string;
}

interface ChangedProps {
  block: Extract<Block, { kind: "changed" }>;
}

interface UnchangedProps {
  lines: string[];
}

const CONTEXT_LINES = 2;

const SEGMENT_STYLES = {
  same: "",
  added: "rounded-sm px-0.5 bg-emerald-100 text-emerald-950 dark:bg-emerald-950 dark:text-emerald-100",
  removed: "rounded-sm px-0.5 bg-rose-100 text-rose-950 line-through decoration-rose-400 dark:bg-rose-950 dark:text-rose-100",
};

const Unchanged: React.FC<UnchangedProps> = ({ lines }) => {
  const [open, setOpen] = useState(false);
  const hidden = lines.length - CONTEXT_LINES * 2;
  if (open || hidden <= 1) {
    return <p className="text-muted-foreground">{lines.join("\n")}</p>;
  }
  return (
    <>
      <p className="text-muted-foreground">{lines.slice(0, CONTEXT_LINES).join("\n")}</p>
      <button
        type="button"
        className="my-1 w-full rounded-sm bg-muted py-0.5 text-center text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(true)}
      >
        {hidden} unchanged lines
      </button>
      <p className="text-muted-foreground">{lines.slice(-CONTEXT_LINES).join("\n")}</p>
    </>
  );
};

const Changed: React.FC<ChangedProps> = ({ block }) => (
  <p className="-mx-3 border-l-2 border-foreground/40 bg-muted/60 px-3 py-1">
    {block.segments.map((segment, index) => (
      <span key={index} className={cn(SEGMENT_STYLES[segment.kind])}>
        {segment.text}
      </span>
    ))}
  </p>
);

export const PromptDiff: React.FC<PromptDiffProps> = ({ title, before, after }) => {
  const blocks = useMemo(() => (before === null ? null : promptDiff(before, after)), [before, after]);
  const changed = blocks !== null && hasChanges(blocks);
  const [open, setOpen] = useState(false);

  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-sm font-semibold">{title}</h3>
        {!changed && (
          <span className="flex items-baseline gap-2 text-sm text-muted-foreground">
            {blocks !== null && "No changes"}
            <Button variant="ghost" size="sm" onClick={() => setOpen(!open)}>
              {open ? "Hide" : "Show"}
            </Button>
          </span>
        )}
      </div>
      {changed && (
        <div className="rounded-md border px-3 py-2 font-mono text-xs leading-relaxed whitespace-pre-wrap">
          {blocks.map((block, index) =>
            block.kind === "same" ? (
              <Unchanged key={index} lines={block.lines} />
            ) : (
              <Changed key={index} block={block} />
            )
          )}
        </div>
      )}
      {!changed && open && (
        <pre className="rounded-md border px-3 py-2 font-mono text-xs leading-relaxed whitespace-pre-wrap">
          {after}
        </pre>
      )}
    </section>
  );
};
