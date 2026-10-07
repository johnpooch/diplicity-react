import { diffLines, diffWords } from "diff";

export type Segment = { kind: "same" | "added" | "removed"; text: string };

export type Block =
  | { kind: "same"; lines: string[] }
  | { kind: "changed"; segments: Segment[] };

const trimNewline = (text: string): string => text.replace(/\n$/, "");

const wordSegments = (before: string, after: string): Segment[] => {
  const segments: Segment[] = [];
  for (const part of diffWords(before, after)) {
    const kind = part.added ? "added" : part.removed ? "removed" : "same";
    const last = segments[segments.length - 1];
    if (last?.kind === kind) {
      last.text += part.value;
    } else {
      segments.push({ kind, text: part.value });
    }
  }
  return segments;
};

export const promptDiff = (before: string, after: string): Block[] => {
  const parts = diffLines(before, after);
  const blocks: Block[] = [];
  for (let index = 0; index < parts.length; index += 1) {
    const part = parts[index];
    const next = parts[index + 1];
    if (!part.added && !part.removed) {
      blocks.push({ kind: "same", lines: trimNewline(part.value).split("\n") });
    } else if (part.removed && next?.added) {
      blocks.push({
        kind: "changed",
        segments: wordSegments(trimNewline(part.value), trimNewline(next.value)),
      });
      index += 1;
    } else {
      blocks.push({
        kind: "changed",
        segments: [{ kind: part.added ? "added" : "removed", text: trimNewline(part.value) }],
      });
    }
  }
  return blocks;
};

export const hasChanges = (blocks: Block[]): boolean => blocks.some(block => block.kind === "changed");
