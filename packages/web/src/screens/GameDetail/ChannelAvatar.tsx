import React from "react";
import { cn } from "@/lib/utils";
import { ChannelNation } from "./channelUtils";

const SCALE = 1.2;

type XAlign = "left" | "center" | "right";
type YAlign = "top" | "center" | "bottom";

const imgX = (d: number, xa: XAlign, xb: number): number => {
  if (xa === "left") return xb - d;
  if (xa === "right") return xb;
  return xb - d / 2;
};

const imgY = (d: number, ya: YAlign, yb: number): number => {
  if (ya === "top") return yb - d;
  if (ya === "bottom") return yb;
  return yb - d / 2;
};

interface FlagImg { url: string; x: number; y: number; d: number }

const buildImgs = (size: number, count: number, flag: (i: number) => string | null): FlagImg[] => {
  const half = size / 2;
  const third = size / 3;
  const imgs: FlagImg[] = [];
  const add = (fi: number, d: number, xa: XAlign, xb: number, ya: YAlign, yb: number) => {
    const url = flag(fi);
    if (url) imgs.push({ url, x: imgX(d, xa, xb), y: imgY(d, ya, yb), d });
  };

  const d2 = half * SCALE;
  const d3 = third * SCALE;
  const T = third;
  const TT = 2 * third;

  if (count === 2) {
    add(0, d2, "left", half, "center", half);
    add(1, d2, "right", half, "center", half);
  } else if (count <= 4) {
    add(0, d2, "left", half, "top", half);
    add(1, d2, "right", half, "top", half);
    add(2, d2, "left", half, "bottom", half);
    add(3, d2, "right", half, "bottom", half);
  } else if (count === 5) {
    add(0, d3, "center", half, "top", T);
    add(1, d3, "left", T, "center", half);
    add(2, d3, "center", half, "center", half);
    add(3, d3, "right", TT, "center", half);
    add(4, d3, "center", half, "bottom", TT);
  } else {
    add(0, d3, "left", T, "top", T);
    add(1, d3, "center", half, "top", T);
    add(2, d3, "right", TT, "top", T);
    add(3, d3, "left", T, "center", half);
    add(4, d3, "center", half, "center", half);
    add(5, d3, "right", TT, "center", half);
    add(6, d3, "left", T, "bottom", TT);
    add(7, d3, "center", half, "bottom", TT);
    add(8, d3, "right", TT, "bottom", TT);
  }

  return imgs;
};

interface ChannelAvatarProps {
  nations: ChannelNation[];
  size?: number;
}

const ChannelAvatar: React.FC<ChannelAvatarProps> = ({ nations, size = 40 }) => {
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
        width: size,
        height: size,
        boxShadow: isSingle ? `0 0 0 1px ${items[0].color}` : undefined,
      }}
    >
      <div
        className={isSingle ? "bg-muted" : "bg-background dark:bg-black"}
        style={{
          width: size,
          height: size,
          position: "relative",
          clipPath: "circle(50% at 50% 50%)",
        }}
      >
        {isSingle ? (
          singleUrl && (
            <img
              src={singleUrl}
              alt=""
              style={{ width: size, height: size, objectFit: "cover", display: "block" }}
            />
          )
        ) : (
          buildImgs(size, count, flag).map((img, i) => (
            <img
              key={`grid-${i}`}
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
