import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { TimelinePoint } from "@/games";
import { cn } from "@/lib/utils";

interface CentreTimelineProps {
  points: TimelinePoint[];
  nation: string;
  currentYear: number;
  onSelect: (year: number | null) => void;
}

interface LineKeyProps {
  color: string;
}

const ACCENT = "#2a78d6";
const CONTEXT = "#c3c2b7";
const GRID = "#e1e0d9";
const SURFACE = "#ffffff";
const WIDTH = 440;
const HEIGHT = 150;
const LEFT = 24;
const RIGHT = 84;
const TOP = 10;
const BOTTOM = 24;

const LineKey: React.FC<LineKeyProps> = ({ color }) => (
  <span className="inline-block h-0.5 w-3 shrink-0 rounded-full" style={{ backgroundColor: color }} />
);

const ticksFor = (top: number): number[] => {
  const step = top <= 9 ? 3 : 6;
  return Array.from({ length: top / step + 1 }, (_, index) => index * step);
};

export const CentreTimeline: React.FC<CentreTimelineProps> = ({ points, nation, currentYear, onSelect }) => {
  const [active, setActive] = useState<number | null>(null);
  const [table, setTable] = useState(false);
  const nations = Object.keys(points[0]?.centres ?? {}).sort();
  const highest = Math.max(...points.flatMap(point => Object.values(point.centres)));
  const top = Math.max(6, Math.ceil(highest / 3) * 3);
  const band = (WIDTH - LEFT - RIGHT) / Math.max(points.length - 1, 1);
  const x = (index: number) => LEFT + index * band;
  const y = (value: number) => TOP + (1 - value / top) * (HEIGHT - TOP - BOTTOM);
  const path = (name: string) =>
    points.map((point, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(point.centres[name])}`).join(" ");
  const others = nations.filter(name => name !== nation);
  const last = points[points.length - 1];
  const shown = active === null ? null : points[active];

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold">Supply centres</h2>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <LineKey color={ACCENT} />
            {nation}
          </span>
          <span className="flex items-center gap-1.5">
            <LineKey color={CONTEXT} />
            Other nations
          </span>
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={() => setTable(!table)}>
            {table ? "Chart" : "Table"}
          </Button>
        </div>
      </div>
      {table ? (
        <table className="text-xs tabular-nums">
          <thead>
            <tr className="text-muted-foreground">
              <th scope="col" className="py-1 pr-3 text-left font-normal">Nation</th>
              {points.map(point => (
                <th key={point.label} scope="col" className="px-2 py-1 text-right font-normal">
                  <button type="button" className="hover:underline" onClick={() => onSelect(point.year)}>
                    {point.label}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {nations.map(name => (
              <tr key={name} className={cn("border-t", name === nation && "font-semibold")}>
                <td className="py-1 pr-3">{name}</td>
                {points.map(point => (
                  <td key={point.label} className="px-2 py-1 text-right">
                    {point.centres[name]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="relative w-fit">
          <svg width={WIDTH} height={HEIGHT} role="img" aria-label={`Supply centres by year for every nation`}>
            {ticksFor(top).map(tick => (
              <g key={tick}>
                <line x1={LEFT} x2={WIDTH - RIGHT} y1={y(tick)} y2={y(tick)} stroke={GRID} strokeWidth={1} />
                <text x={LEFT - 6} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted-foreground text-[10px]">
                  {tick}
                </text>
              </g>
            ))}
            {points.map((point, index) => (
              <text
                key={point.label}
                x={x(index)}
                y={HEIGHT - 6}
                textAnchor="middle"
                className={cn(
                  "text-[10px]",
                  point.year === currentYear ? "fill-foreground font-semibold" : "fill-muted-foreground"
                )}
              >
                {point.label}
              </text>
            ))}
            {active !== null && (
              <line x1={x(active)} x2={x(active)} y1={TOP} y2={HEIGHT - BOTTOM} stroke={CONTEXT} strokeWidth={1} />
            )}
            {others.map(name => (
              <path key={name} d={path(name)} fill="none" stroke={CONTEXT} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
            ))}
            <path d={path(nation)} fill="none" stroke={ACCENT} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
            <circle
              cx={x(points.length - 1)}
              cy={y(last.centres[nation])}
              r={4}
              fill={ACCENT}
              stroke={SURFACE}
              strokeWidth={2}
            />
            <text x={x(points.length - 1) + 10} y={y(last.centres[nation])} dy="0.32em" className="fill-foreground text-[11px]">
              {nation} {last.centres[nation]}
            </text>
            {points.map((point, index) => (
              <rect
                key={point.label}
                x={x(index) - band / 2}
                y={0}
                width={band}
                height={HEIGHT}
                fill="transparent"
                tabIndex={0}
                role="button"
                aria-label={`${point.label}: ${nation} ${point.centres[nation]} centres. Go to ${point.year ?? "the last phase"}`}
                className="cursor-pointer outline-none"
                onPointerEnter={() => setActive(index)}
                onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
                onClick={() => onSelect(point.year)}
                onKeyDown={event => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect(point.year);
                  }
                }}
              />
            ))}
          </svg>
          {shown && active !== null && (
            <div
              className="pointer-events-none absolute top-0 z-10 flex w-36 flex-col gap-0.5 rounded-md border bg-popover px-2.5 py-2 text-xs shadow-md"
              style={{ left: x(active) + (active > points.length / 2 ? -152 : 12) }}
            >
              <p className="mb-1 text-muted-foreground">{shown.year === null ? "End of game" : `Start of ${shown.label}`}</p>
              {[...nations]
                .sort((a, b) => shown.centres[b] - shown.centres[a] || a.localeCompare(b))
                .map(name => (
                  <p key={name} className="flex items-center gap-2">
                    <LineKey color={name === nation ? ACCENT : CONTEXT} />
                    <span className="w-4 text-right font-semibold tabular-nums">{shown.centres[name]}</span>
                    <span className="text-muted-foreground">{name}</span>
                  </p>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
