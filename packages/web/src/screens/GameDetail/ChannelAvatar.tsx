import React from "react";
import { cn } from "@/lib/utils";
import { ChannelNation } from "./channelUtils";

const SIZE = 40;
const HALF = SIZE / 2;
const THIRD = SIZE / 3;

const FlagCell: React.FC<{ url: string | null; w: number; h: number }> = ({
  url,
  w,
  h,
}) => (
  <div style={{ width: w, height: h, flexShrink: 0 }}>
    {url && (
      <img
        src={url}
        alt=""
        style={{ width: w, height: h, objectFit: "cover", display: "block" }}
      />
    )}
  </div>
);

const FlagRow: React.FC<{
  flags: (string | null)[];
  w: number;
  h: number;
}> = ({ flags, w, h }) => (
  <div
    style={{
      display: "flex",
      width: SIZE,
      height: h,
      justifyContent: "center",
    }}
  >
    {flags.map((url, i) => (
      <FlagCell key={i} url={url} w={w} h={h} />
    ))}
  </div>
);

interface ChannelAvatarProps {
  nations: ChannelNation[];
}

const ChannelAvatar: React.FC<ChannelAvatarProps> = ({ nations }) => {
  const items = nations.slice(0, 9);
  const count = items.length;

  if (count === 0) return null;

  const flags = items.map(n => n.flagUrl);
  const isSingle = count === 1;

  let content: React.ReactNode;

  if (isSingle) {
    content = <FlagCell url={flags[0]} w={SIZE} h={SIZE} />;
  } else if (count === 2) {
    content = (
      <div style={{ display: "flex", width: SIZE, height: SIZE, alignItems: "center", justifyContent: "center" }}>
        {flags.slice(0, 2).map((url, i) => (
          <div key={i} style={{ width: HALF, height: HALF, borderRadius: "50%", overflow: "hidden", flexShrink: 0 }}>
            {url && <img src={url} alt="" style={{ width: HALF, height: HALF, objectFit: "cover", display: "block" }} />}
          </div>
        ))}
      </div>
    );
  } else if (count <= 4) {
    content = (
      <>
        <FlagRow flags={flags.slice(0, 2)} w={HALF} h={HALF} />
        <FlagRow flags={flags.slice(2, 4)} w={HALF} h={HALF} />
      </>
    );
  } else if (count === 5) {
    content = (
      <>
        <FlagRow flags={[flags[0]]} w={THIRD} h={THIRD} />
        <FlagRow flags={flags.slice(1, 4)} w={THIRD} h={THIRD} />
        <FlagRow flags={[flags[4]]} w={THIRD} h={THIRD} />
      </>
    );
  } else {
    content = (
      <>
        <FlagRow flags={flags.slice(0, 3)} w={THIRD} h={THIRD} />
        <FlagRow flags={flags.slice(3, 6)} w={THIRD} h={THIRD} />
        <FlagRow flags={flags.slice(6, 9)} w={THIRD} h={THIRD} />
      </>
    );
  }

  return (
    <div
      className={cn(
        "rounded-full overflow-hidden flex-shrink-0",
        isSingle ? "bg-muted" : "bg-background"
      )}
      style={{
        width: SIZE,
        height: SIZE,
        boxShadow: isSingle
          ? `0 0 0 1px ${items[0].color}`
          : "0 0 0 1px hsl(var(--foreground))",
      }}
    >
      {content}
    </div>
  );
};

export { ChannelAvatar };
