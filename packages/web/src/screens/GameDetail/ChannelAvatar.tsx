import React from "react";
import { cn } from "@/lib/utils";
import { ChannelNation } from "./channelUtils";

const SIZE = 40;
const HALF = SIZE / 2;
const THIRD = SIZE / 3;
const SCALE = 1.2;

type XAlign = "left" | "center" | "right";
type YAlign = "top" | "center" | "bottom";

// Each circle is SCALE times the cell size, positioned so its inner edge(s) align
// with the cell's inner boundary. The outer 20% bleeds past the parent boundary
// and is clipped by the parent's overflow-hidden rounded-full.
const FlagCell: React.FC<{
  url: string | null;
  w: number;
  xAlign: XAlign;
  yAlign: YAlign;
}> = ({ url, w, xAlign, yAlign }) => {
  const d = w * SCALE;
  const centerOffset = (w - d) / 2; // negative half-overflow for centering

  const xPos: React.CSSProperties =
    xAlign === "left"   ? { right: 0 } :
    xAlign === "right"  ? { left: 0 } :
    { left: centerOffset };

  const yPos: React.CSSProperties =
    yAlign === "top"    ? { bottom: 0 } :
    yAlign === "bottom" ? { top: 0 } :
    { top: centerOffset };

  return (
    <div style={{ width: w, height: w, flexShrink: 0, position: "relative" }}>
      {url && (
        <img
          src={url}
          alt=""
          style={{
            width: d,
            height: d,
            objectFit: "cover",
            display: "block",
            borderRadius: "50%",
            position: "absolute",
            ...xPos,
            ...yPos,
          }}
        />
      )}
    </div>
  );
};

const Row: React.FC<{ h: number; children: React.ReactNode }> = ({ h, children }) => (
  <div style={{ display: "flex", width: SIZE, height: h }}>
    {children}
  </div>
);

interface ChannelAvatarProps {
  nations: ChannelNation[];
}

const ChannelAvatar: React.FC<ChannelAvatarProps> = ({ nations }) => {
  const items = nations.slice(0, 9);
  const count = items.length;

  if (count === 0) return null;

  const f = items.map(n => n.flagUrl);
  const flag = (i: number): string | null => f[i] ?? null;
  const isSingle = count === 1;

  let content: React.ReactNode;

  if (isSingle) {
    content = f[0] ? (
      <img
        src={f[0]}
        alt=""
        style={{ width: SIZE, height: SIZE, objectFit: "cover", display: "block" }}
      />
    ) : null;
  } else if (count === 2) {
    // 2×1: two cells side-by-side, vertically centred in parent
    content = (
      <div style={{ display: "flex", width: SIZE, height: SIZE, alignItems: "center", justifyContent: "center" }}>
        <FlagCell url={flag(0)} w={HALF} xAlign="left"  yAlign="center" />
        <FlagCell url={flag(1)} w={HALF} xAlign="right" yAlign="center" />
      </div>
    );
  } else if (count <= 4) {
    // 2×2 grid
    content = (
      <>
        <Row h={HALF}>
          <FlagCell url={flag(0)} w={HALF} xAlign="left"  yAlign="top" />
          <FlagCell url={flag(1)} w={HALF} xAlign="right" yAlign="top" />
        </Row>
        <Row h={HALF}>
          <FlagCell url={flag(2)} w={HALF} xAlign="left"  yAlign="bottom" />
          <FlagCell url={flag(3)} w={HALF} xAlign="right" yAlign="bottom" />
        </Row>
      </>
    );
  } else {
    // 3×3 grid.
    // 5 nations: cross pattern (TC, ML, MC, MR, BC) — corners empty.
    // 6–9 nations: fill left-to-right, top-to-bottom.
    const cells: (string | null)[] = count === 5
      ? [null, flag(0), null, flag(1), flag(2), flag(3), null, flag(4), null]
      : [0, 1, 2, 3, 4, 5, 6, 7, 8].map(flag);

    const xs: XAlign[] = ["left", "center", "right", "left", "center", "right", "left", "center", "right"];
    const ys: YAlign[] = ["top", "top", "top", "center", "center", "center", "bottom", "bottom", "bottom"];

    content = (
      <>
        <Row h={THIRD}>
          {[0, 1, 2].map(i => <FlagCell key={i} url={cells[i]} w={THIRD} xAlign={xs[i]} yAlign={ys[i]} />)}
        </Row>
        <Row h={THIRD}>
          {[3, 4, 5].map(i => <FlagCell key={i} url={cells[i]} w={THIRD} xAlign={xs[i]} yAlign={ys[i]} />)}
        </Row>
        <Row h={THIRD}>
          {[6, 7, 8].map(i => <FlagCell key={i} url={cells[i]} w={THIRD} xAlign={xs[i]} yAlign={ys[i]} />)}
        </Row>
      </>
    );
  }

  return (
    <div
      className={cn(
        "rounded-full overflow-hidden flex-shrink-0",
        isSingle ? "bg-muted" : "bg-background dark:bg-black ring-1 ring-black dark:ring-white"
      )}
      style={{
        width: SIZE,
        height: SIZE,
        boxShadow: isSingle ? `0 0 0 1px ${items[0].color}` : undefined,
      }}
    >
      {content}
    </div>
  );
};

export { ChannelAvatar };
