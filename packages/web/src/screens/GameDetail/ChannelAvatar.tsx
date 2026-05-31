import React from "react";
import { cn } from "@/lib/utils";
import { ChannelNation } from "./channelUtils";

const SIZE = 40;
const HALF = SIZE / 2;
const THIRD = SIZE / 3;
const SCALE = 1.2;

type XAlign = "left" | "center" | "right";
type YAlign = "top" | "center" | "bottom";

const imgX = (d: number, xa: XAlign, xb: number): number =>
  xa === "left"   ? xb - d :
  xa === "right"  ? xb     :
  xb - d / 2;

const imgY = (d: number, ya: YAlign, yb: number): number =>
  ya === "top"    ? yb - d :
  ya === "bottom" ? yb     :
  yb - d / 2;

interface FlagImg { url: string; x: number; y: number; d: number }

const buildImgs = (count: number, flag: (i: number) => string | null): FlagImg[] => {
  const imgs: FlagImg[] = [];
  const add = (fi: number, d: number, xa: XAlign, xb: number, ya: YAlign, yb: number) => {
    const url = flag(fi);
    if (url) imgs.push({ url, x: imgX(d, xa, xb), y: imgY(d, ya, yb), d });
  };

  const d2 = HALF * SCALE;
  const d3 = THIRD * SCALE;
  const T = THIRD;
  const TT = 2 * THIRD;

  if (count === 2) {
    add(0, d2, "left",  HALF, "center", HALF);
    add(1, d2, "right", HALF, "center", HALF);
  } else if (count <= 4) {
    add(0, d2, "left",  HALF, "top",    HALF);
    add(1, d2, "right", HALF, "top",    HALF);
    add(2, d2, "left",  HALF, "bottom", HALF);
    add(3, d2, "right", HALF, "bottom", HALF);
  } else if (count === 5) {
    add(0, d3, "center", HALF,  "top",    T);
    add(1, d3, "left",   T,     "center", HALF);
    add(2, d3, "center", HALF,  "center", HALF);
    add(3, d3, "right",  TT,    "center", HALF);
    add(4, d3, "center", HALF,  "bottom", TT);
  } else {
    add(0, d3, "left",   T,    "top",    T);
    add(1, d3, "center", HALF, "top",    T);
    add(2, d3, "right",  TT,   "top",    T);
    add(3, d3, "left",   T,    "center", HALF);
    add(4, d3, "center", HALF, "center", HALF);
    add(5, d3, "right",  TT,   "center", HALF);
    add(6, d3, "left",   T,    "bottom", TT);
    add(7, d3, "center", HALF, "bottom", TT);
    add(8, d3, "right",  TT,   "bottom", TT);
  }

  return imgs;
};

interface ChannelAvatarProps {
  nations: ChannelNation[];
}

const ChannelAvatar: React.FC<ChannelAvatarProps> = ({ nations }) => {
  const items = nations.slice(0, 9);
  const count = items.length;

  if (count === 0) return null;

  const flag = (i: number): string | null => items[i]?.flagUrl ?? null;
  const isSingle = count === 1;
  const singleUrl = isSingle ? flag(0) : null;

  return (
    <div
      className={cn(
        "rounded-full flex-shrink-0",
        !isSingle && "ring-1 ring-black dark:ring-white"
      )}
      style={{
        width: SIZE,
        height: SIZE,
        boxShadow: isSingle ? `0 0 0 1px ${items[0].color}` : undefined,
      }}
    >
      <div
        className={isSingle ? "bg-muted" : "bg-background dark:bg-black"}
        style={{
          width: SIZE,
          height: SIZE,
          position: "relative",
          clipPath: "circle(50% at 50% 50%)",
        }}
      >
        {isSingle ? (
          singleUrl && (
            <img
              src={singleUrl}
              alt=""
              style={{ width: SIZE, height: SIZE, objectFit: "cover", display: "block" }}
            />
          )
        ) : (
          buildImgs(count, flag).map((img, i) => (
            <img
              key={i}
              src={img.url}
              alt=""
              style={{
                position: "absolute",
                left: img.x,
                top: img.y,
                width: img.d,
                height: img.d,
                objectFit: "cover",
                display: "block",
                borderRadius: "50%",
              }}
            />
          ))
        )}
      </div>
    </div>
  );
};

export { ChannelAvatar };
